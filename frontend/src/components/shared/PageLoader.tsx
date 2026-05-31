import React from 'react';
import { useTranslation } from 'react-i18next';

export const PageLoader: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        gap: '1rem',
      }}
    >
      <div
        style={{
          width: '3rem',
          height: '3rem',
          border: '4px solid rgb(var(--muted))',
          borderTopColor: 'rgb(var(--primary))',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }}
      />
      <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.875rem' }}>
        {t('states.loading')}
      </p>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
