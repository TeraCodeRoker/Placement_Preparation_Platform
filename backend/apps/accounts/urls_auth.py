from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("register", views.register),
    path("login", views.login),
    path("refresh", views.refresh),
    path("logout", views.logout),
    path("guest", views.guest),
    path("claim", views.claim),
]
