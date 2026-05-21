from django.db import models
from django.contrib.auth.models import User


class ChatSession(models.Model):
    """One chat session per user with admin support."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_session')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"Chat with {self.user.username}"

    class Meta:
        ordering = ['-updated_at']


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:40]}"

    class Meta:
        ordering = ['timestamp']

