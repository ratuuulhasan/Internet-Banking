import api from './axios';

export const chatApi = {
  listSessions: () => api.get('/chat/sessions/'),
  getSession: (id) => api.get(`/chat/sessions/${id}/`),
  getMessages: (id) => api.get(`/chat/sessions/${id}/messages/`),
  deleteSession: (id) => api.delete(`/chat/sessions/${id}/`),
  sendMessage: (sessionId, message) =>
    api.post('/chat/ask/', { session_id: sessionId, message }),
};

/**
 * SSE streaming helper. Uses fetch since axios doesn't support SSE streams well.
 */
export async function streamChat({ sessionId, message, onToken, onSources, onDone, onError }) {
  const token = localStorage.getItem('access');
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  try {
    const response = await fetch(`${apiUrl}/chat/stream/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ session_id: sessionId, message }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = JSON.parse(line.slice(6));

        if (payload.type === 'token') onToken?.(payload.content);
        else if (payload.type === 'sources') onSources?.(payload.sources);
        else if (payload.type === 'saved') onDone?.(payload.session_id);
        else if (payload.type === 'error') onError?.(payload.message);
        else if (payload.error) onError?.(payload.error);
      }
    }
  } catch (e) {
    onError?.(e.message);
  }
}