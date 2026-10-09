from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountsAuthTests(TestCase):
    def setUp(self):
        self.register_url = reverse("accounts:register")
        self.login_url = reverse("accounts:login")
        self.logout_url = reverse("accounts:logout")
        self.home_url = reverse("core:home")

        self.user_data = {
            "username": "candidate_test",
            "email": "test@techdna.io",
            "password": "StrongPassword123!",
            "first_name": "Dev",
            "last_name": "Test",
            "role": "candidate",
            "primary_track": "backend",
        }

    def test_register_success_creates_user_and_logs_in(self):
        """Verifica que el registro crea el usuario y lo autentica en la sesión."""
        data = {
            "username": "new_dev",
            "email": "newdev@techdna.io",
            "first_name": "New",
            "last_name": "Developer",
            "role": "candidate",
            "primary_track": "backend",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        response = self.client.post(self.register_url, data)

        # Debe redirigir a core:home tras registrarse
        self.assertRedirects(response, self.home_url)

        # El usuario debe existir en la base de datos
        user = User.objects.get(username="new_dev")
        self.assertEqual(user.email, "newdev@techdna.io")
        self.assertEqual(user.role, "candidate")
        self.assertEqual(user.primary_track, "backend")

        # Debe estar autenticado en la sesión
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_register_duplicate_email_fails(self):
        """Verifica que el formulario rechaza correos duplicados."""
        User.objects.create_user(
            username="existing_user",
            email="duplicate@techdna.io",
            password="StrongPassword123!",
        )

        data = {
            "username": "another_user",
            "email": "DUPLICATE@techdna.io",  # En mayúsculas para comprobar case-insensitive
            "first_name": "Another",
            "last_name": "User",
            "role": "candidate",
            "primary_track": "frontend",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        response = self.client.post(self.register_url, data)

        # Debe recargar la misma página con errores (código 200, sin redirect)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="another_user").exists())
        self.assertFormError(
            response,
            "form",
            "email",
            "Ya existe una cuenta con este correo electrónico.",
        )

    def test_login_success(self):
        """Verifica que un usuario registrado puede iniciar sesión."""
        User.objects.create_user(**self.user_data)

        response = self.client.post(
            self.login_url,
            {
                "username": self.user_data["username"],
                "password": self.user_data["password"],
            },
        )
        self.assertRedirects(response, self.home_url)
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_logout_post(self):
        """Verifica que cerrar sesión mediante POST invalida la sesión."""
        user = User.objects.create_user(**self.user_data)
        self.client.force_login(user)

        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.home_url)
        self.assertFalse("_auth_user_id" in self.client.session)