import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useProducts } from '../../hooks/api/useProducts';
import { useCategories } from '../../hooks/api/useCategories';
import { useAddToCart } from '../../hooks/api/useCart';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/Button';
import { SectionLoader } from '../../components/shared/SectionLoader';
import { EmptyState } from '../../components/shared/EmptyState';
import { formatPrice } from '../../lib/utils';

export const ProductListing: React.FC = () => {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // Search filter states synchronized with URL search params
  const categoryFilter = searchParams.get('category') || '';
  const searchQuery = searchParams.get('search') || '';
  const sortBy = searchParams.get('sort') || '';
  const priceMin = searchParams.get('priceMin') || '';
  const priceMax = searchParams.get('priceMax') || '';

  const { data: categories } = useCategories();
  const { data: products, isLoading, refetch } = useProducts({
    category: categoryFilter,
    search: searchQuery,
    sort: sortBy,
    priceMin,
    priceMax,
  });

  const { mutate: addToCart } = useAddToCart();

  const handleCategorySelect = (catId: string) => {
    const nextParams = new URLSearchParams(searchParams);
    if (catId) {
      nextParams.set('category', catId);
    } else {
      nextParams.delete('category');
    }
    setSearchParams(nextParams);
  };

  const handleSortChange = (sortVal: string) => {
    const nextParams = new URLSearchParams(searchParams);
    if (sortVal) {
      nextParams.set('sort', sortVal);
    } else {
      nextParams.delete('sort');
    }
    setSearchParams(nextParams);
  };

  const handleClearFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  const handleAddToCart = (productId: string) => {
    if (!isAuthenticated) {
      window.location.href = '/login';
      return;
    }
    addToCart(
      { productId, quantity: 1 },
      {
        onSuccess: () => {
          alert(t('products.addedToCart', 'Product added to cart successfully!'));
        },
        onError: (err: any) => {
          alert(err.message || 'Could not add product to cart.');
        },
      }
    );
  };

  return (
    <div className="container" style={{ paddingBottom: '4rem', paddingTop: '2rem' }}>
      <div style={{ display: 'flex', gap: '2rem' }}>
        {/* Sidebar Filters */}
        <aside
          style={{
            width: '260px',
            flexShrink: 0,
            background: 'rgb(var(--card))',
            border: '1px solid rgb(var(--border))',
            borderRadius: 'var(--radius)',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem',
            height: 'fit-content',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>{t('products.showFilters', 'Filters')}</h3>
            {(categoryFilter || searchQuery || sortBy || priceMin || priceMax) && (
              <button
                onClick={handleClearFilters}
                style={{ fontSize: '0.75rem', color: 'rgb(var(--primary))', fontWeight: 600, cursor: 'pointer' }}
              >
                Clear
              </button>
            )}
          </div>

          {/* Categories Filter */}
          <div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem' }}>
              {t('products.category', 'Category')}
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <button
                onClick={() => handleCategorySelect('')}
                style={{
                  textAlign: 'left',
                  fontSize: '0.85rem',
                  fontWeight: !categoryFilter ? 700 : 500,
                  color: !categoryFilter ? 'rgb(var(--primary))' : 'rgb(var(--foreground))',
                  cursor: 'pointer',
                }}
              >
                All Categories
              </button>
              {categories?.map((cat: any) => (
                <button
                  key={cat.id}
                  onClick={() => handleCategorySelect(cat.id)}
                  style={{
                    textAlign: 'left',
                    fontSize: '0.85rem',
                    fontWeight: categoryFilter === cat.id ? 700 : 500,
                    color: categoryFilter === cat.id ? 'rgb(var(--primary))' : 'rgb(var(--foreground))',
                    cursor: 'pointer',
                  }}
                >
                  {cat.name}
                </button>
              ))}
            </div>
          </div>

          {/* Price Range Filter */}
          <div>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem' }}>Price Range</h4>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input
                type="number"
                placeholder="Min"
                value={priceMin}
                onChange={(e) => {
                  const nextParams = new URLSearchParams(searchParams);
                  if (e.target.value) nextParams.set('priceMin', e.target.value);
                  else nextParams.delete('priceMin');
                  setSearchParams(nextParams);
                }}
                className="input"
                style={{ padding: '0.35rem', fontSize: '0.75rem' }}
              />
              <span style={{ fontSize: '0.75rem', color: 'rgb(var(--muted-foreground))' }}>-</span>
              <input
                type="number"
                placeholder="Max"
                value={priceMax}
                onChange={(e) => {
                  const nextParams = new URLSearchParams(searchParams);
                  if (e.target.value) nextParams.set('priceMax', e.target.value);
                  else nextParams.delete('priceMax');
                  setSearchParams(nextParams);
                }}
                className="input"
                style={{ padding: '0.35rem', fontSize: '0.75rem' }}
              />
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div style={{ flexGrow: 1 }}>
          {/* Header Controls */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1.5rem',
              gap: '1rem',
            }}
          >
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              {searchQuery
                ? `Results for "${searchQuery}"`
                : categoryFilter
                ? `Category: ${categories?.find((c: any) => c.id === categoryFilter)?.name || 'Loading...'}`
                : t('products.allProducts', 'All Products')}
              <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'rgb(var(--muted-foreground))', marginLeft: '0.5rem' }}>
                ({products?.length || 0} items)
              </span>
            </h2>

            {/* Sorting */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'rgb(var(--muted-foreground))', whiteSpace: 'nowrap' }}>
                {t('products.sortBy', 'Sort By')}:
              </span>
              <select
                value={sortBy}
                onChange={(e) => handleSortChange(e.target.value)}
                className="select"
                style={{ padding: '0.35rem 1.5rem 0.35rem 0.5rem', width: '160px', height: '34px', fontSize: '0.8rem' }}
              >
                <option value="">Default</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="newest">Newest Arrivals</option>
              </select>
            </div>
          </div>

          {/* Product Grid */}
          {isLoading ? (
            <SectionLoader />
          ) : !products || products.length === 0 ? (
            <EmptyState
              title={t('products.noProducts', 'No Products Found')}
              message="No products match your selected filters. Try clearing your filters or search terms."
              actionLabel="Reset Filters"
              onAction={handleClearFilters}
            />
          ) : (
            <div className="grid grid-cols-3">
              {products.map((prod: any) => (
                <div
                  key={prod.id}
                  className="card"
                  style={{
                    height: '100%',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                    e.currentTarget.style.boxShadow = '0 8px 20px rgba(0,0,0,0.06)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.05)';
                  }}
                >
                  <Link
                    to={`/product/${prod.id}`}
                    style={{
                      height: '200px',
                      backgroundColor: 'rgb(var(--muted) / 0.3)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      overflow: 'hidden',
                    }}
                  >
                    {prod.images && prod.images.length > 0 ? (
                      <img
                        src={prod.images[0].startsWith('http') ? prod.images[0] : `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}${prod.images[0]}`}
                        alt={prod.name}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        onError={(e) => { e.currentTarget.style.display = 'none'; }}
                      />
                    ) : (
                      <div style={{ fontSize: '2.5rem', color: 'rgb(var(--muted-foreground))' }}>📦</div>
                    )}
                  </Link>

                  <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '1rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'rgb(var(--muted-foreground))', textTransform: 'uppercase', fontWeight: 600 }}>
                      {prod.category?.name}
                    </span>
                    <Link to={`/product/${prod.id}`}>
                      <h3
                        style={{
                          fontSize: '0.95rem',
                          fontWeight: 600,
                          color: 'rgb(var(--foreground))',
                          height: '2.4rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          lineHeight: '1.2',
                        }}
                      >
                        {prod.name}
                      </h3>
                    </Link>

                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.25rem' }}>
                      <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'rgb(var(--primary))' }}>
                        {formatPrice(prod.price)}
                      </span>
                      {prod.stock === 0 && (
                        <span style={{ fontSize: '0.75rem', color: 'rgb(var(--danger))', fontWeight: 600 }}>
                          {t('products.outOfStock', 'Out of Stock')}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="card-footer" style={{ padding: '1rem', borderTop: '1px solid rgb(var(--border) / 0.3)' }}>
                    <Button
                      onClick={() => handleAddToCart(prod.id)}
                      variant={prod.stock === 0 ? 'secondary' : 'primary'}
                      disabled={prod.stock === 0}
                      style={{ width: '100%' }}
                    >
                      🛒 {t('products.addToCart', 'Add to Cart')}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
