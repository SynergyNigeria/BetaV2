from django.contrib import admin
from .models import ChatSession, ChatMessage

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at', 'is_closed']
    list_filter = ['is_closed']
    search_fields = ['user__username']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'sender', 'content', 'timestamp', 'is_read']
    list_filter = ['is_read']
    search_fields = ['sender__username', 'content']

