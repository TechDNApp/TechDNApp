from django.db import models
from django.utils.text import slugify


# ej: Programación, Bases de Datos, Cloud, Ciberseguridad, DevOps, Inteligencia Artificial
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True, #temporary fix for migration issues
        blank=True
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=True, #temporary fix for migration issues
        blank=True
    )
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# ej: Python, Java, SQL, Docker, AWS, Linuxq
class Technology(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="technologies"
    )

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# ej: Backend Developer, Data Analyst, DevOps Engineer, Cybersecurity Analyst
class Role(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ej: Python, JavaScript, React, Node.js, PostgreSQL, MongoDB
class Skill(models.Model):
    technology = models.ForeignKey(
        Technology,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name