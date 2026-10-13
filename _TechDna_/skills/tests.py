from django.test import TestCase
from .models import Category, Technology



class CategoryModelTest(TestCase):

    def test_create_category(self):

        category = Category.objects.create(
            name="Programación"
        )

        self.assertEqual(
            category.name,
            "Programación"
        )

class CategoryModelTest(TestCase):

    def test_slug_generation(self):

        category = Category.objects.create(
            name="Cloud Computing"
        )

        self.assertEqual(
            category.slug,
            "cloud-computing"
        )

class TechnologyModelTest(TestCase):

    def test_create_technology(self):

        category = Category.objects.create(
            name="Programación"
        )

        technology = Technology.objects.create(
            name="Python",
            category=category
        )

        self.assertEqual(
            technology.name,
            "Python"
        )

        self.assertEqual(
            technology.category,
            category
        )

