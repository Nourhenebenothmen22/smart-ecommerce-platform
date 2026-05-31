import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { EmptyState } from './EmptyState';

export const AuthRequiredState: React.FC<{ returnTo?: string }> = ({ returnTo = '/' }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div className="container" style={{ padding: '5rem 1.5rem' }}>
      <EmptyState
        title={t('states.authRequired')}
        message={t('states.loginRequired')}
        actionLabel={t('nav.login')}
        onAction={() => navigate('/login', { state: { from: { pathname: returnTo } } })}
      />
    </div>
  );
};
