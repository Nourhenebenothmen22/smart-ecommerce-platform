import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardBody, CardFooter } from '../../components/ui/Card';

export const Login: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Check if there is a redirect query param
  const from = (location.state as any)?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setIsLoading(true);
    setError('');

    try {
      const user = await login({ email, password });
      if (user.role === 'admin') {
        navigate('/admin');
      } else {
        navigate(from);
      }
    } catch (err: any) {
      setError(err.message || 'Invalid email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '70vh',
        padding: '2rem 1.5rem',
      }}
    >
      <Card style={{ maxWidth: '400px', width: '100%', textAlign: 'left' }}>
        <CardHeader>
          <CardTitle>{t('auth.loginTitle', 'Log In to DarStore')}</CardTitle>
          <p style={{ fontSize: '0.85rem', color: 'rgb(var(--muted-foreground))' }}>
            Enter your credentials below to access your account.
          </p>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardBody style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {error && (
              <div
                style={{
                  backgroundColor: 'rgb(var(--danger) / 0.1)',
                  color: 'rgb(var(--danger))',
                  padding: '0.75rem',
                  borderRadius: 'var(--radius)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                }}
              >
                ⚠️ {error}
              </div>
            )}

            <Input
              id="email"
              type="email"
              label={t('auth.email', 'Email Address')}
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />

            <Input
              id="password"
              type="password"
              label={t('auth.password', 'Password')}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </CardBody>
          <CardFooter style={{ flexDirection: 'column', alignItems: 'stretch', gap: '1rem' }}>
            <Button type="submit" variant="primary" style={{ width: '100%' }} isLoading={isLoading}>
              {t('auth.loginButton', 'Sign In')}
            </Button>
            <p style={{ fontSize: '0.85rem', textAlign: 'center', color: 'rgb(var(--muted-foreground))' }}>
              {t('auth.noAccount', "Don't have an account?")}{' '}
              <Link to="/register" style={{ color: 'rgb(var(--primary))', fontWeight: 600 }}>
                {t('auth.register', 'Register')}
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
