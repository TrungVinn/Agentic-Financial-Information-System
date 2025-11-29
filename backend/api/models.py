from django.conf import settings
from django.db import models
import uuid


class Conversation(models.Model):
    """
    Một phiên chat giữa người dùng và agent.

    Nếu user là null => phiên tạm (không gắn tài khoản).
    Nếu có user => lịch sử thuộc về tài khoản đó.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="conversations",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:  # pragma: no cover - hỗ trợ debug/admin
        return self.title or f"Conversation {self.id}"


class Message(models.Model):
    """
    Một tin nhắn trong phiên chat.
    """

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
    ]

    id = models.BigAutoField(primary_key=True)
    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()

    # Thông tin kỹ thuật thêm cho assistant
    sql = models.TextField(blank=True)
    used_sample = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    rows_json = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"[{self.role}] {self.content[:50]}"
