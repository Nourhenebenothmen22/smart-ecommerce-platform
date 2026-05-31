import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../ui/Button';

export const RetryButton: React.FC<{ onRetry: () => void }> = ({ onRetry }) => {
  const { t } = useTranslation();
  return (
    <Button onClick={onRetry} variant="outline">
      {t('common.retry')}
    </Button>
  );
};
