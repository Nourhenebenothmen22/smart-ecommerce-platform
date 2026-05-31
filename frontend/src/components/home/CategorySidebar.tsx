import React, { useState } from 'react';
import { ChevronDown, SlidersHorizontal } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { CategoryGroup } from '../../data/products';

type CategorySidebarProps = {
  categories: CategoryGroup[];
  selectedCategory: string;
  selectedSubcategory: string;
  onSelect: (category: string, subcategory?: string) => void;
};

export const CategorySidebar: React.FC<CategorySidebarProps> = ({
  categories,
  selectedCategory,
  selectedSubcategory,
  onSelect,
}) => {
  const { t } = useTranslation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openCategories, setOpenCategories] = useState<Record<string, boolean>>(
    () => Object.fromEntries(categories.map((category) => [category.name, true]))
  );

  const toggleCategory = (name: string) => {
    setOpenCategories((current) => ({ ...current, [name]: !current[name] }));
  };

  return (
    <aside className={`category-sidebar ${mobileOpen ? 'is-open' : ''}`}>
      <button className="category-mobile-toggle" onClick={() => setMobileOpen((value) => !value)}>
        <SlidersHorizontal size={18} />
        {t('nav.categories')}
      </button>

      <div className="category-panel">
        <button className={!selectedCategory ? 'category-all active' : 'category-all'} onClick={() => onSelect('')}>
          {t('products.allProducts')}
        </button>

        {categories.map((category) => (
          <div key={category.name} className="category-group">
            <button className="category-heading" onClick={() => toggleCategory(category.name)}>
              <span>{String(t(`categories.${category.name}`, category.name))}</span>
              <ChevronDown className={openCategories[category.name] ? 'rotated' : ''} size={18} />
            </button>

            {openCategories[category.name] && (
              <div className="subcategory-list">
                {category.subcategories.map((subcategory) => (
                  <button
                    key={subcategory}
                    className={selectedCategory === category.name && selectedSubcategory === subcategory ? 'active' : ''}
                    onClick={() => onSelect(category.name, subcategory)}
                  >
                    {String(t(`subcategories.${subcategory}`, subcategory))}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </aside>
  );
};
