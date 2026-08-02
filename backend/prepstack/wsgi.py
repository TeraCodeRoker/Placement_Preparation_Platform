"""WSGI entrypoint (Gunicorn serves this on Render)."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prepstack.settings")
application = get_wsgi_application()
