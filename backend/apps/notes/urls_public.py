from django.urls import path

from apps.notes import views

urlpatterns = [
    path("", views.list_public),
]
