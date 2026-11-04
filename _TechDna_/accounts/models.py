from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis_models
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("candidate", "Candidato"),
        ("evaluator", "Evaluador"),
    ]

    TRACK_CHOICES = [
        ("frontend", "Frontend Development"),
        ("backend", "Backend Development"),
        ("devops", "Cloud & DevOps"),
        ("data", "Data & AI"),
        ("fullstack", "Full Stack"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="candidate",
        verbose_name="Rol",
    )
    primary_track = models.CharField(
        max_length=30,
        choices=TRACK_CHOICES,
        default="backend",
        verbose_name="Track Principal",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        verbose_name="Avatar",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Ciudad",
    )
    bio = models.TextField(
        blank=True,
        verbose_name="Biografía / Presentación técnica",
    )
    github_url = models.URLField(
        blank=True,
        verbose_name="Perfil de GitHub",
    )
    linkedin_url = models.URLField(
        blank=True,
        verbose_name="Perfil de LinkedIn",
    )

    # Sesión 12: geolocalización (PostGIS). Point(longitud, latitud) en WGS84.
    # geography=True para que las distancias se calculen en metros reales
    # sobre la esfera terrestre y no en grados.
    location = gis_models.PointField(
        srid=4326,
        geography=True,
        null=True,
        blank=True,
        verbose_name="Ubicación",
    )
    location_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Zona",
        help_text="Nombre legible de la zona o ciudad (ej. Hospitalet de Llobregat)",
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"