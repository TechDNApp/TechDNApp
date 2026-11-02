from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "text", "is_read", "created_at")
    can_delete = False

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'assessment', 'student', 'instructor', 'created_at', 'updated_at')
    search_fields = ('student__username', 'instructor__username', 'assessment__title')
    list_filter = ('created_at',)
    inlines = [MessageInline] 

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'text', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')