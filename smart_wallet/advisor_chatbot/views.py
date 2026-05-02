import os
import requests

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics

from .models import AdvisorChat
from .serializers import AdvisorAskSerializer, AdvisorChatSerializer
from .context_builder import build_financial_context


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL   = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """
You are a friendly, smart, and concise personal financial advisor embedded inside 
a budgeting app called Smart Wallet.

You will be given a real-time summary of the user's financial data: their wallet 
balance, this month's transactions, expense breakdown by category, active budgets, 
and saving goals.

Your job is to answer the user's financial question based ONLY on their actual data.
Be specific — mention real numbers from their data. Be encouraging but honest.
Keep your answer under 150 words. Use simple language, no jargon.
Do not make up data that is not in the summary.

If the user asks something unrelated to personal finance, politely redirect them.
"""


def call_claude(user_message: str, financial_context: str) -> str:
    """
    Calls the Anthropic API and returns the AI's text response.
    Raises an exception if the call fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    # Inject the user's live financial data into the user message
    full_user_message = (
        f"Here is my current financial data:\n\n"
        f"{financial_context}\n\n"
        f"My question: {user_message}"
    )

    payload = {
        "model":      ANTHROPIC_MODEL,
        "max_tokens": 400,
        "system":     SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": full_user_message}
        ],
    }

    response = requests.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=30)

    if response.status_code != 200:
        raise Exception(f"Anthropic API error {response.status_code}: {response.text}")

    data = response.json()
    return data["content"][0]["text"]


class AdvisorAskView(APIView):
    """
    BONUS FEATURE — AI Financial Advisor

    POST /advisor/ask/

    Body: { "message": "Am I overspending on food?" }

    The system collects the user's live financial data, builds a context
    summary, sends it along with the user's question to Claude, and returns
    a personalized financial answer.

    The exchange is saved to the database so the user can review past advice.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AdvisorAskSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data['message']
        user         = request.user

        # Build the user's financial context
        financial_context = build_financial_context(user)

        # Call Claude
        try:
            ai_response = call_claude(user_message, financial_context)
        except Exception as e:
            return Response(
                {"detail": f"AI service error: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Save to DB
        chat = AdvisorChat.objects.create(
            user         = user,
            user_message = user_message,
            ai_response  = ai_response,
        )

        return Response(
            AdvisorChatSerializer(chat).data,
            status=status.HTTP_201_CREATED
        )


class AdvisorHistoryView(generics.ListAPIView):
    """
    GET /advisor/history/

    Returns the user's past AI advisor conversations,
    most recent first. Useful for reviewing past advice.
    """
    serializer_class   = AdvisorChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AdvisorChat.objects.filter(user=self.request.user)
