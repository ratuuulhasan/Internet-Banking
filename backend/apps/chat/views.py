"""
Chat API Views — Django
Handles sessions, messages, and streaming from AI service.
"""
import json
import traceback

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
    """Non-streaming chat."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Get or create session
        session = None
        if data.get('session_id'):
            session = ChatSession.objects.filter(
                session_id=data['session_id'], user=request.user
            ).first()
        if not session:
            session = ChatSession.objects.create(
                user=request.user,
                title=data['message'][:60],
            )

        # Save user message
        ChatMessage.objects.create(
            session=session, role='user', content=data['message']
        )

        # Build history
        history = [
            {'role': m.role, 'content': m.content}
            for m in session.messages.order_by('created_at')[:-1]
        ]

        # User context
        kyc = KYC.objects.filter(user=request.user).first()
        user_context = {
            'full_name': request.user.full_name,
            'role': request.user.role,
            'kyc_status': kyc.status if kyc else 'NOT_SUBMITTED',
        }

        try:
            r = requests.post(
                f"{settings.AI_SERVICE_URL}/chatbot/ask",
                json={
                    'message': data['message'],
                    'history': history,
                    'user_context': user_context,
                    'auth_token': str(request.auth) if request.auth else '',
                },
                timeout=60,
            )
            r.raise_for_status()
            result = r.json()
        except Exception as e:
            return Response(
                {'error': f'AI service error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

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
    """Stream OpenAI response via SSE."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id')

        if not message:
            return Response({'error': 'Empty message'}, status=400)

        # Get or create session
        session = None
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

        # Build history (exclude the message we just created)
        try:
            history = [
                {'role': m.role, 'content': m.content}
                for m in session.messages.order_by('created_at')[:-1]
            ]
        except Exception:
            history = []

        # User context
        try:
            kyc = KYC.objects.filter(user=request.user).first()
            user_context = {
                'full_name': request.user.full_name,
                'role': request.user.role,
                'kyc_status': kyc.status if kyc else 'NOT_SUBMITTED',
            }
        except Exception:
            user_context = {
                'full_name': request.user.full_name,
                'role': 'CUSTOMER',
                'kyc_status': 'UNKNOWN',
            }

        # Auth token safely
        try:
            auth_token = str(request.auth) if request.auth else ''
        except Exception:
            auth_token = ''

        ai_url = f"{settings.AI_SERVICE_URL}/chatbot/stream"

        # ---- Closure ----
        def event_stream():
            buffer = ''
            sources = []

            # Send early event so browser sees stream opening
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"

            try:
                with requests.post(
                    ai_url,
                    json={
                        'message': message,
                        'history': history,
                        'user_context': user_context,
                        'auth_token': auth_token,
                    },
                    stream=True,
                    timeout=120,
                    headers={'Accept': 'text/event-stream'},
                ) as r:
                    print(f"🔵 AI stream status: {r.status_code}")

                    if r.status_code != 200:
                        err_body = r.text[:500]
                        print(f"❌ AI err: {err_body}")
                        yield f"data: {json.dumps({'type': 'error', 'message': f'AI {r.status_code}: {err_body[:200]}'})}\n\n"
                        return

                    for line in r.iter_lines(decode_unicode=True):
                        if not line or not line.startswith('data: '):
                            continue

                        try:
                            payload = json.loads(line[6:])
                        except Exception:
                            continue

                        ptype = payload.get('type')
                        if ptype == 'sources':
                            sources = payload.get('sources', [])
                        elif ptype == 'token':
                            buffer += payload.get('content', '')
                        elif ptype == 'done':
                            break
                        elif ptype == 'error':
                            yield f"data: {json.dumps(payload)}\n\n"
                            return

                        yield f"data: {line[6:]}\n\n"

            except Exception as e:
                tb = traceback.format_exc()
                print(f"❌❌ Stream exception:\n{tb}")
                yield f"data: {json.dumps({'type': 'error', 'message': f'{type(e).__name__}: {e}'})}\n\n"
                return

            # Save final message
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
            except Exception as e:
                print(f"❌ Save msg error: {e}")

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream',
            status=200,
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response