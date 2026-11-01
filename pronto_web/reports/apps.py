"""Register the stable reports Django app label used by existing migrations."""

from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pronto_web.reports"
