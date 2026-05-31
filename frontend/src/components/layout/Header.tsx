import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useCart } from '../../hooks/api/useCart';
import { useTheme } from '../../hooks/useTheme';
import { useLanguage } from '../../hooks/useLanguage';
import { useDirection } from '../../hooks/useDirection';
import { Button } from '../ui/Button';

export const Header: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dir = useDirection();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, changeLanguage, languages } = useLanguage();
  const [searchQuery, setSearchQuery] = useState('');
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  // Fetch cart only if authenticated
  const { data: cartData } = useCart({ enabled: isAuthenticated });
  // Backend returns data with items. Let's count items.
  const cartItemsCount = cartData?.items?.reduce((acc: number, item: any) => acc + item.quantity, 0) || 0;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        backgroundColor: 'rgb(var(--card) / 0.85)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgb(var(--border))',
        width: '100%',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)',
      }}
    >
      {/* Top bar (Language & Theme toggle) */}
      <div
        style={{
          borderBottom: '1px solid rgb(var(--border) / 0.5)',
          padding: '0.4rem 1.5rem',
          fontSize: '0.8rem',
          color: 'rgb(var(--muted-foreground))',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          {t('footer.aboutUsDesc', 'Welcome to DarStore – Your Intelligent Marketplace')}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          {/* Theme selector */}
          <button
            onClick={toggleTheme}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              color: 'inherit',
              cursor: 'pointer',
            }}
          >
            {theme === 'dark' ? (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
                {t('nav.lightMode', 'Light Mode')}
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
                {t('nav.darkMode', 'Dark Mode')}
              </>
            )}
          </button>

          {/* Language selector */}
          <div style={{ position: 'relative', display: 'inline-block' }}>
            <span style={{ marginRight: '0.4rem' }}>🌐</span>
            <select
              value={language}
              onChange={(e) => changeLanguage(e.target.value as any)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'inherit',
                fontSize: 'inherit',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              {languages.map((lng) => (
                <option key={lng.code} value={lng.code} style={{ color: 'black' }}>
                  {lng.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main bar */}
      <div
        className="container"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.8rem 1.5rem',
          gap: '1.5rem',
        }}
      >
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <img
            src="/images/logo.png"
            alt="DarStore Logo"
            style={{ height: '38px', width: 'auto', objectFit: 'contain' }}
            onError={(e) => {
              // Fallback text if logo doesn't load
              e.currentTarget.style.display = 'none';
            }}
          />
          <span
            style={{
              fontSize: '1.5rem',
              fontWeight: 800,
              letterSpacing: '-0.5px',
              background: 'linear-gradient(135deg, rgb(var(--primary)) 0%, rgb(var(--accent)) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            DarStore
          </span>
        </Link>

        {/* Search bar */}
        <form
          onSubmit={handleSearch}
          style={{
            flexGrow: 1,
            maxWidth: '550px',
            position: 'relative',
            display: 'flex',
          }}
        >
          <input
            type="text"
            placeholder={t('nav.searchPlaceholder', 'Search products, brands and categories...')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input"
            style={{
              paddingLeft: dir === 'rtl' ? '1rem' : '2.75rem',
              paddingRight: dir === 'rtl' ? '2.75rem' : '1rem',
              borderRadius: '9999px',
              height: '42px',
              border: '1.5px solid rgb(var(--border))',
            }}
          />
          <button
            type="submit"
            style={{
              position: 'absolute',
              top: '50%',
              [dir === 'rtl' ? 'right' : 'left']: '1rem',
              transform: 'translateY(-50%)',
              color: 'rgb(var(--muted-foreground))',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </button>
        </form>

        {/* Actions (Home, Products, Cart, Profile dropdown) */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <Link
            to="/products"
            style={{
              fontSize: '0.9rem',
              fontWeight: 600,
              color: 'rgb(var(--foreground))',
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
            }}
          >
            {t('nav.products', 'Products')}
          </Link>

          {/* Cart Icon */}
          <Link
            to="/cart"
            style={{
              position: 'relative',
              padding: '0.5rem',
              color: 'rgb(var(--foreground))',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="9" cy="21" r="1" /><circle cx="20" cy="21" r="1" />
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
            </svg>
            {cartItemsCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: '-2px',
                  right: dir === 'rtl' ? 'auto' : '-2px',
                  left: dir === 'rtl' ? '-2px' : 'auto',
                  backgroundColor: 'rgb(var(--accent))',
                  color: 'rgb(var(--accent-foreground))',
                  fontSize: '0.7rem',
                  fontWeight: 800,
                  borderRadius: '50%',
                  minWidth: '18px',
                  height: '18px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '2px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
                }}
              >
                {cartItemsCount}
              </span>
            )}
          </Link>

          {/* Account profile dropdown */}
          <div style={{ position: 'relative' }}>
            {isAuthenticated ? (
              <>
                <button
                  onClick={() => setShowProfileMenu(!showProfileMenu)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    color: 'rgb(var(--foreground))',
                    fontWeight: 600,
                    fontSize: '0.9rem',
                    padding: '0.4rem 0.8rem',
                    borderRadius: '9999px',
                    border: '1.5px solid rgb(var(--border))',
                    cursor: 'pointer',
                  }}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
                  </svg>
                  <span style={{ maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {user?.firstName}
                  </span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {showProfileMenu && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '120%',
                      [dir === 'rtl' ? 'left' : 'right']: 0,
                      backgroundColor: 'rgb(var(--card))',
                      border: '1px solid rgb(var(--border))',
                      borderRadius: 'var(--radius)',
                      boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                      width: '200px',
                      zIndex: 110,
                      display: 'flex',
                      flexDirection: 'column',
                      overflow: 'hidden',
                      animation: 'fadeIn 0.15s ease',
                    }}
                    onClick={() => setShowProfileMenu(false)}
                  >
                    <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid rgb(var(--border) / 0.5)' }}>
                      <p style={{ fontWeight: 600, fontSize: '0.85rem' }}>{`${user?.firstName} ${user?.lastName}`}</p>
                      <p style={{ fontSize: '0.75rem', color: 'rgb(var(--muted-foreground))', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {user?.email}
                      </p>
                    </div>
                    {user?.role === 'admin' ? (
                      <Link
                        to="/admin"
                        style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: 'rgb(var(--foreground))', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                      >
                        💼 {t('nav.admin', 'Admin Dashboard')}
                      </Link>
                    ) : (
                      <Link
                        to="/customer"
                        style={{ padding: '0.6rem 1rem', fontSize: '0.85rem', color: 'rgb(var(--foreground))', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                      >
                        👤 {t('nav.profile', 'My Profile')}
                      </Link>
                    )}
                    <button
                      onClick={logout}
                      style={{
                        padding: '0.6rem 1rem',
                        fontSize: '0.85rem',
                        color: 'rgb(var(--danger))',
                        textAlign: dir === 'rtl' ? 'right' : 'left',
                        borderTop: '1px solid rgb(var(--border) / 0.5)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        cursor: 'pointer',
                        width: '100%',
                      }}
                    >
                      🚪 {t('nav.logout', 'Log Out')}
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
                  {t('nav.login', 'Log In')}
                </Button>
                <Button variant="primary" size="sm" onClick={() => navigate('/register')}>
                  {t('nav.register', 'Register')}
                </Button>
              </div>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
};
