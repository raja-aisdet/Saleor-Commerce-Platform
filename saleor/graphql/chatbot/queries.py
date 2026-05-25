"""GraphQL queries for chatbot."""

import graphene
from graphene import relay

from saleor.chatbot.models import ChatSession, ChatbotConfig
from saleor.graphql.chatbot.types import ChatSessionConnection, ChatSessionType


class Query(graphene.ObjectType):
    """Root query for chatbot."""

    chat_session = relay.Node.Field(ChatSessionType, description="Get a chat session")
    user_chat_sessions = relay.ConnectionField(
        ChatSessionConnection, description="Get all chat sessions for the current user"
    )

    @staticmethod
    def resolve_user_chat_sessions(root, info, **kwargs):
        """Get all chat sessions for the current user."""
        user = info.context.user
        if not user or not user.is_authenticated:
            return ChatSession.objects.none()

        return ChatSession.objects.filter(user=user).order_by("-started_at")
