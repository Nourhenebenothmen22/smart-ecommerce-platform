import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Button } from '../ui/Button';

export const Footer: React.FC = () => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setSubscribed(true);
      setEmail('');
    }
  };

  return (
    <footer
      style={{
        backgroundColor: 'rgb(var(--card))',
        borderTop: '1px solid rgb(var(--border))',
        color: 'rgb(var(--foreground))',
        padding: '4rem 1.5rem 2rem',
        marginTop: 'auto',
      }}
    >
      <div className="container" style={{ display: 'flex', flexWrap: 'wrap', gap: '3rem', justifyContent: 'space-between' }}>
        <div style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <span
            style={{
              fontSize: '1.5rem',
              fontWeight: 800,
              background: 'linear-gradient(135deg, rgb(var(--primary)) 0%, rgb(var(--accent)) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            DarStore
          </span>
          <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.875rem', lineHeight: '1.5' }}>
            {t('footer.aboutUsDesc')}
          </p>
        </div>

        <div style={{ flex: '1 1 150px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {t('footer.quickLinks')}
          </h4>
          <Link to="/" style={{ fontSize: '0.875rem', color: 'rgb(var(--muted-foreground))' }}>
            {t('nav.home')}
          </Link>
          <Link to="/products" style={{ fontSize: '0.875rem', color: 'rgb(var(--muted-foreground))' }}>
            {t('nav.products')}
          </Link>
          <Link to="/cart" style={{ fontSize: '0.875rem', color: 'rgb(var(--muted-foreground))' }}>
            {t('nav.cart')}
          </Link>
        </div>

        <div style={{ flex: '1 1 150px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {t('footer.customerService')}
          </h4>
          <a href="#" style={{ fontSize: '0.875rem', color: 'rgb(var(--muted-foreground))' }}>
            {t('footer.helpCenter')}
          </a>
          <a href="#" style={{ fontSize: '0.875rem', color: 'rgb(var(--muted-foreground))' }}>
            {t('footer.shippingInfo')}
          </a>
          <a href="#" style={{ fontSize: '0.875rem', color: 'rgb(var(--muted-foreground))' }}>
            {t('footer.returnPolicy')}
          </a>
        </div>

        <div style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {t('home.newsletter')}
          </h4>
          <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.875rem' }}>
            {t('home.newsletterSubtitle')}
          </p>
          {subscribed ? (
            <p style={{ color: 'rgb(var(--success))', fontSize: '0.875rem', fontWeight: 600 }}>
              <span aria-hidden="true">✓</span> {t('common.success')}
            </p>
          ) : (
            <form onSubmit={handleSubscribe} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
              <input
                type="email"
                required
                placeholder={t('home.emailPlaceholder')}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                style={{ height: '38px', fontSize: '0.8rem' }}
              />
              <Button type="submit" variant="primary" style={{ padding: '0 1rem', height: '38px' }}>
                {t('home.subscribe')}
              </Button>
            </form>
          )}
        </div>
      </div>

      <div style={{ borderTop: '1px solid rgb(var(--border) / 0.5)', marginTop: '3rem', paddingTop: '1.5rem', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: 'rgb(var(--muted-foreground))', gap: '1rem' }}>
        <p>
          &copy; {new Date().getFullYear()} DarStore. {t('footer.allRightsReserved')}
        </p>
        <div style={{ display: 'flex', gap: '1.5rem' }}>
          <a href="#">{t('footer.privacyPolicy')}</a>
          <a href="#">{t('footer.termsOfService')}</a>
        </div>
      </div>
    </footer>
  );
};
