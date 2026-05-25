"""Celery tasks for chatbot operations."""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from saleor.chatbot.models import ChatSession

logger = logging.getLogger(__name__)


@shared_task
def close_expired_chat_sessions():
    """Close chat sessions that have timed out."""
    from saleor.chatbot.models import ChatbotConfig

    try:
        configs = ChatbotConfig.objects.filter(is_enabled=True)

        for config in configs:
            timeout_delta = timedelta(hours=config.session_timeout_hours)
            expired_time = timezone.now() - timeout_delta

            expired_sessions = ChatSession.objects.filter(
                channel=config.channel,
                is_active=True,
                updated_at__lt=expired_time,
            )

            count = expired_sessions.count()
            expired_sessions.update(
                is_active=False,
                closed_at=timezone.now(),
            )

            logger.info(f"Closed {count} expired chat sessions for {config.channel.name}")

    except Exception as e:
        logger.exception(f"Error closing expired chat sessions: {str(e)}")


@shared_task
def cleanup_old_chat_sessions(days=90):
    """Delete old chat sessions (data retention policy)."""
    try:
        cutoff_date = timezone.now() - timedelta(days=days)

        deleted_sessions = ChatSession.objects.filter(
            is_active=False,
            closed_at__lt=cutoff_date,
        )

        count = deleted_sessions.count()
        deleted_sessions.delete()

        logger.info(f"Deleted {count} old chat sessions (older than {days} days)")

    except Exception as e:
        logger.exception(f"Error cleaning up old chat sessions: {str(e)}")
