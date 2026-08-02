from django.urls import path

from apps.oa import views

urlpatterns = [
    path("problem", views.problem),
    path("run", views.run),
    path("submit", views.submit),
    path("submission/<uuid:submission_id>", views.submission),
]
