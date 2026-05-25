"""Utility functions for chatbot functionality."""

import logging
from typing import Any, Dict, List, Optional

from django.conf import settings

from saleor.chatbot.models import ChatMessage, ChatSession, ChatbotConfig

logger = logging.getLogger(__name__)


def get_ai_client():
    """Get AI service client (OpenAI)."""
    try:
        import openai
    except ImportError:
        logger.error("OpenAI library not installed")
        raise ImportError("Please install 'openai' library: pip install openai")

    openai.api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not openai.api_key:
        logger.error("OPENAI_API_KEY not configured in settings")
        raise ValueError("OPENAI_API_KEY must be configured in settings")

    return openai


def build_conversation_context(session: ChatSession) -> List[Dict[str, str]]:
    """Build conversation context from chat session messages."""
    messages = session.messages.all().order_by("created_at")
    context = []

    for message in messages:
        context.append(
            {
                "role": message.role,
                "content": message.content,
            }
        )

    return context


def get_chatbot_response(
    session: ChatSession,
    user_message: str,
    config: Optional[ChatbotConfig] = None,
) -> tuple[str, Dict[str, Any]]:
    """
    Get response from AI service for a user message.

    Args:
        session: The chat session
        user_message: The user's message
        config: Chatbot configuration (will fetch if not provided)

    Returns:
        Tuple of (response_text, metadata)
    """
    if config is None:
        config = ChatbotConfig.objects.filter(channel=session.channel).first()
        if not config or not config.is_enabled:
            raise ValueError("Chatbot is not enabled for this channel")

    try:
        openai = get_ai_client()

        # Build conversation history
        messages = build_conversation_context(session)

        # Add system prompt
        system_messages = [
            {
                "role": "system",
                "content": config.system_prompt,
            }
        ]

        # Add user message
        all_messages = system_messages + messages + [
            {
                "role": "user",
                "content": user_message,
            }
        ]

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=config.model_name,
            messages=all_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )

        # Extract response
        assistant_message = response.choices[0].message.content
        metadata = {
            "model": config.model_name,
            "tokens_used": response.usage.total_tokens,
            "finish_reason": response.choices[0].finish_reason,
        }

        return assistant_message, metadata

    except Exception as e:
        logger.exception(f"Error getting AI response: {str(e)}")
        raise


def create_chat_message(
    session: ChatSession,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> ChatMessage:
    """Create a new chat message."""
    return ChatMessage.objects.create(
        session=session,
        role=role,
        content=content,
        metadata=metadata or {},
    )


def validate_session_active(session: ChatSession) -> bool:
    """Check if session is still active."""
    if not session.is_active:
        return False

    # Check if session has timed out
    config = ChatbotConfig.objects.filter(channel=session.channel).first()
    if config:
        from django.utils import timezone
        from datetime import timedelta

        timeout_delta = timedelta(hours=config.session_timeout_hours)
        if timezone.now() - session.updated_at > timeout_delta:
            session.close_session()
            return False

    return True


def count_messages_in_session(session: ChatSession) -> int:
    """Count total messages in a session."""
    return session.messages.count()


def validate_message_limit(session: ChatSession) -> bool:
    """Check if session has reached message limit."""
    config = ChatbotConfig.objects.filter(channel=session.channel).first()
    if config:
        return count_messages_in_session(session) < config.max_messages_per_session
    return True
