from django import forms

from .models import Assessment


class MultipleFileInput(forms.ClearableFileInput):
    """Widget <input type="file" multiple>."""

    allow_multiple_selected = True


class MultipleFileField(forms.ImageField):
    """
    Campo que acepta varias imágenes en un mismo input.
    Django no trae un MultipleImageField listo, así que lo construimos:
    cada archivo se valida con la limpieza normal de ImageField.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        # Varios archivos: validamos cada uno y devolvemos la lista.
        if isinstance(data, (list, tuple)):
            return [
                cleaned_file
                for item in data
                if (cleaned_file := single_file_clean(item, initial))
            ]

        # Ningún archivo: lista vacía (el campo es opcional).
        if data in self.empty_values:
            return []

        # Un solo archivo: lo devolvemos dentro de una lista.
        return [single_file_clean(data, initial)]


class AssessmentForm(forms.ModelForm):
    """
    Formulario de creación/edición de evaluaciones.

    No incluye:
      - owner  -> lo asigna el servidor (request.user) en la vista.
      - active -> lo controla la aplicación (al crear, siempre activa).
      - slug   -> se genera automáticamente en Assessment.save().
    """

    MIN_TITLE_LENGTH = 5
    MAX_IMAGES = 8
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

    # No es un campo del modelo: las imágenes se guardan en AssessmentImage
    # desde la vista (Paso 3).
    images = MultipleFileField(
        required=False,
        label="Imágenes",
        help_text="Portada, diagramas o capturas. Máx. 8 imágenes de 5 MB. "
        "La primera será la imagen principal.",
    )

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

    def clean_images(self):
        images = self.cleaned_data.get("images") or []

        if len(images) > self.MAX_IMAGES:
            raise forms.ValidationError(
                f"Puedes subir como máximo {self.MAX_IMAGES} imágenes."
            )

        for image in images:
            if image.size > self.MAX_IMAGE_SIZE:
                raise forms.ValidationError("Cada imagen no puede superar los 5 MB.")

        return images
