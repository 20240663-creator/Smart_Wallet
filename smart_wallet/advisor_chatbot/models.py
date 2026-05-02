from django.db import models
from django.conf import settings


class AdvisorChat(models.Model):
    """
    Stores every message exchange between the user and the AI advisor.
    Each row is one full conversation turn (user message + AI reply).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='advisor_chats'
    )
    user_message = models.TextField()
    ai_response  = models.TextField()
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} | {self.created_at:%Y-%m-%d %H:%M} | {self.user_message[:60]}"
