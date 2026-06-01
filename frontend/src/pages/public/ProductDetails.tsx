import React, { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useProduct } from '../../hooks/api/useProducts';
import { useAddToCart } from '../../hooks/api/useCart';
import { useCreateOrder } from '../../hooks/api/useOrders';
import { useAuth } from '../../contexts/AuthContext';
import ReviewSection from '../../components/reviews/ReviewSection';

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

export const ProductDetails: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  const { data: product, isLoading, error } = useProduct(id ?? '');
  const { mutate: addToCart } = useAddToCart();
  const { mutate: createOrder } = useCreateOrder();
  const [orderMessage, setOrderMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [orderLoading, setOrderLoading] = useState(false);

  const isCustomer = user?.role === 'customer';

  const handleAddToCart = () => {
    if (!product) return;
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    addToCart(
      { productId: product.id, quantity: 1 },
      {
        onSuccess: () => {
          alert(t('products.addedToCart', 'Product added to cart successfully!'));
        },
        onError: (err: unknown) => {
          alert(getErrorMessage(err, 'Could not add product to cart.'));
        },
      }
    );
  };

  const handlePlaceOrder = () => {
    if (!product || !isCustomer || orderLoading) return;

    setOrderMessage(null);
    setOrderLoading(true);
    createOrder(
      {
        items: [{ product_id: Number(product.id), quantity: 1 }],
        payment_method: 'cash_on_delivery',
      },
      {
        onSuccess: () => {
          setOrderMessage({ type: 'success', text: t('order.success') });
          navigate('/customer');
        },
        onError: (err: unknown) => {
          setOrderMessage({ type: 'error', text: getErrorMessage(err, t('order.error')) });
        },
        onSettled: () => {
          setOrderLoading(false);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <section className="product-details-page">
        <div className="not-found-panel">{t('common.loading', 'Loading...')}</div>
      </section>
    );
  }

  if (!product) {
    return (
      <section className="product-details-page">
        <div className="not-found-panel">
          <h1>{error ? (error as Error).message : t('product.notFound')}</h1>
          <Link to="/">{t('common.back')}</Link>
        </div>
      </section>
    );
  }

  return (
    <section className="product-details-page">
      <div className="product-details-card">
        <div className="product-details-image">
          <img src={product.image} alt={product.name} />
        </div>

        <div className="product-details-content">
          <span>{t('products.category')}: {String(t(`categories.${product.category}`, product.category))} / {String(t(`subcategories.${product.subcategory}`, product.subcategory))}</span>
          <h1>{String(t(product.nameKey, product.name))}</h1>
          <strong>${product.price.toFixed(2)}</strong>
          <p><b>{t('product.description')}:</b> {String(t(product.descriptionKey, product.description))}</p>
          <div className="product-order-actions">
            <button onClick={handleAddToCart}>{t('product.addToCart')}</button>
            {isAuthenticated && isCustomer && (
              <button onClick={handlePlaceOrder} disabled={orderLoading}>
                {orderLoading ? t('order.placing') : t('order.placeOrder')}
              </button>
            )}
          </div>
          {!isAuthenticated && <p className="order-access-message">{t('order.loginCustomer')}</p>}
          {isAuthenticated && !isCustomer && <p className="order-access-message">{t('order.customersOnly')}</p>}
          {orderMessage && <p className={`order-status-message ${orderMessage.type}`}>{orderMessage.text}</p>}
        </div>
      </div>

      <ReviewSection productId={id ?? ''} />
    </section>
  );
};
