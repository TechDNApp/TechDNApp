from django.test import TestCase
from django.urls import reverse

class CoreViewsTests(TestCase):
       def test_home_page_status_200(self):
           response = self.client.get(reverse("core:home"))
           self.assertEqual(response.status_code, 200)

       def test_home_page_template(self):
           response = self.client.get(reverse("core:home"))
           self.assertTemplateUsed(response, "core/home.html")


# Create your tests here.
