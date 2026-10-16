from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from skills.models import Category, Role, Technology

from .forms import AssessmentForm
from .models import Assessment, Favorite

User = get_user_model()


class AssessmentViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="laura",
            email="laura@example.com",
            password="TestPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="carlos",
            email="carlos@example.com",
            password="TestPassword123!",
        )

        self.category = Category.objects.create(name="Programación")
        self.technology = Technology.objects.create(
            category=self.category,
            name="Python",
        )
        self.other_technology = Technology.objects.create(
            category=self.category,
            name="SQL",
        )
        self.role = Role.objects.create(name="Backend Developer")

        self.assessment = Assessment.objects.create(
            owner=self.user,
            title="Python Backend Junior",
            description="Fundamentos de Python para backend",
            technology=self.technology,
            role=self.role,
            mode=Assessment.TRAINING,
            active=True,
        )

    def _make_assessment(self, **kwargs):
        data = {
            "owner": self.user,
            "title": "Evaluación extra",
            "description": "Descripción",
            "technology": self.technology,
            "role": self.role,
            "active": True,
        }
        data.update(kwargs)
        return Assessment.objects.create(**data)

    # ---------- Listado ----------

    def test_list_is_public(self):
        response = self.client.get(reverse("assessments:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Backend Junior")

    def test_list_only_shows_active_assessments(self):
        self._make_assessment(title="Evaluación oculta", active=False)

        response = self.client.get(reverse("assessments:list"))

        self.assertContains(response, "Python Backend Junior")
        self.assertNotContains(response, "Evaluación oculta")

    def test_list_is_paginated(self):
        for i in range(13):
            self._make_assessment(title=f"Evaluación {i}")

        response = self.client.get(reverse("assessments:list"))

        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["assessments"]), 12)

    # ---------- Detalle ----------

    def test_detail_returns_200(self):
        response = self.client.get(self.assessment.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Backend Junior")

    def test_detail_url_uses_pk_and_slug(self):
        self.assertEqual(
            self.assessment.get_absolute_url(),
            f"/assessments/{self.assessment.pk}/python-backend-junior/",
        )

    def test_detail_with_wrong_slug_redirects_to_canonical_url(self):
        response = self.client.get(
            f"/assessments/{self.assessment.pk}/otro-slug/"
        )

        self.assertRedirects(
            response,
            self.assessment.get_absolute_url(),
            status_code=301,
        )

    def test_title_without_letters_gets_fallback_slug(self):
        assessment = self._make_assessment(title="!!!!!")

        self.assertEqual(assessment.slug, "evaluacion")
        self.assertEqual(
            self.client.get(assessment.get_absolute_url()).status_code,
            200,
        )

    def test_duplicated_titles_are_allowed(self):
        duplicate = self._make_assessment(title="Python Backend Junior")

        self.assertEqual(duplicate.slug, self.assessment.slug)
        response = self.client.get(duplicate.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    # ---------- Creación ----------

    def test_create_requires_login(self):
        response = self.client.get(reverse("assessments:create"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_logged_user_can_create_assessment(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("assessments:create"),
            {
                "title": "SQL Fundamentals",
                "description": "Consultas básicas",
                "technology": self.technology.pk,
                "role": self.role.pk,
                "mode": Assessment.CERTIFICATION,
            },
        )

        assessment = Assessment.objects.get(title="SQL Fundamentals")
        self.assertEqual(assessment.owner, self.user)
        self.assertTrue(assessment.active)
        self.assertEqual(assessment.slug, "sql-fundamentals")
        self.assertRedirects(response, assessment.get_absolute_url())

    def test_create_ignores_owner_sent_in_post(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("assessments:create"),
            {
                "title": "Linux Essentials",
                "description": "Shell",
                "technology": self.technology.pk,
                "role": self.role.pk,
                "mode": Assessment.TRAINING,
                "owner": self.other_user.pk,
            },
        )

        assessment = Assessment.objects.get(title="Linux Essentials")
        self.assertEqual(assessment.owner, self.user)

    # ---------- Edición ----------

    def test_other_user_cannot_edit_assessment(self):
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse("assessments:update", kwargs={"pk": self.assessment.pk})
        )

        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_edit_assessment_with_post(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("assessments:update", kwargs={"pk": self.assessment.pk}),
            {
                "title": "Hackeado",
                "description": "x",
                "technology": self.technology.pk,
                "role": self.role.pk,
                "mode": Assessment.TRAINING,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.title, "Python Backend Junior")

    def test_owner_can_edit_assessment(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("assessments:update", kwargs={"pk": self.assessment.pk})
        )

        self.assertEqual(response.status_code, 200)

    def test_owner_edit_keeps_slug(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("assessments:update", kwargs={"pk": self.assessment.pk}),
            {
                "title": "Python Backend Junior 2026",
                "description": "Actualizada",
                "technology": self.technology.pk,
                "role": self.role.pk,
                "mode": Assessment.TRAINING,
            },
        )

        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.title, "Python Backend Junior 2026")
        self.assertEqual(self.assessment.slug, "python-backend-junior")

    # ---------- Eliminación ----------

    def test_other_user_cannot_delete_assessment(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("assessments:delete", kwargs={"pk": self.assessment.pk})
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Assessment.objects.filter(pk=self.assessment.pk).exists()
        )

    def test_delete_get_only_shows_confirmation(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("assessments:delete", kwargs={"pk": self.assessment.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Assessment.objects.filter(pk=self.assessment.pk).exists()
        )

    def test_owner_can_delete_assessment(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("assessments:delete", kwargs={"pk": self.assessment.pk})
        )

        self.assertFalse(
            Assessment.objects.filter(pk=self.assessment.pk).exists()
        )

    # ---------- Mis evaluaciones ----------

    def test_my_assessments_requires_login(self):
        response = self.client.get(reverse("assessments:mine"))

        self.assertEqual(response.status_code, 302)

    def test_my_assessments_only_shows_own_including_inactive(self):
        self._make_assessment(title="Mi borrador", active=False)
        self._make_assessment(title="De Carlos", owner=self.other_user)
        self.client.force_login(self.user)

        response = self.client.get(reverse("assessments:mine"))

        self.assertContains(response, "Python Backend Junior")
        self.assertContains(response, "Mi borrador")
        self.assertNotContains(response, "De Carlos")

    # ---------- Ejercicios prácticos ----------

    def test_filter_by_technology(self):
        self._make_assessment(title="SQL Avanzado", technology=self.other_technology)

        response = self.client.get(
            reverse("assessments:by_technology", kwargs={"slug": "sql"})
        )

        self.assertContains(response, "SQL Avanzado")
        self.assertNotContains(response, "Python Backend Junior")

    def test_filter_by_unknown_technology_returns_404(self):
        response = self.client.get(
            reverse("assessments:by_technology", kwargs={"slug": "cobol"})
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_public_page_only_shows_active(self):
        self._make_assessment(title="Borrador de Laura", active=False)

        response = self.client.get(
            reverse("assessments:by_owner", kwargs={"username": "laura"})
        )

        self.assertContains(response, "Python Backend Junior")
        self.assertNotContains(response, "Borrador de Laura")


class AssessmentFormTests(TestCase):

    def setUp(self):
        category = Category.objects.create(name="Programación")
        self.technology = Technology.objects.create(category=category, name="Python")
        self.role = Role.objects.create(name="Backend Developer")

    def _data(self, **kwargs):
        data = {
            "title": "Python Backend Junior",
            "description": "Descripción",
            "technology": self.technology.pk,
            "role": self.role.pk,
            "mode": Assessment.TRAINING,
        }
        data.update(kwargs)
        return data

    def test_form_does_not_expose_owner_or_active(self):
        form = AssessmentForm()

        self.assertNotIn("owner", form.fields)
        self.assertNotIn("active", form.fields)
        self.assertNotIn("slug", form.fields)

    def test_short_title_is_rejected(self):
        form = AssessmentForm(data=self._data(title="  Py  "))

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_valid_form(self):
        form = AssessmentForm(data=self._data())

        self.assertTrue(form.is_valid())

class FavoriteListViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="laura",
            password="TestPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="carlos",
            password="TestPassword123!",
        )
        category = Category.objects.create(name="Programación")
        technology = Technology.objects.create(category=category, name="Python")
        role = Role.objects.create(name="Backend Developer")

        self.assessment = Assessment.objects.create(
            owner=self.other_user,
            title="Python Backend Junior",
            description="Fundamentos",
            technology=technology,
            role=role,
        )
        self.url = reverse("assessments:favorites")

    def test_favorites_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_favorites_shows_saved_assessments(self):
        Favorite.objects.create(user=self.user, assessment=self.assessment)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Backend Junior")

    def test_favorites_only_shows_own_favorites(self):
        # Laura guarda la evaluación; Carlos no debe verla en SUS favoritos.
        Favorite.objects.create(user=self.user, assessment=self.assessment)
        self.client.force_login(self.other_user)

        response = self.client.get(self.url)

        self.assertNotContains(response, "Python Backend Junior")
        self.assertContains(response, "Todavía no has guardado")