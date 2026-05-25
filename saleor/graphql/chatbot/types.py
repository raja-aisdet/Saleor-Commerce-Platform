"""GraphQL types for chatbot."""

from typing import Optional

import graphene
from graphene import relay

from saleor.chatbot.models import ChatMessage, ChatSession, ChatbotConfig
from saleor.core.connection import CountableConnection
from saleor.graphql.core.types import BaseObjectType
from saleor.graphql.core.types.common import PermissionDisplay
from saleor.permission import ChatbotPermissions


class ChatMessageType(BaseObjectType):
    """GraphQL type for ChatMessage."""

    id = graphene.ID(required=True)
    role = graphene.String(required=True, description="Role of the message sender")
    content = graphene.String(required=True, description="Message content")
    metadata = graphene.JSONString(description="Additional metadata")
    created_at = graphene.DateTime(required=True)

    class Meta:
        name = "ChatMessage"
        model = ChatMessage
        interfaces = (relay.Node,)
        fields = ["id", "role", "content", "metadata", "created_at"]

    @staticmethod
    def resolve_id(root, info):
        return root.id


class ChatSessionType(BaseObjectType):
    """GraphQL type for ChatSession."""

    id = graphene.ID(required=True)
    user = graphene.Field(lambda: "saleor.graphql.account.types.UserType")
    channel = graphene.Field(lambda: "saleor.graphql.channel.types.ChannelType")
    title = graphene.String()
    is_active = graphene.Boolean(required=True)
    messages = relay.ConnectionField(
        "saleor.graphql.chatbot.types.ChatMessageConnection"
    )
    metadata = graphene.JSONString()
    started_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    closed_at = graphene.DateTime()
    message_count = graphene.Int()

    class Meta:
        name = "ChatSession"
        model = ChatSession
        interfaces = (relay.Node,)
        fields = [
            "id",
            "user",
            "channel",
            "title",
            "is_active",
            "metadata",
            "started_at",
            "updated_at",
            "closed_at",
        ]

    @staticmethod
    def resolve_id(root, info):
        return root.id

    @staticmethod
    def resolve_messages(root, info, **kwargs):
        return root.messages.all()

    @staticmethod
    def resolve_message_count(root, info):
        return root.messages.count()


class ChatMessageConnection(CountableConnection):
    """Connection type for ChatMessage."""

    class Meta:
        node = ChatMessageType


class ChatSessionConnection(CountableConnection):
    """Connection type for ChatSession."""

    class Meta:
        node = ChatSessionType


class ChatbotConfigType(BaseObjectType):
    """GraphQL type for ChatbotConfig."""

    id = graphene.ID(required=True)
    channel = graphene.Field(lambda: "saleor.graphql.channel.types.ChannelType")
    is_enabled = graphene.Boolean(required=True)
    ai_provider = graphene.String(required=True)
    system_prompt = graphene.String(required=True)
    model_name = graphene.String(required=True)
    max_tokens = graphene.Int(required=True)
    temperature = graphene.Float(required=True)
    max_messages_per_session = graphene.Int(required=True)
    session_timeout_hours = graphene.Int(required=True)
    metadata = graphene.JSONString()

    class Meta:
        name = "ChatbotConfig"
        model = ChatbotConfig
        interfaces = (relay.Node,)
        fields = [
            "id",
            "channel",
            "is_enabled",
            "ai_provider",
            "system_prompt",
            "model_name",
            "max_tokens",
            "temperature",
            "max_messages_per_session",
            "session_timeout_hours",
            "metadata",
        ]

    @staticmethod
    def resolve_id(root, info):
        return root.id
