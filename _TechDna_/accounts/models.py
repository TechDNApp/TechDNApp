from django.contrib.auth.models import AbstractUser
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

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"