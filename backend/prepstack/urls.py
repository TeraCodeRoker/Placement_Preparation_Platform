"""Root URLconf. Feature routes mount under /api/v1; health at root for Render."""
from django.urls import include, path

from apps.core.views import health, health_detailed

API = "api/v1/"

urlpatterns = [
    path("health", health),
    path("health/detailed", health_detailed),
    path(f"{API}auth/", include("apps.accounts.urls_auth")),
    path(f"{API}users/", include("apps.accounts.urls_users")),
    path(f"{API}ai/interview/", include("apps.interview.urls")),
    path(f"{API}ai/mcq/", include("apps.mcq.urls")),
    path(f"{API}ai/resume/", include("apps.resume.urls")),
    path(f"{API}ai/oa/", include("apps.oa.urls")),
    path(f"{API}notes", include("apps.notes.urls_public")),
    path(f"{API}admin/notes", include("apps.notes.urls_admin")),
]
