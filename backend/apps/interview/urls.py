from django.urls import path

from apps.interview import views

urlpatterns = [
    path("start", views.start),
    path("answer", views.answer),
    path("session/<uuid:session_id>", views.session_state),
    path("history", views.history),
    path("code-review", views.code_review),
]
