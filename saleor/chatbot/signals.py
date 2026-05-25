"""Signals for chatbot app."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from saleor.channel.models import Channel
from saleor.chatbot.models import ChatbotConfig


@receiver(post_save, sender=Channel)
def create_chatbot_config_for_channel(sender, instance, created, **kwargs):
    """Create default chatbot config when a new channel is created."""
    if created:
        ChatbotConfig.objects.get_or_create(
            channel=instance,
            defaults={
                "is_enabled": True,
            },
        )
