from django.contrib import admin
from .models import AdvisorChat


@admin.register(AdvisorChat)
class AdvisorChatAdmin(admin.ModelAdmin):
    list_display  = ['id', 'user', 'short_message', 'created_at']
    search_fields = ['user__username', 'user_message']
    ordering      = ['-created_at']
    readonly_fields = ['user', 'user_message', 'ai_response', 'created_at']

    def short_message(self, obj):
        return obj.user_message[:80]
    short_message.short_description = 'User Message'
