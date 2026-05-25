"""Initial chatbot migration."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Create initial chatbot models."""

    initial = True

    dependencies = [
        ("account", "0002_alter_user_last_name"),
        ("channel", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatbotConfig",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_enabled",
                    models.BooleanField(
                        default=True,
                        help_text="Whether chatbot is enabled for this channel",
                    ),
                ),
                (
                    "ai_provider",
                    models.CharField(
                        choices=[("openai", "OpenAI"), ("custom", "Custom")],
                        default="openai",
                        help_text="AI service provider",
                        max_length=50,
                    ),
                ),
                (
                    "system_prompt",
                    models.TextField(
                        default="You are a helpful shopping assistant. Help customers find products and answer questions about their orders.",
                        help_text="System prompt for the AI model",
                    ),
                ),
                (
                    "model_name",
                    models.CharField(
                        default="gpt-3.5-turbo",
                        help_text="Name of the AI model to use",
                        max_length=100,
                    ),
                ),
                (
                    "max_tokens",
                    models.IntegerField(
                        default=500, help_text="Maximum tokens per response"
                    ),
                ),
                (
                    "temperature",
                    models.FloatField(
                        default=0.7,
                        help_text="Temperature for AI model (0.0-1.0)",
                    ),
                ),
                (
                    "max_messages_per_session",
                    models.IntegerField(
                        default=100,
                        help_text="Maximum messages allowed per session",
                    ),
                ),
                (
                    "session_timeout_hours",
                    models.IntegerField(
                        default=24, help_text="Session timeout in hours"
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional configuration metadata",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="When the configuration was last updated",
                    ),
                ),
                (
                    "channel",
                    models.OneToOneField(
                        help_text="Channel this configuration applies to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chatbot_config",
                        to="channel.channel",
                    ),
                ),
            ],
            options={
                "verbose_name": "Chatbot Configuration",
                "verbose_name_plural": "Chatbot Configurations",
            },
        ),
        migrations.CreateModel(
            name="ChatSession",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        blank=True,
                        help_text="Title or summary of the chat session",
                        max_length=500,
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Whether the chat session is currently active",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional metadata for the chat session",
                    ),
                ),
                (
                    "started_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="When the chat session was started",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="When the chat session was last updated",
                    ),
                ),
                (
                    "closed_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When the chat session was closed",
                        null=True,
                    ),
                ),
                (
                    "channel",
                    models.ForeignKey(
                        help_text="Channel where the chat session was initiated",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chat_sessions",
                        to="channel.channel",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User associated with this chat session",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chat_sessions",
                        to="account.user",
                    ),
                ),
            ],
            options={
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("user", "User"),
                            ("assistant", "Assistant"),
                            ("system", "System"),
                        ],
                        help_text="Role of who sent the message",
                        max_length=20,
                    ),
                ),
                (
                    "content",
                    models.TextField(help_text="Content of the message"),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional metadata for the message (e.g., confidence score, products referenced)",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="When the message was created",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        help_text="Chat session this message belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="chatbot.chatsession",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="chatsession",
            index=models.Index(
                fields=["user", "-started_at"], name="chatbot_cha_user_id_59a7b8_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="chatsession",
            index=models.Index(
                fields=["channel", "-started_at"],
                name="chatbot_cha_channel_a1b2c3_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="chatsession",
            index=models.Index(fields=["is_active"], name="chatbot_cha_is_acti_d4e5f6_idx"),
        ),
        migrations.AddIndex(
            model_name="chatmessage",
            index=models.Index(
                fields=["session", "created_at"],
                name="chatbot_cha_session_g7h8i9_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="chatmessage",
            index=models.Index(fields=["role"], name="chatbot_cha_role_j0k1l2_idx"),
        ),
    ]
