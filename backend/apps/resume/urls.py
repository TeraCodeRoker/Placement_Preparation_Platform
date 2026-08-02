from django.urls import path

from apps.resume import views

urlpatterns = [
    path("analyze", views.analyze),
    path("ats-score", views.ats_score),
    path("improve-bullet", views.improve_bullet),
    path("placement-check", views.placement_check),
    path("pdf-to-json", views.pdf_to_json),
    path("analyze-pdf", views.analyze_pdf),
    path("history", views.history),
]
