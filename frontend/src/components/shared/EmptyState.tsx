import React from 'react';
import { Button } from '../ui/Button';

interface EmptyStateProps {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  message,
  actionLabel,
  onAction,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '4rem 2rem',
        textAlign: 'center',
        background: 'rgb(var(--card))',
        border: '1px border rgb(var(--border))',
        borderRadius: 'var(--radius)',
      }}
    >
      <svg
        style={{ width: '4rem', height: '4rem', color: 'rgb(var(--muted-foreground))', marginBottom: '1rem' }}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.5"
          d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
        />
      </svg>
      <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem', color: 'rgb(var(--foreground))' }}>
        {title}
      </h3>
      <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.875rem', marginBottom: '1.5rem', maxWidth: '300px' }}>
        {message}
      </p>
      {actionLabel && onAction && (
        <Button onClick={onAction} variant="primary">
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
