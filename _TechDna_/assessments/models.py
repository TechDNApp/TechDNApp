from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


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
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=TRAINING)
    role = models.ForeignKey(
        "skills.Role",
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    technology = models.ForeignKey(
        "skills.Technology",
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # El slug NO es único: puede haber dos "Python Backend Junior".
    # El identificador fiable es el pk; el slug sólo hace la URL legible:
    # /assessments/24/python-backend-junior/
    slug = models.SlugField(
        max_length=220,
        blank=True,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_assessments",
    )

    # Sesión 6: contador de visitas (se incrementa con F() en el detalle).
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Política: el slug se genera una sola vez. Si luego cambia el título,
        # se mantiene el slug antiguo para no romper URLs ya compartidas.
        if not self.slug:
            # "or": un título sólo con símbolos daría slug vacío y rompería la URL.
            self.slug = slugify(self.title) or "evaluacion"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "assessments:detail",
            kwargs={
                "pk": self.pk,
                "slug": self.slug,
            },
        )

    @property
    def primary_image(self):
        """
        Imagen principal de la evaluación (o None).

        Usa self.images.all() en lugar de .filter() para aprovechar el
        prefetch_related("images") de las vistas y evitar el problema N+1.
        """
        images = list(self.images.all())
        for image in images:
            if image.is_primary:
                return image
        return images[0] if images else None

    def __str__(self):
        return self.title


class AssessmentImage(models.Model):
    """Imágenes de una evaluación: portada, diagramas, capturas de código..."""

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="assessments/")
    is_primary = models.BooleanField(default=False)
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"Imagen {self.position} de {self.assessment}"


class Favorite(models.Model):
    """
    Modelo intermedio usuario <-> evaluación (Many-to-Many conceptual).
    Usamos un modelo propio en vez de ManyToManyField para guardar la fecha.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Un usuario sólo puede guardar una vez la misma evaluación.
            models.UniqueConstraint(
                fields=["user", "assessment"],
                name="unique_user_assessment_favorite",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.assessment}"


class Question(models.Model):

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    statement = models.TextField()
    explanation = models.TextField(blank=True)
    difficulty = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["difficulty", "created_at"]

    def __str__(self):
        return self.statement[:50]


class Answer(models.Model):

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text


class Attempt(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    finished = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]

    def save(self, *args, **kwargs):
        if self.finished and self.completed_at is None:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.assessment}"


class Result(models.Model):

    attempt = models.OneToOneField(
        Attempt,
        on_delete=models.CASCADE,
        related_name="result",
    )
    score = models.DecimalField(max_digits=5, decimal_places=2)
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.score}%"