import os
from django.core.wsgi import get_wsgi_application
from infrastructure.monitoring.otel_setup import setup_otel

setup_otel()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()

