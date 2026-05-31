import React from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useProduct } from '../../hooks/api/useProducts';
import { useAddToCart } from '../../hooks/api/useCart';
import { useAuth } from '../../contexts/AuthContext';

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

export const ProductDetails: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const { data: product, isLoading, error } = useProduct(id ?? '');
  const { mutate: addToCart } = useAddToCart();

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
          <button onClick={handleAddToCart}>{t('product.addToCart')}</button>
        </div>
      </div>
    </section>
  );
};
