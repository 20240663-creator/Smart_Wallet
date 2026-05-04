from django.urls import path
from .views import AdvisorAskView, AdvisorHistoryView

urlpatterns = [
    path('ask/',     AdvisorAskView.as_view(),     name='advisor-ask'),
    path('history/', AdvisorHistoryView.as_view(), name='advisor-history'),
]
