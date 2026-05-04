from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, DestroyModelMixin

from .models import Notification
from .serializer import NotificationSerializer


class NotificationViewSet(ListModelMixin,
                          RetrieveModelMixin,
                          DestroyModelMixin,
                          GenericViewSet):
    """
    US #11 — Notifications Center

    list:   GET  /notifications/          → all notifications (unread first)
    read:   GET  /notifications/{id}/     → single notification (marks as read)
    delete: DELETE /notifications/{id}/  → delete a notification
    mark_all_read: POST /notifications/mark_all_read/  → mark all as read
    unread_count: GET /notifications/unread_count/     → count of unread
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Return a single notification and mark it as read automatically."""
        instance = self.get_object()
        if not instance.is_read:
            instance.is_read = True
            instance.save(update_fields=['is_read'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """
        Return all notifications. Unread notifications come first.
        Also includes a summary of total and unread counts.
        """
        qs = self.get_queryset()
        # unread first, then by timestamp desc
        qs = qs.order_by('is_read', '-timestamp')
        serializer = self.get_serializer(qs, many=True)
        unread_count = qs.filter(is_read=False).count()
        return Response({
            'unread_count': unread_count,
            'total_count': qs.count(),
            'notifications': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='mark_all_read')
    def mark_all_read(self, request):
        """Mark all of the user's notifications as read."""
        updated = Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return Response({
            'detail': f'{updated} notification(s) marked as read.'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='unread_count')
    def unread_count(self, request):
        """Return only the unread notification count (lightweight poll endpoint)."""
        count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return Response({'unread_count': count})

    @action(detail=True, methods=['patch'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        """Mark a single notification as read without fully retrieving it."""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'detail': 'Notification marked as read.'}, status=status.HTTP_200_OK)
