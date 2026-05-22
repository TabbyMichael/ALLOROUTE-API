import pytest
from django.conf import settings


@pytest.mark.django_db
def test_settings_load():
    """Verify that settings are loaded correctly."""
    assert settings.SECRET_KEY is not None
    assert "apps.api" in settings.INSTALLED_APPS
