"""Permissions for chatbot module."""

from enum import Enum


class ChatbotPermissions(str, Enum):
    """Chatbot-related permissions."""

    MANAGE_CHATBOT = "manage_chatbot"
    MANAGE_CHATBOT_CONFIG = "manage_chatbot_config"
    VIEW_CHATBOT_SESSIONS = "view_chatbot_sessions"
