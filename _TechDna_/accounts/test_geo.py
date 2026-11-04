from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.forms import ProfileForm
from accounts.models import User
from accounts.services import get_candidates_nearby

# Plaça de Catalunya (Barcelona): punto desde el que buscamos.
BCN_LAT, BCN_LNG = 41.3870, 2.1700


def create_geo_users():
    """Dos candidatos (L'Hospitalet ~7 km y Madrid ~500 km) y un evaluador."""
    near = User.objects.create_user(
        username="cand_near",
        email="near@test.com",
        password="pwd",
        role="candidate",
        location=Point(2.0997, 41.3598, srid=4326),
        location_name="L'Hospitalet",
    )
    far = User.objects.create_user(
        username="cand_far",
        email="far@test.com",
        password="pwd",
        role="candidate",
        location=Point(-3.7038, 40.4168, srid=4326),
        location_name="Madrid",
    )
    evaluator = User.objects.create_user(
        username="evaluator_near",
        email="eval@test.com",
        password="pwd",
        role="evaluator",
        location=Point(2.1734, 41.3851, srid=4326),
    )
    return near, far, evaluator


class CandidateSpatialQueryTests(TestCase):
    def setUp(self):
        self.near, self.far, self.evaluator = create_geo_users()

    def test_filter_nearby_candidates_within_10km(self):
        results = list(get_candidates_nearby(BCN_LAT, BCN_LNG, radius_km=10))

        self.assertIn(self.near, results)
        self.assertNotIn(self.far, results)
        self.assertTrue(results[0].distance.km < 10)

    def test_evaluators_are_not_returned(self):
        results = list(get_candidates_nearby(BCN_LAT, BCN_LNG, radius_km=10))
        self.assertNotIn(self.evaluator, results)

    def test_results_ordered_by_distance(self):
        results = list(get_candidates_nearby(BCN_LAT, BCN_LNG, radius_km=600))

        self.assertEqual(results, [self.near, self.far])
        self.assertAlmostEqual(results[1].distance.km, 505, delta=15)

    def test_users_without_location_are_ignored(self):
        User.objects.create_user(username="no_loc", email="no@test.com", password="pwd")
        results = list(get_candidates_nearby(BCN_LAT, BCN_LNG, radius_km=600))
        self.assertEqual(len(results), 2)


class CandidateNearbyAPITests(APITestCase):
    def setUp(self):
        self.near, self.far, self.evaluator = create_geo_users()
        self.url = reverse("candidate-list")

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nearby_filter_returns_distance(self):
        self.client.force_authenticate(user=self.evaluator)
        response = self.client.get(
            self.url, {"lat": BCN_LAT, "lng": BCN_LNG, "distance_km": 10}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual([r["username"] for r in results], ["cand_near"])
        self.assertLess(results[0]["distance_km"], 10)
        # Coordenadas redondeadas a 2 decimales por privacidad.
        self.assertEqual(results[0]["latitude"], 41.36)
        self.assertEqual(results[0]["longitude"], 2.1)

    def test_without_coordinates_lists_all_candidates(self):
        self.client.force_authenticate(user=self.evaluator)
        response = self.client.get(self.url)

        usernames = {r["username"] for r in response.data["results"]}
        self.assertEqual(usernames, {"cand_near", "cand_far"})
        self.assertIsNone(response.data["results"][0]["distance_km"])

    def test_invalid_params_return_400(self):
        self.client.force_authenticate(user=self.evaluator)
        for params in (
            {"lat": "abc", "lng": BCN_LNG},
            {"lat": 120, "lng": BCN_LNG},
            {"lat": BCN_LAT, "lng": BCN_LNG, "distance_km": 0},
            {"lat": BCN_LAT, "lng": BCN_LNG, "distance_km": 9999},
        ):
            response = self.client.get(self.url, params)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, params)


class ProfileFormLocationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="maite", email="maite@test.com", password="pwd"
        )

    def form_data(self, **extra):
        data = {"email": "maite@test.com", "primary_track": "backend"}
        data.update(extra)
        return data

    def test_saves_lat_lng_as_point(self):
        form = ProfileForm(
            data=self.form_data(latitude="41.3598", longitude="2.0997"),
            instance=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.user.refresh_from_db()
        self.assertAlmostEqual(self.user.location.y, 41.3598)
        self.assertAlmostEqual(self.user.location.x, 2.0997)

    def test_only_one_coordinate_is_invalid(self):
        form = ProfileForm(data=self.form_data(latitude="41.3598"), instance=self.user)
        self.assertFalse(form.is_valid())

    def test_empty_coordinates_clear_location(self):
        self.user.location = Point(2.0997, 41.3598, srid=4326)
        self.user.save()

        form = ProfileForm(data=self.form_data(), instance=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.user.refresh_from_db()
        self.assertIsNone(self.user.location)
