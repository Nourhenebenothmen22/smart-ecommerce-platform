import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardBody, CardFooter } from '../../components/ui/Card';

export const Register: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    phone: '',
  });

  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.id]: e.target.value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await register(formData);
      navigate('/'); // Go home
    } catch (err: any) {
      setError(err.message || 'Registration failed. Check your credentials.');
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
        minHeight: '80vh',
        padding: '2rem 1.5rem',
      }}
    >
      <Card style={{ maxWidth: '450px', width: '100%', textAlign: 'left' }}>
        <CardHeader>
          <CardTitle>{t('auth.registerTitle', 'Create Your Account')}</CardTitle>
          <p style={{ fontSize: '0.85rem', color: 'rgb(var(--muted-foreground))' }}>
            Sign up today for a fast e-commerce checkout and AI deals.
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

            <div style={{ display: 'flex', gap: '1rem' }}>
              <Input
                id="firstName"
                type="text"
                label={t('auth.firstName', 'First Name')}
                placeholder="John"
                value={formData.firstName}
                onChange={handleChange}
                required
                disabled={isLoading}
              />
              <Input
                id="lastName"
                type="text"
                label={t('auth.lastName', 'Last Name')}
                placeholder="Doe"
                value={formData.lastName}
                onChange={handleChange}
                required
                disabled={isLoading}
              />
            </div>

            <Input
              id="email"
              type="email"
              label={t('auth.email', 'Email Address')}
              placeholder="name@example.com"
              value={formData.email}
              onChange={handleChange}
              required
              disabled={isLoading}
            />

            <Input
              id="phone"
              type="tel"
              label={t('auth.phone', 'Phone Number')}
              placeholder="+216 99 999 999"
              value={formData.phone}
              onChange={handleChange}
              required
              disabled={isLoading}
            />

            <Input
              id="password"
              type="password"
              label={t('auth.password', 'Password')}
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={isLoading}
            />
          </CardBody>
          <CardFooter style={{ flexDirection: 'column', alignItems: 'stretch', gap: '1rem' }}>
            <Button type="submit" variant="primary" style={{ width: '100%' }} isLoading={isLoading}>
              {t('auth.registerButton', 'Register Now')}
            </Button>
            <p style={{ fontSize: '0.85rem', textAlign: 'center', color: 'rgb(var(--muted-foreground))' }}>
              {t('auth.hasAccount', 'Already have an account?')}{' '}
              <Link to="/login" style={{ color: 'rgb(var(--primary))', fontWeight: 600 }}>
                {t('auth.login', 'Log In')}
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
