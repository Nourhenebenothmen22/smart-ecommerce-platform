import React, { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Footer } from './components/layout/Footer';
import { Navbar } from './components/layout/Navbar';
import { HeroCarousel } from './components/home/HeroCarousel';
import { PageLoader } from './components/shared/PageLoader';
import { ForbiddenState } from './components/shared/ForbiddenState';
import { AuthRequiredState } from './components/shared/AuthRequiredState';
import { SplashScreen } from './components/shared/SplashScreen';
import { Home } from './pages/public/Home';
import { ProductDetails } from './pages/public/ProductDetails';
import { Cart } from './pages/public/Cart';
import { Login } from './pages/public/Login';
import { Register } from './pages/public/Register';
import { CustomerDashboard } from './pages/customer/CustomerDashboard';
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { ChatbotFloatingButton } from './components/chatbot/ChatbotFloatingButton';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

function DirectionSync() {
  const { i18n } = useTranslation();

  useEffect(() => {
    const lang = i18n.language?.startsWith('ar') ? 'ar' : i18n.language?.startsWith('fr') ? 'fr' : 'en';
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  }, [i18n.language]);

  return null;
}

function AdminRedirect() {
  const { loading, isAdmin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && isAdmin && location.pathname !== '/admin') {
      navigate('/admin', { replace: true });
    }
  }, [isAdmin, loading, location.pathname, navigate]);

  return null;
}

function PublicLayout() {
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <>
      <Navbar />
      {isHome && <HeroCarousel />}
      <main style={{ flex: 1 }}>
        <Outlet />
      </main>
      <Footer />
    </>
  );
}

function RequireAuth({ adminOnly = false }: { adminOnly?: boolean }) {
  const { loading, isAuthenticated, isAdmin } = useAuth();
  const location = useLocation();

  if (loading) return <PageLoader />;
  if (!isAuthenticated) return <AuthRequiredState returnTo={location.pathname} />;
  if (adminOnly && !isAdmin) return <ForbiddenState />;
  return <Outlet />;
}

function NotFound() {
  return <Navigate to="/" replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<Home />} />
        <Route path="products" element={<Navigate to="/" replace />} />
        <Route path="product/:id" element={<ProductDetails />} />
        <Route path="cart" element={<Cart />} />
        <Route path="login" element={<Login />} />
        <Route path="admin/login" element={<Login />} />
        <Route path="register" element={<Register />} />

        <Route element={<RequireAuth />}>
          <Route path="customer" element={<CustomerDashboard />} />
        </Route>

        <Route element={<RequireAuth adminOnly />}>
          <Route path="admin" element={<AdminDashboard />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default function App() {
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(() => setShowSplash(false), 6000);
    return () => window.clearTimeout(timer);
  }, []);

  if (showSplash) {
    return <SplashScreen />;
  }

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <DirectionSync />
          <AdminRedirect />
          <AppRoutes />
          <ChatbotFloatingButton />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
