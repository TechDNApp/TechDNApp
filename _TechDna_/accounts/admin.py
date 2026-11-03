from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.gis.db.models import PointField
from django.contrib.gis.forms.widgets import OSMWidget
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    search_fields = ("username", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Perfil técnico", {"fields": ("role", "primary_track", "city")}),
        ("Ubicación (Sesión 12)", {"fields": ("location_name", "location")}),
    )
    # Sesión 12: el widget por defecto usa imágenes de satélite que se ven en
    # negro; con OpenStreetMap y centrado en Barcelona es más fácil situar el punto.
    formfield_overrides = {
        PointField: {
            "widget": OSMWidget(
                attrs={"default_lat": 41.3870, "default_lon": 2.1700, "default_zoom": 11}
            )
        },
    }
