from django.urls import path

from apps.mcq import views

urlpatterns = [
    path("generate", views.generate),
    path("daily-challenge", views.daily_challenge),
    path("attempt", views.attempt),
    path("history", views.history),
]
