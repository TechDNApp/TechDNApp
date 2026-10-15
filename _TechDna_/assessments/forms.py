from django import forms

from .models import Assessment


class AssessmentForm(forms.ModelForm):
    """
    Formulario de creación/edición de evaluaciones.

    No incluye:
      - owner  -> lo asigna el servidor (request.user) en la vista.
      - active -> lo controla la aplicación (al crear, siempre activa).
      - slug   -> se genera automáticamente en Assessment.save().
    """

    MIN_TITLE_LENGTH = 5

    class Meta:
        model = Assessment

        fields = [
            "title",
            "description",
            "technology",
            "role",
            "mode",
        ]

        labels = {
            "title": "Título",
            "description": "Descripción",
            "technology": "Tecnología",
            "role": "Rol profesional",
            "mode": "Modo",
        }

        help_texts = {
            "title": "Ejemplo: Python Backend Junior",
        }

        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()

        if len(title) < self.MIN_TITLE_LENGTH:
            raise forms.ValidationError(
                f"El título debe tener al menos {self.MIN_TITLE_LENGTH} caracteres."
            )

        return title
