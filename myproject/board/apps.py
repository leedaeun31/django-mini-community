from django.apps import AppConfig


from django.apps import AppConfig

class BoardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "board"

    def ready(self):
        from . import signals  # noqa
