import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CategorySidebar } from '../../components/home/CategorySidebar';
import { ProductCard } from '../../components/product/ProductCard';
import type { CategoryGroup, Product } from '../../data/products';
import { useCategories } from '../../hooks/api/useCategories';
import { useProducts } from '../../hooks/api/useProducts';
import { useSubcategories } from '../../hooks/api/useSubcategories';

type ApiCategory = {
  id: string | number;
  name: string;
};

type ApiSubcategory = {
  category_id: string | number;
  name: string;
};

export const Home: React.FC = () => {
  const { t } = useTranslation();
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSubcategory, setSelectedSubcategory] = useState('');
  const { data: apiProducts = [], isLoading: productsLoading, error: productsError } = useProducts();
  const { data: apiCategories = [] } = useCategories();
  const { data: apiSubcategories = [] } = useSubcategories();

  const categories = useMemo<CategoryGroup[]>(() => {
    return (apiCategories as ApiCategory[]).map((category) => ({
      name: category.name,
      subcategories: (apiSubcategories as ApiSubcategory[])
        .filter((subcategory) => String(subcategory.category_id) === String(category.id))
        .map((subcategory) => subcategory.name),
    }));
  }, [apiCategories, apiSubcategories]);

  const visibleProducts = useMemo(() => {
    const products = apiProducts as Product[];
    if (!selectedCategory) return products;

    return products.filter((product) => {
      const categoryMatch = product.category === selectedCategory;
      const subcategoryMatch = selectedSubcategory ? product.subcategory === selectedSubcategory : true;
      return categoryMatch && subcategoryMatch;
    });
  }, [apiProducts, selectedCategory, selectedSubcategory]);

  const handleSelectCategory = (category: string, subcategory = '') => {
    setSelectedCategory(category);
    setSelectedSubcategory(subcategory);
  };

  return (
    <section className="home-page">
      <CategorySidebar
        categories={categories}
        selectedCategory={selectedCategory}
        selectedSubcategory={selectedSubcategory}
        onSelect={handleSelectCategory}
      />

      <div className="home-products">
        <div className="section-heading">
          <span>{t('home.collection')}</span>
          <h2>{selectedSubcategory ? String(t(`subcategories.${selectedSubcategory}`, selectedSubcategory)) : selectedCategory ? String(t(`categories.${selectedCategory}`, selectedCategory)) : t('home.featuredProducts')}</h2>
          <p>{t('home.collectionSubtitle')}</p>
        </div>

        {productsLoading ? (
          <div className="not-found-panel">{t('common.loading', 'Loading...')}</div>
        ) : productsError ? (
          <div className="not-found-panel">{(productsError as Error).message}</div>
        ) : visibleProducts.length > 0 ? (
          <div className="product-grid">
            {visibleProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : (
          <div className="not-found-panel">{t('products.noProducts')}</div>
        )}
      </div>
    </section>
  );
};
