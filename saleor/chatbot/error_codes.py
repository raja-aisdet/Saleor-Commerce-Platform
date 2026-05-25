from enum import Enum


class ChatbotErrorCode(str, Enum):
    """Error codes for chatbot operations."""

    INVALID_INPUT = "invalid_input"
    AI_SERVICE_ERROR = "ai_service_error"
    SESSION_NOT_FOUND = "session_not_found"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_CHANNEL = "invalid_channel"
    GRAPHQL_ERROR = "graphql_error"
