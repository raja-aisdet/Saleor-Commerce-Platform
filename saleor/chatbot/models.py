from django.db import models
from django.utils import timezone

from saleor.account.models import User
from saleor.channel.models import Channel
from saleor.core.models import BaseModel


class ChatSession(BaseModel):
    """Model for storing chat session data."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
        help_text="User associated with this chat session",
    )
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
        help_text="Channel where the chat session was initiated",
    )
    title = models.CharField(
        max_length=500,
        blank=True,
        help_text="Title or summary of the chat session",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the chat session is currently active",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata for the chat session",
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the chat session was started",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the chat session was last updated",
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the chat session was closed",
    )

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user", "-started_at"]),
            models.Index(fields=["channel", "-started_at"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        """Return string representation."""
        return f"Chat Session {self.id} - {self.user.email}"

    def close_session(self):
        """Close the chat session."""
        self.is_active = False
        self.closed_at = timezone.now()
        self.save(update_fields=["is_active", "closed_at"])


class ChatMessage(BaseModel):
    """Model for storing individual chat messages."""

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        help_text="Chat session this message belongs to",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="Role of who sent the message",
    )
    content = models.TextField(
        help_text="Content of the message",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata for the message (e.g., confidence score, products referenced)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the message was created",
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        """Return string representation."""
        return f"Message {self.id} - {self.role} in Session {self.session.id}"


class ChatbotConfig(BaseModel):
    """Global configuration for the chatbot."""

    channel = models.OneToOneField(
        Channel,
        on_delete=models.CASCADE,
        related_name="chatbot_config",
        help_text="Channel this configuration applies to",
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Whether chatbot is enabled for this channel",
    )
    ai_provider = models.CharField(
        max_length=50,
        default="openai",
        choices=[("openai", "OpenAI"), ("custom", "Custom")],
        help_text="AI service provider",
    )
    system_prompt = models.TextField(
        default="You are a helpful shopping assistant. Help customers find products and answer questions about their orders.",
        help_text="System prompt for the AI model",
    )
    model_name = models.CharField(
        max_length=100,
        default="gpt-3.5-turbo",
        help_text="Name of the AI model to use",
    )
    max_tokens = models.IntegerField(
        default=500,
        help_text="Maximum tokens per response",
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="Temperature for AI model (0.0-1.0)",
    )
    max_messages_per_session = models.IntegerField(
        default=100,
        help_text="Maximum messages allowed per session",
    )
    session_timeout_hours = models.IntegerField(
        default=24,
        help_text="Session timeout in hours",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional configuration metadata",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the configuration was last updated",
    )

    class Meta:
        verbose_name = "Chatbot Configuration"
        verbose_name_plural = "Chatbot Configurations"

    def __str__(self):
        """Return string representation."""
        return f"Chatbot Config - {self.channel.name}"
