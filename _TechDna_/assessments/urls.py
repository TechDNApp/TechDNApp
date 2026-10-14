from django.urls import path

from .views import (
    AssessmentListView,
    AssessmentDetailView,
    AssessmentCreateView,
    AssessmentUpdateView,
)

app_name = "assessments"

urlpatterns = [
    path(
        "",
        AssessmentListView.as_view(),
        name="list"
    ),

    path(
        "create/",
        AssessmentCreateView.as_view(),
        name="create"
    ),

    path(
        "<slug:slug>/",
        AssessmentDetailView.as_view(),
        name="detail"
    ),

    path(
        "<slug:slug>/edit/",
        AssessmentUpdateView.as_view(),
        name="update"
    ),
]