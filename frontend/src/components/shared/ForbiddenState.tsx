import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../ui/Button';

export const ForbiddenState: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        padding: '2rem',
        textAlign: 'center',
      }}
    >
      <svg
        style={{ width: '5rem', height: '5rem', color: 'rgb(var(--danger))', marginBottom: '1.5rem' }}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.5"
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
      <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.75rem', color: 'rgb(var(--foreground))' }}>
        {t('states.forbidden')}
      </h1>
      <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '1rem', marginBottom: '2rem', maxWidth: '400px' }}>
        {t('states.noPermission')}
      </p>
      <Button onClick={() => (window.location.href = '/')} variant="primary">
        {t('states.goHome')}
      </Button>
    </div>
  );
};
