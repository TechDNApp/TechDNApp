import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from skills.models import Role, Technology

from .forms import AssessmentForm
from .models import Assessment, Favorite

logger = logging.getLogger(__name__)

User = get_user_model()


# ----------------------------------------------------------------------
# Mixins reutilizables
# ----------------------------------------------------------------------

class OwnerRequiredMixin(UserPassesTestMixin):
    """
    Autorización a nivel de objeto: sólo el propietario de la evaluación
    puede acceder. Cualquier otro usuario autenticado recibe 403.

    Ocultar el botón en el HTML no basta: alguien podría escribir
    /assessments/10/edit/ a mano. Por eso la comprobación vive aquí.
    """

    raise_exception = True

    def test_func(self):
        assessment = self.get_object()
        return assessment.owner == self.request.user


# ----------------------------------------------------------------------
# READ
# ----------------------------------------------------------------------

class AssessmentListView(ListView):
    """Listado público: sólo evaluaciones activas con búsqueda y filtros."""

    model = Assessment
    template_name = "assessments/list.html"
    context_object_name = "assessments"
    paginate_by = 12

    def get_queryset(self):
        # Optimización con select_related y prefetch_related para evitar N+1
        queryset = (
            Assessment.objects
            .filter(active=True)
            .select_related(
                "owner",
                "technology",
                "role",
            )
            .prefetch_related(
                "images",
            )
        )

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(technology__name__icontains=query)
                | Q(role__name__icontains=query)
            )

        technology_id = self.request.GET.get("technology")
        if technology_id:
            queryset = queryset.filter(technology_id=technology_id)

        role_id = self.request.GET.get("role")
        if role_id:
            queryset = queryset.filter(role_id=role_id)

        mode = self.request.GET.get("mode")
        if mode:
            queryset = queryset.filter(mode=mode)

        ordering = self.request.GET.get("ordering", "newest")
        ordering_map = {
            "newest": "-created_at",
            "oldest": "created_at",
            "popular": "-views_count",
            "title_asc": "title",
        }

        queryset = queryset.order_by(ordering_map.get(ordering, "-created_at"))

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["technologies"] = Technology.objects.all()
        context["roles"] = Role.objects.all()
        if hasattr(Assessment, "ModeChoices"):
            context["modes"] = Assessment.ModeChoices.choices

        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["querystring"] = query_params.urlencode()
        return context


class AssessmentDetailView(DetailView):
    model = Assessment
    template_name = "assessments/detail.html"
    context_object_name = "assessment"

    def get_queryset(self):
        return (
            Assessment.objects
            .select_related(
                "owner",
                "technology",
                "role",
            )
            .prefetch_related(
                "questions",
                "images",
            )
        )

    def get_object(self, queryset=None):
        assessment = super().get_object(queryset)
        # Incremento atómico del contador de visitas mediante expresión F()
        Assessment.objects.filter(pk=assessment.pk).update(views_count=F("views_count") + 1)
        assessment.refresh_from_db(fields=["views_count"])
        return assessment

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # El pk identifica; el slug es decorativo. Si el slug no coincide
        # (p. ej. URL antigua o mal escrita) redirigimos a la URL canónica.
        if self.kwargs["slug"] != self.object.slug:
            return redirect(self.object, permanent=True)

        context = self.get_context_data(object=self.object)

        # Comprobar si el usuario autenticado tiene guardada la evaluación como favorita
        is_favorite = False
        if request.user.is_authenticated:
            is_favorite = Favorite.objects.filter(
                user=request.user, assessment=self.object
            ).exists()
        context["is_favorite"] = is_favorite

        return self.render_to_response(context)


class MyAssessmentListView(LoginRequiredMixin, ListView):
    """Listado privado: todas las evaluaciones del usuario (activas o no)."""

    model = Assessment
    template_name = "assessments/my_assessments.html"
    context_object_name = "assessments"
    paginate_by = 12

    def get_queryset(self):
        return (
            Assessment.objects
            .filter(owner=self.request.user)
            .select_related(
                "technology",
                "role",
            )
            .prefetch_related(
                "images",
            )
        )


class AssessmentByTechnologyListView(AssessmentListView):
    """Ejercicio 1: /assessments/technology/<slug>/"""

    def get_queryset(self):
        self.technology = get_object_or_404(
            Technology,
            slug=self.kwargs["slug"],
        )
        return super().get_queryset().filter(
            technology__slug=self.kwargs["slug"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Evaluaciones de {self.technology.name}"
        return context


class OwnerAssessmentListView(AssessmentListView):
    """Ejercicio 2: página pública de un autor -> /assessments/user/<username>/"""

    def get_queryset(self):
        self.author = get_object_or_404(
            User,
            username=self.kwargs["username"],
        )
        # Hereda filter(active=True): nunca muestra las inactivas.
        return super().get_queryset().filter(owner=self.author)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Evaluaciones de {self.author.username}"
        return context


# ----------------------------------------------------------------------
# FAVORITES (TOGGLE)
# ----------------------------------------------------------------------

@login_required
@require_POST
def toggle_favorite(request, pk):
    """
    Permite a los usuarios autenticados marcar o desmarcar una evaluación como favorita.
    Impide que el propietario guarde su propia prueba.
    """
    assessment = get_object_or_404(Assessment, pk=pk)

    # El propietario no puede marcar su propia evaluación como favorita
    if assessment.owner == request.user:
        messages.error(request, "No puedes añadir a favoritos tu propia evaluación.")
        return redirect(assessment)

    favorite, created = Favorite.objects.get_or_create(
        user=request.user, assessment=assessment
    )

    if not created:
        favorite.delete()
        messages.info(request, "Evaluación eliminada de tus favoritos.")
    else:
        messages.success(request, "Evaluación añadida a tus favoritos.")

    return redirect(assessment)


# ----------------------------------------------------------------------
# CREATE / UPDATE / DELETE
# ----------------------------------------------------------------------

class AssessmentCreateView(LoginRequiredMixin, CreateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = "assessments/create.html"
    # Sin get_success_url: CreateView usa Assessment.get_absolute_url().

    def form_valid(self, form):
        # Seguridad: el propietario y el estado los decide el servidor,
        # nunca el formulario.
        form.instance.owner = self.request.user
        form.instance.active = True

        response = super().form_valid(form)

        # Procesar imágenes adjuntas y marcar la primera como principal (is_primary=True)
        images = self.request.FILES.getlist("images")
        for index, image_file in enumerate(images):
            self.object.images.create(
                image=image_file,
                is_primary=(index == 0),
                position=index,
            )

        logger.info(
            "Assessment created: id=%s owner=%s",
            self.object.pk,
            self.request.user.pk,
        )
        messages.success(
            self.request,
            "Evaluación publicada correctamente.",
        )

        return response


class AssessmentUpdateView(
    LoginRequiredMixin,
    OwnerRequiredMixin,
    UpdateView,
):
    model = Assessment
    form_class = AssessmentForm
    template_name = "assessments/create.html"
    # Sin get_success_url: UpdateView usa Assessment.get_absolute_url().

    def form_valid(self, form):
        response = super().form_valid(form)

        # Guardar imágenes adicionales asignando posiciones consecutivas
        images = self.request.FILES.getlist("images")
        if images:
            has_primary = self.object.images.filter(is_primary=True).exists()
            start_pos = self.object.images.count()
            for index, image_file in enumerate(images):
                self.object.images.create(
                    image=image_file,
                    is_primary=(not has_primary and index == 0),
                    position=start_pos + index,
                )

        logger.info(
            "Assessment updated: id=%s owner=%s",
            self.object.pk,
            self.request.user.pk,
        )
        messages.success(
            self.request,
            "Evaluación actualizada correctamente.",
        )

        return response


class AssessmentDeleteView(
    LoginRequiredMixin,
    OwnerRequiredMixin,
    DeleteView,
):
    model = Assessment
    template_name = "assessments/confirm_delete.html"
    context_object_name = "assessment"
    success_url = reverse_lazy("assessments:mine")

    def form_valid(self, form):
        # Guardamos los ids antes de borrar: después self.object ya no existe en BD.
        assessment_id = self.object.pk
        owner_id = self.request.user.pk

        response = super().form_valid(form)

        logger.info(
            "Assessment deleted: id=%s owner=%s",
            assessment_id,
            owner_id,
        )
        messages.success(
            self.request,
            "Evaluación eliminada correctamente.",
        )

        return response