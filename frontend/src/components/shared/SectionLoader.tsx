import React from 'react';

export const SectionLoader: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem',
      }}
    >
      <div
        style={{
          width: '2rem',
          height: '2rem',
          border: '3px solid rgb(var(--muted))',
          borderTopColor: 'rgb(var(--primary))',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }}
      />
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
