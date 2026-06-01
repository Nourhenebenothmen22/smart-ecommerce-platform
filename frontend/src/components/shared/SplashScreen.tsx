import React from 'react';
import { useTranslation } from 'react-i18next';

export const SplashScreen: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="splash-screen" role="status" aria-label={t('splash.loading')}>
      <div className="splash-orb splash-orb-one" />
      <div className="splash-orb splash-orb-two" />
      <div className="splash-particles" aria-hidden="true">
        {Array.from({ length: 18 }).map((_, index) => (
          <span key={index} style={{ '--particle-index': index } as React.CSSProperties} />
        ))}
      </div>

      <div className="splash-content">
        <div className="splash-logo-frame">
          <span className="splash-ring" />
          <img src="/images/logo.png" alt={t('nav.logoAlt')} />
        </div>
        <div className="splash-copy">
          <span>{t('splash.eyebrow')}</span>
          <h1>{t('splash.title')}</h1>
          <p>{t('splash.subtitle')}</p>
        </div>
        <div className="splash-loader" aria-hidden="true">
          <span />
        </div>
      </div>
    </div>
  );
};
