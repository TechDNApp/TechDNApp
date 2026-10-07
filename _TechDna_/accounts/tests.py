from django.contrib.auth import get_user_model
from django.test import TestCase

# Create your tests here.

User = get_user_model()

class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="developer_candidate",
            email="candidate@example.com",
            password="StrongPassword123!",
        )
        self.assertEqual(user.username, "developer_candidate")
        self.assertTrue(user.check_password("StrongPassword123!"))