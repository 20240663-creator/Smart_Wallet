from rest_framework import serializers
from .models import AdvisorChat


class AdvisorChatSerializer(serializers.ModelSerializer):
    """Serializer for returning a stored chat turn."""
    class Meta:
        model  = AdvisorChat
        fields = ['id', 'user_message', 'ai_response', 'created_at']
        read_only_fields = fields


class AdvisorAskSerializer(serializers.Serializer):
    """Serializer for the incoming user question."""
    message = serializers.CharField(
        max_length=1000,
        help_text="Your financial question (e.g. 'Am I overspending on food?')"
    )
