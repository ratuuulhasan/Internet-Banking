from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Card
from .serializers import CardSerializer, CardLimitSerializer
from apps.audit.utils import log_action


class CardViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(account__user=self.request.user)

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        card = self.get_object()
        if card.status == 'BLOCKED':
            return Response({'error': 'Already blocked'}, status=400)
        card.status = 'BLOCKED'
        card.save()
        log_action(request.user, 'CARD_BLOCKED', 'Card', card.card_id)
        return Response({'message': 'Card blocked', 'status': card.status})

    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        card = self.get_object()
        if card.status != 'BLOCKED':
            return Response({'error': 'Card is not blocked'}, status=400)
        card.status = 'ACTIVE'
        card.save()
        log_action(request.user, 'CARD_UNBLOCKED', 'Card', card.card_id)
        return Response({'message': 'Card unblocked', 'status': card.status})

    @action(detail=True, methods=['post'])
    def set_limit(self, request, pk=None):
        card = self.get_object()
        serializer = CardLimitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card.daily_limit = serializer.validated_data['daily_limit']
        card.save()
        log_action(request.user, 'CARD_LIMIT_SET', 'Card', card.card_id,
                   {'limit': str(card.daily_limit)})
        return Response(CardSerializer(card).data)