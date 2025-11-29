from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface cho Conversation model."""
    list_display = ['id', 'title', 'user', 'created_at', 'updated_at', 'message_count']
    list_filter = ['created_at', 'updated_at', 'user']
    search_fields = ['title', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def message_count(self, obj):
        """Hiển thị số lượng messages trong conversation."""
        return obj.messages.count()
    message_count.short_description = 'Số tin nhắn'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface cho Message model."""
    list_display = ['id', 'conversation', 'role', 'content_preview', 'created_at', 'has_sql', 'has_error']
    list_filter = ['role', 'created_at', 'used_sample', 'conversation__user']
    search_fields = ['content', 'sql', 'conversation__title', 'conversation__user__username']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    raw_id_fields = ['conversation']
    
    def content_preview(self, obj):
        """Hiển thị preview của content (50 ký tự đầu)."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Nội dung'
    
    def has_sql(self, obj):
        """Kiểm tra xem message có SQL không."""
        return bool(obj.sql and obj.sql.strip())
    has_sql.short_description = 'Có SQL'
    has_sql.boolean = True
    
    def has_error(self, obj):
        """Kiểm tra xem message có lỗi không."""
        return bool(obj.error and obj.error.strip())
    has_error.short_description = 'Có lỗi'
    has_error.boolean = True
