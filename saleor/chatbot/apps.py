from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    """Configuration for the chatbot app."""

    name = "saleor.chatbot"
    label = "chatbot"
    verbose_name = "Chatbot"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Import signals when the app is ready."""
        from . import signals  # noqa: F401
