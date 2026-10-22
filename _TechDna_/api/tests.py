from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User
from assessments.models import Assessment
from skills.models import Category, Technology, Role

class AssessmentAPITests(APITestCase):
    def setUp(self):
        # Crear usuarios de prueba
        self.user1 = User.objects.create_user(email="user1@example.com", password="password123", username="user1")
        self.user2 = User.objects.create_user(email="user2@example.com", password="password123", username="user2")
        
        # Crear dependencias obligatorias (Category antes que Technology)
        self.category = Category.objects.create(name="Framework")
        self.role = Role.objects.create(name="Backend Developer")
        self.technology = Technology.objects.create(name="Django", category=self.category)

        # Crear una evaluación inicial propiedad de user1
        self.assessment = Assessment.objects.create(
            title="Python Backend Junior",
            description="Test description for assessment",
            mode=Assessment.TRAINING,
            role=self.role,
            technology=self.technology,
            owner=self.user1
        )

        self.list_url = reverse("assessment-list")
        self.detail_url = reverse("assessment-detail", kwargs={"pk": self.assessment.pk})

    def test_get_assessment_list_public(self):
        """Cualquier usuario (incluso anónimo) puede listar las evaluaciones"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_assessment_authenticated(self):
        """Un usuario autenticado puede crear una evaluación"""
        self.client.force_authenticate(user=self.user1)
        data = {
            "title": "Advanced DRF API",
            "description": "Deep dive into Django REST Framework",
            "mode": "training",
            "role": self.role.id,
            "technology": self.technology.id
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Assessment.objects.count(), 2)

    def test_create_assessment_unauthenticated(self):
        """Un usuario sin autenticar no puede crear evaluaciones"""
        data = {
            "title": "Unauthorized Assessment",
            "description": "Should fail",
            "mode": "training",
            "role": self.role.id,
            "technology": self.technology.id
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_assessment_by_owner(self):
        """El propietario puede actualizar su propia evaluación"""
        self.client.force_authenticate(user=self.user1)
        data = {"title": "Updated Python Backend Junior"}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.title, "Updated Python Backend Junior")

    def test_update_assessment_by_non_owner(self):
        """Un usuario que no es propietario recibe un error Forbidden (403) al intentar modificar"""
        self.client.force_authenticate(user=self.user2)
        data = {"title": "Malicious Update"}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_and_search_assessments(self):
        """Verificar el funcionamiento de los filtros y parámetros de búsqueda"""
        response = self.client.get(self.list_url, {"search": "Python"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Python Backend Junior")