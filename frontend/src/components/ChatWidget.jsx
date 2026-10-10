import { useState, useRef, useEffect } from 'react';
import { Button, Card, Form, Spinner, Badge } from 'react-bootstrap';
import { streamChat } from '../api/chat';

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 আসসালামু আলাইকুম! আমি আপনার ব্যাংকিং সহকারী। কীভাবে সাহায্য করতে পারি?\n\nHello! I\'m your banking assistant. How can I help?',
    },
  ]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [streaming, setStreaming] = useState(false);
  const [currentSources, setCurrentSources] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || streaming) return;

    setInput('');
    setMessages((m) => [...m, { role: 'user', content: text }]);
    setMessages((m) => [...m, { role: 'assistant', content: '', streaming: true }]);
    setStreaming(true);
    setCurrentSources([]);

    await streamChat({
      sessionId,
      message: text,
      onSources: (sources) => setCurrentSources(sources),
      onToken: (token) => {
        setMessages((m) => {
          const copy = [...m];
          const last = copy[copy.length - 1];
          copy[copy.length - 1] = {
            ...last,
            content: last.content + token,
          };
          return copy;
        });
      },
      onDone: (sid) => {
        setSessionId(sid);
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = {
            ...copy[copy.length - 1],
            streaming: false,
            sources: currentSources,
          };
          return copy;
        });
        setStreaming(false);
      },
      onError: (err) => {
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = {
            role: 'assistant',
            content: `❌ Error: ${err}`,
          };
          return copy;
        });
        setStreaming(false);
      },
    });
  };

  return (
    <>
      {!open && (
        <Button
          onClick={() => setOpen(true)}
          style={{
            position: 'fixed', bottom: 20, right: 20,
            borderRadius: '50%', width: 60, height: 60,
            fontSize: 28, zIndex: 1050,
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          }}
          variant="primary"
        >
          💬
        </Button>
      )}

      {open && (
        <Card
          style={{
            position: 'fixed', bottom: 20, right: 20,
            width: 400, height: 600, zIndex: 1050,
            boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
          }}
        >
          <Card.Header className="d-flex justify-content-between align-items-center bg-primary text-white">
            <div>
              <strong>🤖 Banking Assistant</strong>
              <br />
              <small>বাংলা / English</small>
            </div>
            <Button
              variant="outline-light" size="sm"
              onClick={() => setOpen(false)}
            >
              ✕
            </Button>
          </Card.Header>

          <Card.Body
            style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}
          >
            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                }}
              >
                <div
                  style={{
                    background: m.role === 'user' ? '#0d6efd' : '#f1f3f5',
                    color: m.role === 'user' ? 'white' : 'black',
                    padding: '8px 12px',
                    borderRadius: 12,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {m.content}
                  {m.streaming && <Spinner animation="grow" size="sm" className="ms-2" />}
                </div>
                {m.sources?.length > 0 && (
                  <div className="mt-1">
                    {m.sources.map((s, j) => (
                      <Badge key={j} bg="secondary" className="me-1" style={{ fontSize: 9 }}>
                        📄 {s}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </Card.Body>

          <Card.Footer>
            <Form onSubmit={handleSend} className="d-flex gap-2">
              <Form.Control
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question..."
                disabled={streaming}
              />
              <Button type="submit" disabled={streaming || !input.trim()}>
                {streaming ? '...' : '➤'}
              </Button>
            </Form>
          </Card.Footer>
        </Card>
      )}
    </>
  );
}