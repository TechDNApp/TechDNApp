from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView

from . import services
from .forms import CounterOfferForm, JobOfferForm
from .models import JobOffer


def _user_offers(user):
    """Ofertas en las que participa el usuario: la base de toda consulta."""
    return (
        JobOffer.objects
        .filter(Q(evaluator=user) | Q(candidate=user))
        .select_related("assessment", "evaluator", "candidate", "created_by")
    )


def _first_error(error):
    return error.messages[0] if isinstance(error, ValidationError) else str(error)


class OfferListView(LoginRequiredMixin, ListView):
    """
    Bandeja de ofertas con tres pestañas:
      - received: propuestas pendientes que esperan MI respuesta.
      - sent:     propuestas pendientes que he hecho yo.
      - history:  todo lo ya cerrado.
    """

    template_name = "offers/list.html"
    context_object_name = "offers"
    paginate_by = 12
    TABS = {
        "received": "Pendientes de mi respuesta",
        "sent": "Enviadas por mí",
        "history": "Historial",
    }

    def get_tab(self):
        tab = self.request.GET.get("tab", "received")
        return tab if tab in self.TABS else "received"

    def get_queryset(self):
        user = self.request.user
        queryset = _user_offers(user)
        tab = self.get_tab()
        if tab == "received":
            return queryset.filter(status=JobOffer.Status.PENDING).exclude(created_by=user)
        if tab == "sent":
            return queryset.filter(status=JobOffer.Status.PENDING, created_by=user)
        return queryset.exclude(status=JobOffer.Status.PENDING)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tab"] = self.get_tab()
        context["tabs"] = self.TABS
        context["querystring"] = f"tab={self.get_tab()}"
        return context


class OfferDetailView(LoginRequiredMixin, DetailView):
    template_name = "offers/detail.html"
    context_object_name = "offer"

    def get_queryset(self):
        # Quien no participa recibe 404: ni siquiera sabe que la oferta existe.
        return _user_offers(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offer = self.object
        user = self.request.user
        context["history"] = services.get_negotiation_history(offer)
        context["latest"] = (
            offer.counter_offers.order_by("-created_at").first()
        )
        context["can_respond"] = offer.can_respond(user)
        context["can_cancel"] = offer.can_cancel(user)
        context["other_party"] = offer.other_party(user)
        if context["can_respond"]:
            context["counter_form"] = kwargs.get("counter_form") or CounterOfferForm(
                initial={"salary": offer.salary, "modality": offer.modality},
            )
        return context


class OfferCreateView(LoginRequiredMixin, FormView):
    template_name = "offers/create.html"
    form_class = JobOfferForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["evaluator"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # /offers/new/?assessment=5 preselecciona la evaluación.
        if self.request.GET.get("assessment"):
            initial["assessment"] = self.request.GET["assessment"]
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            offer = services.create_offer(
                evaluator=self.request.user,
                assessment_id=data["assessment"].pk,
                candidate_id=data["candidate"].pk,
                position_title=data["position_title"],
                salary=data["salary"],
                modality=data["modality"],
                message=data.get("message", ""),
                expires_at=data.get("expires_at"),
            )
        except (PermissionDenied, ValidationError) as error:
            form.add_error(None, _first_error(error))
            return self.form_invalid(form)

        messages.success(self.request, "Oferta enviada correctamente.")
        return redirect(offer)


# ----------------------------------------------------------------------
# Acciones (siempre POST): la lógica vive en services.py
# ----------------------------------------------------------------------

def _run_action(request, pk, service, success_message):
    offer = get_object_or_404(_user_offers(request.user), pk=pk)
    try:
        result = service(request.user, offer.pk)
    except PermissionDenied as error:
        return HttpResponseForbidden(str(error))
    except ValidationError as error:
        messages.error(request, _first_error(error))
        return redirect(offer)
    messages.success(request, success_message)
    return redirect(result)


@login_required
@require_POST
def accept_offer_view(request, pk):
    return _run_action(request, pk, services.accept_offer, "Has aceptado la oferta.")


@login_required
@require_POST
def reject_offer_view(request, pk):
    return _run_action(request, pk, services.reject_offer, "Has rechazado la oferta.")


@login_required
@require_POST
def cancel_offer_view(request, pk):
    return _run_action(request, pk, services.cancel_offer, "Has cancelado la oferta.")


@login_required
@require_POST
def counter_offer_view(request, pk):
    offer = get_object_or_404(_user_offers(request.user), pk=pk)
    form = CounterOfferForm(request.POST)
    if not form.is_valid():
        view = OfferDetailView()
        view.setup(request, pk=pk)
        view.object = offer
        return render(
            request,
            "offers/detail.html",
            view.get_context_data(object=offer, counter_form=form),
            status=400,
        )
    try:
        new_offer = services.counter_offer(
            request.user,
            offer.pk,
            salary=form.cleaned_data["salary"],
            modality=form.cleaned_data["modality"],
            message=form.cleaned_data["message"],
        )
    except PermissionDenied as error:
        return HttpResponseForbidden(str(error))
    except ValidationError as error:
        messages.error(request, _first_error(error))
        return redirect(offer)
    messages.success(request, "Contraoferta enviada.")
    return redirect(new_offer)
