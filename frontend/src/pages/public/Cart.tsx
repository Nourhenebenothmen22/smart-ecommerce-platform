import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useCart, useUpdateCartItem, useRemoveFromCart } from '../../hooks/api/useCart';
import { useCreateOrder } from '../../hooks/api/useOrders';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/Button';
import { PageLoader } from '../../components/shared/PageLoader';
import { EmptyState } from '../../components/shared/EmptyState';
import { formatPrice } from '../../lib/utils';
import { API_BASE_URL } from '../../config/api';

function getCartItems(cart: any) {
  return Array.isArray(cart) ? cart : cart?.items ?? [];
}

function getItemProductId(item: any) {
  return String(item.product?.id ?? item.product_id ?? '');
}

function getItemName(item: any) {
  return item.product?.name ?? item.product?.title ?? item.name ?? item.title ?? '';
}

function getItemPrice(item: any) {
  return Number(item.product?.price ?? item.product?.final_price ?? item.price ?? item.final_price ?? 0);
}

function getItemStock(item: any) {
  return Number(item.product?.stock ?? item.stock ?? 0);
}

function getItemImage(item: any) {
  const image = item.product?.image ?? item.product?.thumbnail ?? item.thumbnail ?? item.product?.images?.[0];
  if (!image) return '';
  const value = String(image);
  if (value.startsWith('http') || value.startsWith('/hero') || value.startsWith('/images')) return value;
  return `${API_BASE_URL}${value}`;
}

export const Cart: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [paymentMethod, setPaymentMethod] = useState<'cash_on_delivery' | 'credit_card'>('cash_on_delivery');
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState('');

  const { data: cart, isLoading, refetch } = useCart({ enabled: isAuthenticated });
  const { mutate: updateQuantity } = useUpdateCartItem();
  const { mutate: removeItem } = useRemoveFromCart();
  const { mutate: createOrder } = useCreateOrder();

  const isCustomer = user?.role === 'customer';

  if (!isAuthenticated) {
    return (
      <div className="container" style={{ padding: '6rem 2rem', textAlign: 'center' }}>
        <EmptyState
          title={t('states.loginRequired')}
          message={t('order.loginCustomer')}
          actionLabel={t('nav.login')}
          onAction={() => navigate('/login')}
        />
      </div>
    );
  }

  if (isLoading) return <PageLoader />;

  const items = getCartItems(cart);

  if (items.length === 0) {
    return (
      <div className="container" style={{ padding: '4rem 2rem' }}>
        <EmptyState
          title={t('cart.title', 'Your Cart is Empty')}
          message={t('cart.emptyMessage', 'Browse our products and add items to your cart to begin shopping!')}
          actionLabel={t('cart.continueShopping', 'Start Shopping')}
          onAction={() => navigate('/products')}
        />
      </div>
    );
  }

  // Calculate Subtotal (price * quantity)
  const subtotal = items.reduce((acc: number, item: any) => {
    return acc + getItemPrice(item) * item.quantity;
  }, 0);

  const shipping = subtotal > 150 ? 0 : 15; // Free shipping over $150
  const tax = subtotal * 0.05; // 5% tax
  const total = subtotal + shipping + tax;

  const handleQtyChange = (productId: string, newQty: number, stock: number) => {
    if (newQty < 1 || newQty > stock) return;
    updateQuantity(
      { productId, quantity: newQty },
      {
        onSuccess: () => refetch(),
        onError: (err: any) => alert(err.message || 'Failed to update quantity'),
      }
    );
  };

  const handleRemove = (productId: string) => {
    if (window.confirm('Remove this product from your cart?')) {
      removeItem(productId, {
        onSuccess: () => refetch(),
        onError: (err: any) => alert(err.message || 'Failed to remove product'),
      });
    }
  };

  const handleCheckout = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isCustomer || checkoutLoading) return;

    setCheckoutError('');
    setCheckoutLoading(true);

    const orderItems = items.map((item: any) => ({
      product_id: Number(getItemProductId(item)),
      quantity: item.quantity,
    }));

    createOrder(
      {
        items: orderItems,
        payment_method: paymentMethod,
      },
      {
        onSuccess: () => {
          setCheckoutError('');
          navigate('/customer'); // Redirect to customer profile/orders dashboard
        },
        onError: (err: any) => {
          setCheckoutError(err.message || t('order.error'));
        },
        onSettled: () => {
          setCheckoutLoading(false);
        },
      }
    );
  };

  return (
    <div className="container" style={{ paddingBottom: '4rem', paddingTop: '2rem', textAlign: 'left' }}>
      <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '2rem' }}>
        {t('cart.title', 'Shopping Cart')}
      </h1>

      <div className="cart-checkout-layout">
        {/* Left Side: Cart Items List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {items.map((item: any) => (
            <div
              key={item.id ?? getItemProductId(item)}
              style={{
                display: 'flex',
                gap: '1.5rem',
                backgroundColor: 'rgb(var(--card))',
                border: '1px solid rgb(var(--border))',
                borderRadius: 'var(--radius)',
                padding: '1rem',
                alignItems: 'center',
              }}
            >
              {/* Product Thumbnail */}
              <div
                style={{
                  width: '90px',
                  height: '90px',
                  backgroundColor: 'rgb(var(--muted) / 0.3)',
                  borderRadius: 'var(--radius)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden',
                  flexShrink: 0,
                }}
              >
                {getItemImage(item) ? (
                  <img
                    src={getItemImage(item)}
                    alt={getItemName(item)}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                ) : (
                  <span style={{ fontSize: '1.5rem' }}>📦</span>
                )}
              </div>

              {/* Title & Price */}
              <div style={{ flexGrow: 1 }}>
                <Link
                  to={`/product/${getItemProductId(item)}`}
                  style={{ fontWeight: 600, color: 'rgb(var(--foreground))', fontSize: '0.95rem' }}
                >
                  {getItemName(item)}
                </Link>
                <p style={{ fontSize: '0.85rem', color: 'rgb(var(--muted-foreground))', marginTop: '0.25rem' }}>
                  {t('product.sku', 'SKU')}: D-{getItemProductId(item)}
                </p>
                <p style={{ fontWeight: 700, color: 'rgb(var(--primary))', fontSize: '0.95rem', marginTop: '0.5rem' }}>
                  {formatPrice(getItemPrice(item))}
                </p>
              </div>

              {/* Quantity Controls */}
              <div style={{ display: 'flex', alignItems: 'center', border: '1px solid rgb(var(--border))', borderRadius: 'var(--radius)', overflow: 'hidden', height: '34px' }}>
                <button
                  onClick={() => item.quantity <= 1 ? handleRemove(getItemProductId(item)) : handleQtyChange(getItemProductId(item), item.quantity - 1, getItemStock(item))}
                  style={{ width: '28px', height: '100%', background: 'rgb(var(--muted))', cursor: 'pointer', fontWeight: 700 }}
                >
                  -
                </button>
                <span style={{ width: '32px', textAlign: 'center', fontSize: '0.85rem', fontWeight: 600 }}>{item.quantity}</span>
                <button
                  onClick={() => handleQtyChange(getItemProductId(item), item.quantity + 1, getItemStock(item))}
                  style={{ width: '28px', height: '100%', background: 'rgb(var(--muted))', cursor: 'pointer', fontWeight: 700 }}
                >
                  +
                </button>
              </div>

              {/* Delete Icon */}
              <button
                onClick={() => handleRemove(getItemProductId(item))}
                style={{
                  color: 'rgb(var(--danger))',
                  cursor: 'pointer',
                  padding: '0.5rem',
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
                  strokeWidth="2"
                >
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                  <line x1="10" y1="11" x2="10" y2="17" />
                  <line x1="14" y1="11" x2="14" y2="17" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        {/* Right Side: Order Summary & Checkout Form */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div
            style={{
              background: 'rgb(var(--card))',
              border: '1px solid rgb(var(--border))',
              borderRadius: 'var(--radius)',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, borderBottom: '1px solid rgb(var(--border) / 0.5)', paddingBottom: '0.75rem' }}>
              {t('cart.orderSummary', 'Order Summary')}
            </h3>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
              <span style={{ color: 'rgb(var(--muted-foreground))' }}>{t('cart.subtotal', 'Subtotal')}</span>
              <span>{formatPrice(subtotal)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
              <span style={{ color: 'rgb(var(--muted-foreground))' }}>{t('cart.shipping', 'Shipping')}</span>
              <span>{shipping === 0 ? t('cart.freeShipping', 'Free') : formatPrice(shipping)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
              <span style={{ color: 'rgb(var(--muted-foreground))' }}>Estimated Tax (5%)</span>
              <span>{formatPrice(tax)}</span>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontWeight: 700,
                fontSize: '1.1rem',
                borderTop: '1px solid rgb(var(--border) / 0.5)',
                paddingTop: '0.75rem',
                marginTop: '0.25rem',
              }}
            >
              <span>{t('cart.total', 'Total')}</span>
              <span style={{ color: 'rgb(var(--primary))' }}>{formatPrice(total)}</span>
            </div>
          </div>

          {/* Checkout Checkout Form */}
          <form
            onSubmit={handleCheckout}
            style={{
              background: 'rgb(var(--card))',
              border: '1px solid rgb(var(--border))',
              borderRadius: 'var(--radius)',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem',
            }}
          >
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>{t('order.checkoutDetails')}</h3>

            {!isCustomer && (
              <div className="order-access-card">
                {isAuthenticated ? t('order.customersOnly') : t('order.loginCustomer')}
              </div>
            )}

            {checkoutError && <div className="order-error-card">{checkoutError}</div>}

            {/* Payment Method Selector */}
            <div>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>
                {t('order.paymentMethod')}
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="payment"
                    checked={paymentMethod === 'cash_on_delivery'}
                    onChange={() => setPaymentMethod('cash_on_delivery')}
                    disabled={!isCustomer || checkoutLoading}
                  />
                  {t('order.cashOnDelivery')}
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="payment"
                    checked={paymentMethod === 'credit_card'}
                    onChange={() => setPaymentMethod('credit_card')}
                    disabled={!isCustomer || checkoutLoading}
                  />
                  {t('order.creditCard')}
                </label>
              </div>
            </div>

            {isCustomer && (
              <Button type="submit" variant="primary" style={{ width: '100%', height: '42px' }} disabled={checkoutLoading}>
                {checkoutLoading ? t('order.placing') : t('order.placeOrder')}
              </Button>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};
