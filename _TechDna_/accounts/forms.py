from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.gis.geos import Point
from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "primary_track",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo electrónico.")
        return email.lower()


class ProfileForm(forms.ModelForm):
    # Sesión 12: el usuario introduce latitud/longitud y las guardamos en el
    # PointField ``location`` (que recibe primero la longitud).
    latitude = forms.FloatField(
        required=False,
        min_value=-90,
        max_value=90,
        label="Latitud",
        help_text="Ej. 41.3598 (puedes copiarla de Google Maps).",
    )
    longitude = forms.FloatField(
        required=False,
        min_value=-180,
        max_value=180,
        label="Longitud",
        help_text="Ej. 2.0997",
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "primary_track",
            "avatar",
            "city",
            "location_name",
            "bio",
            "github_url",
            "linkedin_url",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.location:
            self.fields["latitude"].initial = self.instance.location.y
            self.fields["longitude"].initial = self.instance.location.x

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")
        if (latitude is None) != (longitude is None):
            raise forms.ValidationError(
                "Indica latitud y longitud a la vez, o deja ambas vacías."
            )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        latitude = self.cleaned_data.get("latitude")
        longitude = self.cleaned_data.get("longitude")
        if latitude is None:
            user.location = None
        else:
            user.location = Point(longitude, latitude, srid=4326)
        if commit:
            user.save()
            self._save_m2m()
        return user

    def clean_email(self):
        email = self.cleaned_data.get("email")
        queryset = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso.")
        return email.lower()
