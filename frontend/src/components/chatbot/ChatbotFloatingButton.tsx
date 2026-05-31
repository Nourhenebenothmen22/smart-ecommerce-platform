import React, { useState } from 'react';
import { MessageCircle, Sparkles } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { ChatbotPanel } from './ChatbotPanel';

export const ChatbotFloatingButton: React.FC = () => {
  const { loading, isAuthenticated, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  if (loading || !isAuthenticated || user?.role !== 'customer') {
    return null;
  }

  return (
    <>
      {isOpen && <ChatbotPanel onClose={() => setIsOpen(false)} />}
      <button
        type="button"
        className="chatbot-floating-button"
        aria-label={isOpen ? 'Close customer chatbot' : 'Open customer chatbot'}
        onClick={() => setIsOpen((current) => !current)}
        style={{
          position: 'fixed',
          right: '1.25rem',
          bottom: '1.25rem',
          zIndex: 1001,
          width: '64px',
          height: '64px',
          borderRadius: '999px',
          background: 'linear-gradient(135deg, rgb(var(--primary)), #0f766e 58%, #14b8a6)',
          color: 'white',
          boxShadow: '0 18px 42px rgba(15, 118, 110, 0.35), 0 8px 18px rgba(15, 23, 42, 0.18)',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          overflow: 'visible',
        }}
      >
        <span className="chatbot-floating-pulse" />
        <span className="chatbot-floating-icon">
          <MessageCircle size={28} strokeWidth={2.4} />
          <Sparkles className="chatbot-floating-sparkle" size={14} strokeWidth={2.8} />
        </span>
        <style>{`
          .chatbot-floating-button {
            transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease;
          }

          .chatbot-floating-button:hover {
            transform: translateY(-4px) scale(1.04);
            filter: saturate(1.08);
            box-shadow: 0 24px 52px rgba(15, 118, 110, 0.42), 0 10px 24px rgba(15, 23, 42, 0.2);
          }

          .chatbot-floating-button:active {
            transform: translateY(-1px) scale(0.98);
          }

          .chatbot-floating-pulse {
            position: absolute;
            inset: -7px;
            border-radius: 999px;
            border: 2px solid rgba(20, 184, 166, 0.45);
            animation: chatbot-pulse 2.2s ease-out infinite;
          }

          .chatbot-floating-icon {
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
          }

          .chatbot-floating-sparkle {
            position: absolute;
            top: 16px;
            right: 15px;
            color: #fde68a;
          }

          @keyframes chatbot-pulse {
            0% {
              opacity: 0.75;
              transform: scale(0.9);
            }
            70% {
              opacity: 0;
              transform: scale(1.22);
            }
            100% {
              opacity: 0;
              transform: scale(1.22);
            }
          }
        `}</style>
      </button>
    </>
  );
};
