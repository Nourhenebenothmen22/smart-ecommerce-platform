import type { TFunction } from 'i18next';

type TranslatableProduct = {
  id?: string | number;
  name?: string;
  title?: string;
  slug?: string;
  category?: string;
  subcategory?: string;
};

export function toCatalogSlug(value: unknown) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function translateWithFallback(t: TFunction, keys: string[], fallback: string) {
  for (const key of keys) {
    const translated = t(key, { defaultValue: '' });
    if (translated) return String(translated);
  }

  return fallback;
}

export function translateCategoryName(t: TFunction, value: unknown) {
  const label = String(value ?? '');
  const slug = toCatalogSlug(label);

  return translateWithFallback(
    t,
    [`categories.${label}`, `catalog.categories.${slug}`],
    label
  );
}

export function translateSubcategoryName(t: TFunction, value: unknown) {
  const label = String(value ?? '');
  const slug = toCatalogSlug(label);

  return translateWithFallback(
    t,
    [`subcategories.${label}`, `catalog.subcategories.${slug}`],
    label
  );
}

export function translateProductName(t: TFunction, product: TranslatableProduct) {
  const label = String(product.name ?? product.title ?? '');
  const slug = toCatalogSlug(product.slug ?? label);

  return translateWithFallback(
    t,
    [`catalog.productNames.${slug}`, `catalog.products.${product.id}.name`],
    label
  );
}

export function translateProductDescription(t: TFunction, product: TranslatableProduct & { description?: string; descriptionKey?: string }) {
  const label = String(product.description ?? '');
  const slug = toCatalogSlug(product.slug ?? product.name ?? product.title);

  return translateWithFallback(
    t,
    [`catalog.productDescriptions.${slug}`, `catalog.products.${product.id}.description`, String(product.descriptionKey ?? '')].filter(Boolean),
    label
  );
}
