import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Globe2, Menu, Moon, Search, ShoppingCart, Sun, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../contexts/AuthContext';
import { useCart } from '../../hooks/api/useCart';

export const Navbar: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [languageOpen, setLanguageOpen] = useState(false);
  const { i18n, t } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  const { loading, isAuthenticated, logout } = useAuth();
  const { data: cart } = useCart({ enabled: isAuthenticated });
  const cartItems = Array.isArray(cart) ? cart : cart?.items ?? [];
  const cartCount = cartItems.reduce((total: number, item: any) => total + Number(item.quantity ?? 0), 0);

  const languages = [
    { code: 'en', labelKey: 'language.en' },
    { code: 'fr', labelKey: 'language.fr' },
    { code: 'ar', labelKey: 'language.ar' },
  ];

  const changeLanguage = async (code: string) => {
    await i18n.changeLanguage(code);
    localStorage.setItem('darstore-language', code);
    document.documentElement.lang = code;
    document.documentElement.dir = code === 'ar' ? 'rtl' : 'ltr';
    setLanguageOpen(false);
    setOpen(false);
  };

  return (
    <header className="navbar">
      <button className="navbar-toggle" onClick={() => setOpen((value) => !value)} aria-label={t('nav.toggleNavigation')}>
        {open ? <X size={22} /> : <Menu size={22} />}
      </button>

      <div className="navbar-search">
        <Search size={17} />
        <input placeholder={t('nav.searchPlaceholder')} />
      </div>

      <nav className={`navbar-auth ${open ? 'is-open' : ''}`}>
        <div className="navbar-language">
          <button
            className="language-trigger"
            onClick={() => setLanguageOpen((value) => !value)}
            aria-label={t('nav.language')}
            aria-expanded={languageOpen}
          >
            <Globe2 size={18} />
          </button>
          {languageOpen && (
            <div className="language-menu">
              {languages.map((language) => (
                <button
                  key={language.code}
                  className={i18n.language.startsWith(language.code) ? 'active' : ''}
                  onClick={() => void changeLanguage(language.code)}
                >
                  {t(language.labelKey)}
                </button>
              ))}
            </div>
          )}
        </div>
        <button
          type="button"
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? t('nav.lightMode') : t('nav.darkMode')}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <Link to="/cart" className="navbar-cart-link" onClick={() => setOpen(false)} aria-label={t('nav.cart')}>
          <ShoppingCart size={18} />
          <span>{cartCount}</span>
        </Link>
        {!loading && !isAuthenticated && (
          <>
            <Link to="/login" onClick={() => setOpen(false)}>{t('nav.login')}</Link>
            <Link to="/register" className="navbar-register" onClick={() => setOpen(false)}>{t('nav.register')}</Link>
          </>
        )}
        {!loading && isAuthenticated && (
          <button
            type="button"
            className="navbar-logout"
            onClick={() => {
              setOpen(false);
              void logout();
            }}
          >
            {t('nav.logout', 'Logout')}
          </button>
        )}
      </nav>

      <Link to="/" className="navbar-logo" onClick={() => setOpen(false)} aria-label={t('nav.logoHome')}>
        <img src="/images/logo.png" alt={t('nav.logoAlt')} />
      </Link>
    </header>
  );
};
