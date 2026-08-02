from django.urls import path

from apps.notes import views

urlpatterns = [
    path("", views.admin_collection),
    path("/<uuid:note_id>", views.admin_update),
]
