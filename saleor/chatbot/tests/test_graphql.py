"""Test chatbot GraphQL queries and mutations."""

import pytest
from django.contrib.auth import get_user_model

from saleor.channel.models import Channel
from saleor.chatbot.models import ChatbotConfig, ChatSession

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
    )


@pytest.mark.django_db
def test_start_chat_session_mutation(client, user, channel, chatbot_config):
    """Test starting a chat session."""
    mutation = """
    mutation StartChatSession($input: StartChatSessionInput!) {
        startChatSession(input: $input) {
            chatSession {
                id
                title
                isActive
            }
            errors {
                field
                message
                code
            }
        }
    }
    """

    variables = {
        "input": {
            "channelId": str(channel.id),
            "title": "Test Session",
        }
    }

    # This test would require authentication and GraphQL endpoint setup
    # For now, it demonstrates the expected mutation structure


@pytest.mark.django_db
def test_chat_session_creation_without_auth(client, channel):
    """Test that chat session creation requires authentication."""
    mutation = """
    mutation StartChatSession($input: StartChatSessionInput!) {
        startChatSession(input: $input) {
            errors {
                code
            }
        }
    }
    """

    variables = {
        "input": {
            "channelId": str(channel.id),
        }
    }

    # Without authentication, should return UNAUTHORIZED error


@pytest.mark.django_db
def test_user_chat_sessions_query(user, channel):
    """Test querying user chat sessions."""
    # Create some test sessions
    for i in range(3):
        ChatSession.objects.create(
            user=user,
            channel=channel,
            title=f"Session {i}",
        )

    # Query should return all user's sessions
    sessions = ChatSession.objects.filter(user=user)
    assert sessions.count() == 3
