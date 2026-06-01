import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShoppingCart } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Product } from '../../data/products';
import { useAddToCart } from '../../hooks/api/useCart';
import { useAuth } from '../../contexts/AuthContext';
import { translateCategoryName, translateProductName } from '../../lib/catalogTranslations';

type ProductCardProps = {
  product: Product;
};

export const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  const { mutate: addToCart, isPending } = useAddToCart();

  const openProduct = () => {
    navigate(`/product/${product.id}`);
  };

  const productName = translateProductName(t, product);

  const handleAddToCart = (event: React.MouseEvent) => {
    event.stopPropagation();

    if (!isAuthenticated) {
      alert(t('cart.loginToAdd'));
      navigate('/login');
      return;
    }

    if (user?.role !== 'customer') {
      alert(t('cart.customersOnlyCart'));
      return;
    }

    addToCart(
      { productId: product.id, quantity: 1 },
      {
        onError: (error: any) => {
          alert(error.message || t('cart.addError'));
        },
      }
    );
  };

  return (
    <article className="product-card" onClick={openProduct}>
      <div className="product-card-image">
        <img src={product.image} alt={productName} />
        <button
          type="button"
          className="product-card-cart"
          onClick={handleAddToCart}
          disabled={isPending}
          aria-label={t('cart.addItem')}
        >
          <ShoppingCart size={18} />
        </button>
      </div>
      <div className="product-card-body">
        <span>{translateCategoryName(t, product.category)}</span>
        <h3>{productName}</h3>
        <strong>${product.price.toFixed(2)}</strong>
        <button onClick={openProduct}>{t('product.viewProduct')}</button>
      </div>
    </article>
  );
};
