from django.urls import path

from . import views

app_name = "assessments"

# IMPORTANTE: el detalle <int:pk>/<slug:slug>/ va el ÚLTIMO.
# Si estuviera antes, "/assessments/5/edit/" o "/assessments/5/favorite/" 
# encajaría con él (slug="edit" o "favorite") y se mostraría el detalle en lugar de la vista correspondiente.
urlpatterns = [
    path(
        "",
        views.AssessmentListView.as_view(),
        name="list",
    ),
    path(
        "create/",
        views.AssessmentCreateView.as_view(),
        name="create",
    ),
    path(
        "mine/",
        views.MyAssessmentListView.as_view(),
        name="mine",
    ),
    path(
        "technology/<slug:slug>/",
        views.AssessmentByTechnologyListView.as_view(),
        name="by_technology",
    ),
    path(
        "user/<str:username>/",
        views.OwnerAssessmentListView.as_view(),
        name="by_owner",
    ),
    path(
        "<int:pk>/edit/",
        views.AssessmentUpdateView.as_view(),
        name="update",
    ),
    path(
        "<int:pk>/delete/",
        views.AssessmentDeleteView.as_view(),
        name="delete",
    ),
    path(
        "<int:pk>/favorite/",
        views.toggle_favorite,
        name="toggle_favorite",
    ),
    path(
        "<int:pk>/<slug:slug>/",
        views.AssessmentDetailView.as_view(),
        name="detail",
    ),
]