# Ensure other necessary settings are present by importing base settings
from .base import *

# Use SQLite in-memory for testing to avoid connection issues
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
