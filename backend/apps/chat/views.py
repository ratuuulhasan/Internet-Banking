import json
import requests
from django.conf import settings
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer, ChatMessageSerializer, SendMessageSerializer,
)
from apps.kyc.models import KYC


class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        session = self.get_object()
        msgs = session.messages.all()
        return Response(ChatMessageSerializer(msgs, many=True).data)


class ChatAPIView(APIView):
    """Non-streaming chat — for fallback."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Get or create session
        if data.get('session_id'):
            try:
                session = ChatSession.objects.get(
                    session_id=data['session_id'], user=request.user
                )
            except ChatSession.DoesNotExist:
                return Response({'error': 'Session not found'}, status=404)
        else:
            session = ChatSession.objects.create(
                user=request.user,
                title=data['message'][:60],
            )

        # Save user message
        ChatMessage.objects.create(session=session, role='user', content=data['message'])

        # Build history
        history = [
            {'role': m.role, 'content': m.content}
            for m in session.messages.order_by('created_at')[:-1]
        ]

        # Get user context
        kyc = KYC.objects.filter(user=request.user).first()
        user_context = {
            'full_name': request.user.full_name,
            'role': request.user.role,
            'kyc_status': kyc.status if kyc else 'NOT_SUBMITTED',
        }

        # Call AI service
        try:
            r = requests.post(
                f"{settings.AI_SERVICE_URL}/chatbot/ask",
                json={
                    'message': data['message'],
                    'history': history,
                    'user_context': user_context,
                    'auth_token': str(request.auth),
                },
                timeout=30,
            )
            r.raise_for_status()
            result = r.json()
        except Exception as e:
            return Response(
                {'error': f'AI service error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Save assistant message
        ai_msg = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=result.get('reply', ''),
            sources=result.get('sources', []),
            tool_calls=result.get('tool_calls', []),
            tokens_used=result.get('tokens_used', 0),
        )

        session.updated_at = timezone.now()
        session.save()

        return Response({
            'session_id': session.session_id,
            'message': ChatMessageSerializer(ai_msg).data,
        })


class ChatStreamView(APIView):
    """
    Stream OpenAI response via SSE.
    Django uses StreamingHttpResponse with sync generator.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id')

        if not message:
            return Response({'error': 'Empty message'}, status=400)

        # Get or create session
        if session_id:
            session = ChatSession.objects.filter(
                session_id=session_id, user=request.user
            ).first()
        if not session:
            session = ChatSession.objects.create(
                user=request.user,
                title=message[:60],
            )

        ChatMessage.objects.create(session=session, role='user', content=message)

        history = [
            {'role': m.role, 'content': m.content}
            for m in session.messages.order_by('created_at')[:-1]
        ]

        kyc = KYC.objects.filter(user=request.user).first()
        user_context = {
            'full_name': request.user.full_name,
            'role': request.user.role,
            'kyc_status': kyc.status if kyc else 'NOT_SUBMITTED',
        }

        auth_token = str(request.auth)

        def stream_generator():
            import requests as req
            buffer = ''
            sources = []
            try:
                with req.post(
                    f"{settings.AI_SERVICE_URL}/chatbot/stream",
                    json={
                        'message': message,
                        'history': history,
                        'user_context': user_context,
                        'auth_token': auth_token,
                    },
                    stream=True,
                    timeout=120,
                ) as r:
                    for line in r.iter_lines(decode_unicode=True):
                        if not line or not line.startswith('data: '):
                            continue
                        payload = json.loads(line[6:])

                        if payload['type'] == 'sources':
                            sources = payload['sources']
                        elif payload['type'] == 'token':
                            buffer += payload['content']
                        elif payload['type'] == 'done':
                            break
                        elif payload['type'] == 'error':
                            yield f"data: {json.dumps({'error': payload['message']})}\n\n"
                            return

                        yield f"data: {line[6:]}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

            # Save final assistant message
            try:
                ChatMessage.objects.create(
                    session=session,
                    role='assistant',
                    content=buffer,
                    sources=sources,
                )
                session.updated_at = timezone.now()
                session.save()

                yield f"data: {json.dumps({'type': 'saved', 'session_id': session.session_id})}\n\n"
            except Exception:
                pass

        response = StreamingHttpResponse(
            stream_generator(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response