from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model

from assessments.models import Assessment

from .models import JobOffer
from .services import CANDIDATE_ROLE

User = get_user_model()


class JobOfferForm(forms.ModelForm):
    """
    Formulario para enviar una oferta. El evaluador, el autor y el estado los
    decide el servidor; aquí sólo se eligen evaluación, candidato y condiciones.
    """

    class Meta:
        model = JobOffer
        fields = [
            "assessment",
            "candidate",
            "position_title",
            "salary",
            "modality",
            "message",
            "expires_at",
        ]
        labels = {
            "assessment": "Evaluación",
            "candidate": "Candidato",
            "position_title": "Puesto",
            "salary": "Salario bruto anual (€)",
            "modality": "Modalidad",
            "message": "Mensaje",
            "expires_at": "Caduca el (opcional)",
        }
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
            "expires_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, evaluator, **kwargs):
        super().__init__(*args, **kwargs)
        # Sólo evaluaciones propias y activas; sólo candidatos activos que no seas tú.
        self.fields["assessment"].queryset = Assessment.objects.filter(
            owner=evaluator, active=True,
        )
        self.fields["candidate"].queryset = (
            User.objects.filter(role=CANDIDATE_ROLE, is_active=True)
            .exclude(pk=evaluator.pk)
            .order_by("username")
        )
        self.fields["candidate"].label_from_instance = lambda user: user.username


class CounterOfferForm(forms.Form):
    salary = forms.DecimalField(
        label="Nuevo salario (€)",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    modality = forms.ChoiceField(label="Modalidad", choices=JobOffer.Modality.choices)
    message = forms.CharField(
        label="Mensaje",
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
