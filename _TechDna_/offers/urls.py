from django.urls import path

from . import views

app_name = "offers"

urlpatterns = [
    path("", views.OfferListView.as_view(), name="list"),
    path("new/", views.OfferCreateView.as_view(), name="create"),
    path("<int:pk>/", views.OfferDetailView.as_view(), name="detail"),
    path("<int:pk>/accept/", views.accept_offer_view, name="accept"),
    path("<int:pk>/reject/", views.reject_offer_view, name="reject"),
    path("<int:pk>/cancel/", views.cancel_offer_view, name="cancel"),
    path("<int:pk>/counter/", views.counter_offer_view, name="counter"),
]
