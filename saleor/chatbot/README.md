# AI Shopping Assistant (Chatbot) - Implementation Guide

## Overview

The AI Shopping Assistant is a chatbot module integrated into Saleor that provides intelligent customer support using OpenAI's GPT models. It helps customers find products, answer questions about orders, and provide shopping assistance.

## Features

### 1. **Chat Sessions**
- Users can start multiple chat sessions per channel
- Sessions track conversation history
- Automatic session timeout management
- Session metadata for storing custom data

### 2. **AI Integration**
- Integration with OpenAI API (GPT-3.5-turbo by default, configurable to GPT-4)
- Customizable system prompts per channel
- Configurable response parameters (temperature, max tokens)
- Rate limiting and message limits per session

### 3. **Message Management**
- Store chat history in database
- Differentiate between user, assistant, and system messages
- Message metadata for tracking confidence scores and referenced products
- Full conversation context for coherent responses

### 4. **Configuration**
- Per-channel chatbot configuration
- Enable/disable chatbot per channel
- Configurable AI model parameters
- Session timeout and message limits

### 5. **Background Tasks**
- Automatic cleanup of expired sessions
- Data retention policies
- Celery task scheduling

## GraphQL API

### Queries

#### Get User Chat Sessions
```graphql
query {
  userChatSessions(first: 10) {
    edges {
      node {
        id
        title
        isActive
        startedAt
        messageCount
        messages(first: 50) {
          edges {
            node {
              id
              role
              content
              createdAt
            }
          }
        }
      }
    }
  }
}
```

#### Get Specific Chat Session
```graphql
query {
  chatSession(id: "Q2hhdFNlc3Npb246MQ==") {
    id
    title
    isActive
    messages {
      edges {
        node {
          id
          role
          content
          createdAt
        }
      }
    }
  }
}
```

### Mutations

#### Start Chat Session
```graphql
mutation {
  startChatSession(input: {
    channelId: "Q2hhbm5lbDox"
    title: "Product Inquiry"
  }) {
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
```

#### Send Message
```graphql
mutation {
  sendMessage(input: {
    sessionId: "Q2hhdFNlc3Npb246MQ=="
    message: "Can you recommend a blue shirt?"
  }) {
    chatSession {
      id
      messageCount
    }
    message {
      id
      role
      content
      createdAt
    }
    response {
      id
      role
      content
      metadata
      createdAt
    }
    errors {
      field
      message
      code
    }
  }
}
```

#### Close Chat Session
```graphql
mutation {
  closeChatSession(input: {
    sessionId: "Q2hhdFNlc3Npb246MQ=="
  }) {
    chatSession {
      id
      isActive
      closedAt
    }
    errors {
      field
      message
      code
    }
  }
}
```

## Models

### ChatSession
Represents a conversation session between a user and the AI assistant.

**Fields:**
- `id` - Unique identifier
- `user` - Associated user
- `channel` - Channel where session was initiated
- `title` - Session title/description
- `is_active` - Whether session is currently active
- `started_at` - Session creation timestamp
- `updated_at` - Last update timestamp
- `closed_at` - Session closure timestamp
- `metadata` - Additional JSON metadata

### ChatMessage
Represents individual messages in a conversation.

**Fields:**
- `id` - Unique identifier
- `session` - Associated chat session
- `role` - Message role (user/assistant/system)
- `content` - Message text
- `created_at` - Creation timestamp
- `metadata` - Additional metadata (tokens used, confidence score, etc.)

### ChatbotConfig
Global configuration for chatbot behavior per channel.

**Fields:**
- `channel` - Associated channel (one-to-one)
- `is_enabled` - Enable/disable chatbot
- `ai_provider` - AI service provider (openai/custom)
- `system_prompt` - System instruction for AI model
- `model_name` - Model identifier
- `max_tokens` - Maximum response length
- `temperature` - Response randomness (0.0-1.0)
- `max_messages_per_session` - Maximum messages allowed
- `session_timeout_hours` - Session inactivity timeout

## Configuration

### Environment Variables

```bash
# OpenAI API key (required for AI functionality)
OPENAI_API_KEY=sk-...
```

### Django Settings

The chatbot app is automatically added to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...
    "saleor.chatbot",
    ...
]
```

### Celery Tasks

Add these to your Celery beat schedule for background tasks:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "close-expired-chat-sessions": {
        "task": "saleor.chatbot.tasks.close_expired_chat_sessions",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
    "cleanup-old-chat-sessions": {
        "task": "saleor.chatbot.tasks.cleanup_old_chat_sessions",
        "schedule": crontab(minute=0, hour=2),  # Daily at 2 AM
        "kwargs": {"days": 90},
    },
}
```

## Usage Example

### Python API

```python
from saleor.chatbot.models import ChatSession, ChatbotConfig
from saleor.chatbot.utils import create_chat_message, get_chatbot_response

# Get or create session
session = ChatSession.objects.create(
    user=user,
    channel=channel,
    title="Product Inquiry"
)

# Create user message
user_msg = create_chat_message(session, "user", "What products do you have?")

# Get AI response
config = ChatbotConfig.objects.get(channel=channel)
response_text, metadata = get_chatbot_response(session, "What products do you have?", config)

# Create assistant message
assistant_msg = create_chat_message(session, "assistant", response_text, metadata)
```

## Error Handling

The module includes comprehensive error handling with specific error codes:

- `INVALID_INPUT` - Invalid message or parameters
- `AI_SERVICE_ERROR` - Error from OpenAI API
- `SESSION_NOT_FOUND` - Session doesn't exist
- `UNAUTHORIZED` - User not authenticated or unauthorized
- `RATE_LIMIT_EXCEEDED` - Message limit reached
- `INVALID_CHANNEL` - Invalid channel or chatbot disabled

## Testing

Run chatbot tests:

```bash
pytest saleor/chatbot/tests/
```

### Test Files
- `test_models.py` - Model tests
- `test_graphql.py` - GraphQL API tests

## Security Considerations

1. **Authentication** - All chat endpoints require authenticated users
2. **Authorization** - Users can only access their own sessions
3. **Rate Limiting** - Configurable message limits prevent abuse
4. **Data Privacy** - Session data stored in database, configurable retention
5. **API Keys** - OpenAI API key must be securely configured

## Performance Optimization

- Database indexes on frequently queried fields
- Session timeout to prevent unlimited memory usage
- Message limit to prevent excessive database growth
- Batch operations for cleanup tasks

## Future Enhancements

1. **Product Integration** - Context-aware product recommendations
2. **Order Integration** - Order lookup and status checks
3. **Analytics** - Track conversation metrics and satisfaction
4. **Multi-language Support** - Language detection and translation
5. **Human Handoff** - Route to live support when needed
6. **Custom AI Models** - Support for custom/fine-tuned models
7. **Webhook Events** - Emit events for external integrations

## Contributing

When contributing to the chatbot module:

1. Follow Saleor's testing guidelines (see AGENTS.md)
2. Add tests for new features
3. Update GraphQL schema as needed
4. Document new features in this guide
5. Ensure thread safety for concurrent operations

## Support

For issues or questions about the chatbot implementation, refer to:
- Saleor Documentation: https://docs.saleor.io
- GitHub Issues: https://github.com/saleor/saleor/issues
- Community Discord: https://saleor.io/discord
