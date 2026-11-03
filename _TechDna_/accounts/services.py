from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from .models import User


def get_candidates_nearby(latitude, longitude, radius_km=15):
    """
    Sesión 12: devuelve los candidatos con ubicación dentro de un radio en
    kilómetros, anotando la distancia al punto dado y ordenando del más
    cercano al más lejano.

    Ojo con el orden: Point recibe (x=longitud, y=latitud).
    """
    user_location = Point(float(longitude), float(latitude), srid=4326)

    return (
        User.objects.filter(
            role="candidate",
            is_active=True,
            location__distance_lte=(user_location, D(km=float(radius_km))),
        )
        .annotate(distance=Distance("location", user_location))
        .order_by("distance")
    )
