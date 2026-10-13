from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    # Import the signals module so its receivers get registered
    def ready(self):
        import api.signals  # noqa: F401 -- registers the token-creation signal
