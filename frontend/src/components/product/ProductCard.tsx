import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { Product } from '../../data/products';

type ProductCardProps = {
  product: Product;
};

export const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const openProduct = () => {
    navigate(`/product/${product.id}`);
  };

  return (
    <article className="product-card" onClick={openProduct}>
      <div className="product-card-image">
        <img src={product.image} alt={product.name} />
      </div>
      <div className="product-card-body">
        <span>{String(t(`categories.${product.category}`, product.category))}</span>
        <h3>{String(t(product.nameKey, product.name))}</h3>
        <strong>${product.price.toFixed(2)}</strong>
        <button onClick={openProduct}>{t('product.viewProduct')}</button>
      </div>
    </article>
  );
};
