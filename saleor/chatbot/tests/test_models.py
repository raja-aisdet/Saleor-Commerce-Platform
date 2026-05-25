"""Tests for chatbot module."""

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

from saleor.channel.models import Channel
from saleor.chatbot.models import ChatMessage, ChatSession, ChatbotConfig
from saleor.chatbot.utils import (
    build_conversation_context,
    count_messages_in_session,
    validate_message_limit,
    validate_session_active,
)

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(email="test@example.com", password="test123")


@pytest.fixture
def channel(db):
    """Create a test channel."""
    return Channel.objects.create(
        name="Test Channel",
        slug="test-channel",
        currency_code="USD",
        default_country="US",
    )


@pytest.fixture
def chatbot_config(db, channel):
    """Create a test chatbot config."""
    return ChatbotConfig.objects.create(
        channel=channel,
        is_enabled=True,
        system_prompt="You are a helpful assistant.",
        model_name="gpt-3.5-turbo",
        max_tokens=100,
        temperature=0.7,
        max_messages_per_session=50,
        session_timeout_hours=24,
    )


@pytest.fixture
def chat_session(db, user, channel):
    """Create a test chat session."""
    return ChatSession.objects.create(
        user=user,
        channel=channel,
        title="Test Session",
        is_active=True,
    )


@pytest.fixture
def chat_messages(db, chat_session):
    """Create test chat messages."""
    messages = [
        ChatMessage.objects.create(
            session=chat_session,
            role="user",
            content="Hello",
        ),
        ChatMessage.objects.create(
            session=chat_session,
            role="assistant",
            content="Hi there! How can I help?",
        ),
        ChatMessage.objects.create(
            session=chat_session,
            role="user",
            content="Tell me about your products",
        ),
    ]
    return messages


class TestChatSession(TestCase):
    """Tests for ChatSession model."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            email="test@example.com", password="test123"
        )
        self.channel = Channel.objects.create(
            name="Test",
            slug="test",
            currency_code="USD",
            default_country="US",
        )

    def test_create_chat_session(self):
        """Test creating a chat session."""
        session = ChatSession.objects.create(
            user=self.user,
            channel=self.channel,
            title="Test",
        )
        assert session.id is not None
        assert session.is_active is True
        assert session.closed_at is None

    def test_close_session(self):
        """Test closing a chat session."""
        session = ChatSession.objects.create(
            user=self.user,
            channel=self.channel,
        )
        session.close_session()

        session.refresh_from_db()
        assert session.is_active is False
        assert session.closed_at is not None


@pytest.mark.django_db
def test_build_conversation_context(chat_session, chat_messages):
    """Test building conversation context."""
    context = build_conversation_context(chat_session)

    assert len(context) == 3
    assert context[0]["role"] == "user"
    assert context[0]["content"] == "Hello"
    assert context[1]["role"] == "assistant"
    assert context[2]["role"] == "user"


@pytest.mark.django_db
def test_count_messages_in_session(chat_session, chat_messages):
    """Test counting messages in a session."""
    count = count_messages_in_session(chat_session)
    assert count == 3


@pytest.mark.django_db
def test_validate_session_active(chat_session):
    """Test validating session is active."""
    assert validate_session_active(chat_session) is True

    chat_session.close_session()
    assert validate_session_active(chat_session) is False


@pytest.mark.django_db
def test_validate_message_limit(chat_session, chatbot_config):
    """Test validating message limit."""
    # Create messages up to the limit
    for i in range(50):
        ChatMessage.objects.create(
            session=chat_session,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
        )

    # Should still be valid (equal to limit)
    assert validate_message_limit(chat_session) is False


@pytest.mark.django_db
def test_chatbot_config_creation(channel):
    """Test chatbot config creation."""
    config = ChatbotConfig.objects.create(
        channel=channel,
        is_enabled=True,
    )

    assert config.is_enabled is True
    assert config.ai_provider == "openai"
    assert config.model_name == "gpt-3.5-turbo"
    assert config.max_tokens == 500
    assert config.temperature == 0.7
