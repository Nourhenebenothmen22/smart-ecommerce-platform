import React from 'react';
import { useTranslation } from 'react-i18next';
import { RetryButton } from './RetryButton';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  onRetry,
}) => {
  const { t } = useTranslation();
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 2rem',
        textAlign: 'center',
        background: 'rgb(var(--card))',
        border: '1px solid rgb(var(--border))',
        borderRadius: 'var(--radius)',
      }}
    >
      <svg
        style={{ width: '3.5rem', height: '3.5rem', color: 'rgb(var(--danger))', marginBottom: '1rem' }}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <h3 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '0.5rem', color: 'rgb(var(--foreground))' }}>
        {title || t('states.somethingWentWrong')}
      </h3>
      <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.875rem', marginBottom: '1.5rem', maxWidth: '350px' }}>
        {message || t('states.error')}
      </p>
      {onRetry && (
        <RetryButton onRetry={onRetry} />
      )}
    </div>
  );
};
