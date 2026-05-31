import React, { useRef, useState } from 'react';
import { Send, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { chatService } from '../../services/chatService';

type ChatMessage = {
  id: string;
  role: 'customer' | 'bot';
  text: string;
};

type ChatbotPanelProps = {
  onClose: () => void;
};

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Chatbot service failed. Please try again.';
}

export const ChatbotPanel: React.FC<ChatbotPanelProps> = ({ onClose }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const query = input.trim();
    if (!query || isLoading) return;

    const customerMessage: ChatMessage = {
      id: `customer-${Date.now()}`,
      role: 'customer',
      text: query,
    };

    setMessages((current) => [...current, customerMessage]);
    setInput('');
    setError('');
    setIsLoading(true);

    try {
      const result = await chatService.sendMessage(query, sessionId);
      setSessionId(result.session_id);
      setMessages((current) => [
        ...current,
        {
          id: `bot-${Date.now()}`,
          role: 'bot',
          text: result.response,
        },
      ]);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <section
      aria-label="Customer chatbot"
      style={{
        position: 'fixed',
        right: '1.25rem',
        bottom: '5.5rem',
        zIndex: 1000,
        width: 'min(360px, calc(100vw - 2rem))',
        height: '460px',
        background: 'rgb(var(--card))',
        border: '1px solid rgb(var(--border))',
        borderRadius: 'var(--radius)',
        boxShadow: '0 18px 45px rgba(15, 23, 42, 0.18)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <header
        style={{
          padding: '0.9rem 1rem',
          borderBottom: '1px solid rgb(var(--border))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
        }}
      >
        <div>
          <strong style={{ display: 'block', fontSize: '0.95rem' }}>Customer Chatbot</strong>
          <span style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.75rem' }}>
            Ask about products or your shopping needs
          </span>
        </div>
        <button
          type="button"
          aria-label="Close chatbot"
          onClick={onClose}
          style={{ color: 'rgb(var(--muted-foreground))', cursor: 'pointer' }}
        >
          <X size={20} />
        </button>
      </header>

      <div
        style={{
          flex: 1,
          padding: '1rem',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
      >
        {messages.length === 0 && (
          <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.85rem', margin: 0 }}>
            Send a message to start chatting with the assistant.
          </p>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            style={{
              alignSelf: message.role === 'customer' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              padding: '0.7rem 0.8rem',
              borderRadius: 'var(--radius)',
              background:
                message.role === 'customer'
                  ? 'rgb(var(--primary))'
                  : 'rgb(var(--muted) / 0.55)',
              color: message.role === 'customer' ? 'white' : 'rgb(var(--foreground))',
              fontSize: '0.86rem',
              lineHeight: 1.45,
              whiteSpace: 'pre-wrap',
            }}
          >
            {message.text}
          </div>
        ))}

        {isLoading && (
          <div style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.85rem' }}>
            Chatbot is thinking...
          </div>
        )}

        {error && (
          <div
            role="alert"
            style={{
              color: 'rgb(var(--danger))',
              background: 'rgb(var(--danger) / 0.1)',
              borderRadius: 'var(--radius)',
              padding: '0.65rem 0.75rem',
              fontSize: '0.82rem',
              fontWeight: 600,
            }}
          >
            {error}
          </div>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        style={{
          borderTop: '1px solid rgb(var(--border))',
          padding: '0.8rem',
          display: 'flex',
          gap: '0.5rem',
        }}
      >
        <input
          ref={inputRef}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type your message..."
          maxLength={500}
          disabled={isLoading}
          className="input"
          style={{ flex: 1, height: '40px' }}
        />
        <Button
          type="submit"
          aria-label="Send chatbot message"
          size="sm"
          disabled={!input.trim()}
          isLoading={isLoading}
          style={{ height: '40px', width: '44px', padding: 0, justifyContent: 'center' }}
        >
          {!isLoading && <Send size={17} />}
        </Button>
      </form>
    </section>
  );
};
