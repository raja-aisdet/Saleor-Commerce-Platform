"""GraphQL mutations for chatbot."""

import graphene

from saleor.chatbot.error_codes import ChatbotErrorCode
from saleor.chatbot.models import ChatMessage, ChatSession, ChatbotConfig
from saleor.chatbot.utils import (
    create_chat_message,
    get_chatbot_response,
    validate_message_limit,
    validate_session_active,
)
from saleor.channel.models import Channel
from saleor.core.exceptions import PermissionDenied
from saleor.graphql.chatbot.types import ChatMessageType, ChatSessionType
from saleor.graphql.core.types.common import GenericScalar
from saleor.permission import ChatbotPermissions


class ChatbotError(graphene.ObjectType):
    """Error object for chatbot operations."""

    field = graphene.String(description="Name of a field that caused the error")
    message = graphene.String(description="The error message")
    code = graphene.String(description="The error code")


class StartChatSessionInput(graphene.InputObjectType):
    """Input for starting a new chat session."""

    channel_id = graphene.ID(required=True, description="Channel ID")
    title = graphene.String(description="Optional session title")


class StartChatSession(graphene.Mutation):
    """Start a new chat session."""

    chat_session = graphene.Field(ChatSessionType)
    errors = graphene.List(ChatbotError)

    class Arguments:
        input = StartChatSessionInput(required=True)

    @staticmethod
    def mutate(root, info, input: StartChatSessionInput):
        """Create a new chat session."""
        user = info.context.user
        if not user or not user.is_authenticated:
            return StartChatSession(
                chat_session=None,
                errors=[
                    ChatbotError(
                        field="user",
                        message="User must be authenticated",
                        code=ChatbotErrorCode.UNAUTHORIZED,
                    )
                ],
            )

        try:
            channel = Channel.objects.get(id=input.channel_id)
        except Channel.DoesNotExist:
            return StartChatSession(
                chat_session=None,
                errors=[
                    ChatbotError(
                        field="channel",
                        message="Channel not found",
                        code=ChatbotErrorCode.INVALID_CHANNEL,
                    )
                ],
            )

        # Check if chatbot is enabled for this channel
        config = ChatbotConfig.objects.filter(channel=channel).first()
        if not config or not config.is_enabled:
            return StartChatSession(
                chat_session=None,
                errors=[
                    ChatbotError(
                        field="channel",
                        message="Chatbot is not enabled for this channel",
                        code=ChatbotErrorCode.INVALID_CHANNEL,
                    )
                ],
            )

        # Create new session
        chat_session = ChatSession.objects.create(
            user=user,
            channel=channel,
            title=input.title or "Chat Session",
        )

        return StartChatSession(chat_session=chat_session, errors=[])


class SendMessageInput(graphene.InputObjectType):
    """Input for sending a message."""

    session_id = graphene.ID(required=True, description="Chat session ID")
    message = graphene.String(required=True, description="Message content")


class SendMessage(graphene.Mutation):
    """Send a message in a chat session."""

    chat_session = graphene.Field(ChatSessionType)
    message = graphene.Field(ChatMessageType)
    response = graphene.Field(ChatMessageType)
    errors = graphene.List(ChatbotError)

    class Arguments:
        input = SendMessageInput(required=True)

    @staticmethod
    def mutate(root, info, input: SendMessageInput):
        """Process a user message and get AI response."""
        user = info.context.user
        if not user or not user.is_authenticated:
            return SendMessage(
                chat_session=None,
                message=None,
                response=None,
                errors=[
                    ChatbotError(
                        field="user",
                        message="User must be authenticated",
                        code=ChatbotErrorCode.UNAUTHORIZED,
                    )
                ],
            )

        try:
            chat_session = ChatSession.objects.get(id=input.session_id)
        except ChatSession.DoesNotExist:
            return SendMessage(
                chat_session=None,
                message=None,
                response=None,
                errors=[
                    ChatbotError(
                        field="session",
                        message="Chat session not found",
                        code=ChatbotErrorCode.SESSION_NOT_FOUND,
                    )
                ],
            )

        # Verify user owns this session
        if chat_session.user_id != user.id:
            return SendMessage(
                chat_session=None,
                message=None,
                response=None,
                errors=[
                    ChatbotError(
                        field="session",
                        message="You don't have access to this session",
                        code=ChatbotErrorCode.UNAUTHORIZED,
                    )
                ],
            )

        # Validate session is active
        if not validate_session_active(chat_session):
            return SendMessage(
                chat_session=chat_session,
                message=None,
                response=None,
                errors=[
                    ChatbotError(
                        field="session",
                        message="Chat session is no longer active",
                        code=ChatbotErrorCode.GRAPHQL_ERROR,
                    )
                ],
            )

        # Validate message limit
        if not validate_message_limit(chat_session):
            return SendMessage(
                chat_session=chat_session,
                message=None,
                response=None,
                errors=[
                    ChatbotError(
                        field="message",
                        message="Message limit reached for this session",
                        code=ChatbotErrorCode.RATE_LIMIT_EXCEEDED,
                    )
                ],
            )

        # Validate input
        if not input.message or not input.message.strip():
            return SendMessage(
                chat_session=chat_session,
                message=None,
                response=None,
                errors=[
                    ChatbotError(
                        field="message",
                        message="Message cannot be empty",
                        code=ChatbotErrorCode.INVALID_INPUT,
                    )
                ],
            )

        try:
            # Create user message
            user_message = create_chat_message(
                chat_session, "user", input.message.strip()
            )

            # Get AI response
            config = ChatbotConfig.objects.get(channel=chat_session.channel)
            response_text, metadata = get_chatbot_response(
                chat_session, input.message.strip(), config
            )

            # Create assistant message
            assistant_message = create_chat_message(
                chat_session, "assistant", response_text, metadata
            )

            return SendMessage(
                chat_session=chat_session,
                message=user_message,
                response=assistant_message,
                errors=[],
            )

        except ValueError as e:
            return SendMessage(
                chat_session=chat_session,
                message=None,
                response=None,
                errors=[
                    ChatbotError(
                        field="chatbot",
                        message=str(e),
                        code=ChatbotErrorCode.INVALID_CHANNEL,
                    )
                ],
            )

        except Exception as e:
            return SendMessage(
                chat_session=chat_session,
                message=None,
                response=None,
                errors=[
                    ChatbotError(
                        field="ai_service",
                        message="Error getting AI response",
                        code=ChatbotErrorCode.AI_SERVICE_ERROR,
                    )
                ],
            )


class CloseChatSessionInput(graphene.InputObjectType):
    """Input for closing a chat session."""

    session_id = graphene.ID(required=True, description="Chat session ID")


class CloseChatSession(graphene.Mutation):
    """Close a chat session."""

    chat_session = graphene.Field(ChatSessionType)
    errors = graphene.List(ChatbotError)

    class Arguments:
        input = CloseChatSessionInput(required=True)

    @staticmethod
    def mutate(root, info, input: CloseChatSessionInput):
        """Close a chat session."""
        user = info.context.user
        if not user or not user.is_authenticated:
            return CloseChatSession(
                chat_session=None,
                errors=[
                    ChatbotError(
                        field="user",
                        message="User must be authenticated",
                        code=ChatbotErrorCode.UNAUTHORIZED,
                    )
                ],
            )

        try:
            chat_session = ChatSession.objects.get(id=input.session_id)
        except ChatSession.DoesNotExist:
            return CloseChatSession(
                chat_session=None,
                errors=[
                    ChatbotError(
                        field="session",
                        message="Chat session not found",
                        code=ChatbotErrorCode.SESSION_NOT_FOUND,
                    )
                ],
            )

        # Verify user owns this session
        if chat_session.user_id != user.id:
            return CloseChatSession(
                chat_session=None,
                errors=[
                    ChatbotError(
                        field="session",
                        message="You don't have access to this session",
                        code=ChatbotErrorCode.UNAUTHORIZED,
                    )
                ],
            )

        chat_session.close_session()

        return CloseChatSession(chat_session=chat_session, errors=[])


class Mutation(graphene.ObjectType):
    """Root mutation for chatbot."""

    start_chat_session = StartChatSession.Field(
        description="Start a new chat session"
    )
    send_message = SendMessage.Field(description="Send a message in a chat session")
    close_chat_session = CloseChatSession.Field(description="Close a chat session")
