from django.db import models
from django.conf import settings


# ejemplos: Python Backend Junior, SQL Fundamentals, Linux Essentials
class Assessment(models.Model):

    TRAINING = "training"
    CERTIFICATION = "certification"

    MODE_CHOICES = [
        (TRAINING, "Entrenamiento"),
        (CERTIFICATION, "Certificación"),
    ]

    title = models.CharField(max_length=200)

    description = models.TextField()

    mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES
    )

    role = models.ForeignKey(
        "skills.Role",
        on_delete=models.CASCADE
    )

    technology = models.ForeignKey(
        "skills.Technology",
        on_delete=models.CASCADE
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    statement = models.TextField()

    explanation = models.TextField(
        blank=True
    )

    difficulty = models.PositiveSmallIntegerField(
        default=1
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.statement[:50]


class Answer(models.Model):

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers"
    )

    text = models.CharField(max_length=500)

    is_correct = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.text


class Attempt(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    finished = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.user} - {self.assessment}"


class Result(models.Model):

    attempt = models.OneToOneField(
        Attempt,
        on_delete=models.CASCADE
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    passed = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.score}%"
