import apiClient, { ApiError } from '../lib/apiClient';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';

function parseImages(value: any): string[] {
  if (Array.isArray(value)) return value;
  if (!value) return [];
  if (typeof value !== 'string') return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return value.split(',').map((item) => item.trim()).filter(Boolean);
  }
}

function resolveImageUrl(value: unknown): string {
  if (typeof value !== 'string' || !value) return '/hero/hero1.png';
  if (value.startsWith('http') || value.startsWith('/hero/')) return value;
  return `${API_BASE_URL}${value}`;
}

export function normalizeProduct(product: any): any {
  if (!product) return product;
  const images = parseImages(product.images);
  const image = resolveImageUrl(images[0] ?? product.thumbnail);
  const category = product.category?.name ?? product.category_name ?? product.category ?? '';
  const subcategory = product.subcategory?.name ?? product.subcategory_name ?? product.subcategory ?? '';
  const name = product.name ?? product.title ?? '';
  const description = product.description ?? '';

  return {
    ...product,
    id: String(product.id),
    name,
    title: product.title ?? product.name ?? '',
    categoryId: product.categoryId ?? product.category_id,
    subcategoryId: product.subcategoryId ?? product.subcategory_id,
    category,
    subcategory,
    categoryName: category,
    subcategoryName: subcategory,
    category_name: product.category_name ?? category,
    subcategory_name: product.subcategory_name ?? subcategory,
    price: Number(product.final_price ?? product.price ?? 0),
    images: images.length ? images : (product.thumbnail ? [product.thumbnail] : []),
    image,
    nameKey: name,
    description,
    descriptionKey: description,
    createdAt: product.createdAt ?? product.created_at,
  };
}

function toBackendParams(params?: Record<string, string>): Record<string, string> | undefined {
  if (!params) return undefined;
  const mapped: Record<string, string> = {};
  if (params.search) mapped.search = params.search;
  if (params.category) mapped.category_id = params.category;
  if (params.subcategory) mapped.subcategory_id = params.subcategory;
  if (params.priceMin) mapped.min_price = params.priceMin;
  if (params.priceMax) mapped.max_price = params.priceMax;
  if (params.limit) mapped.limit = params.limit;
  if (params.sort === 'price_asc') {
    mapped.sort_by = 'price';
    mapped.sort_order = 'asc';
  } else if (params.sort === 'price_desc') {
    mapped.sort_by = 'price';
    mapped.sort_order = 'desc';
  } else if (params.sort === 'newest') {
    mapped.sort_by = 'created_at';
    mapped.sort_order = 'desc';
  }
  return mapped;
}

function applyClientFilters(products: any[], params?: Record<string, string>) {
  let result = products;

  if (params?.search) {
    const search = params.search.toLowerCase();
    result = result.filter((product) =>
      `${product.name} ${product.title} ${product.brand}`.toLowerCase().includes(search)
    );
  }

  if (params?.category) {
    result = result.filter((product) => String(product.categoryId) === String(params.category));
  }

  if (params?.subcategory) {
    result = result.filter((product) => String(product.subcategoryId) === String(params.subcategory));
  }

  if (params?.priceMin) {
    result = result.filter((product) => product.price >= Number(params.priceMin));
  }

  if (params?.priceMax) {
    result = result.filter((product) => product.price <= Number(params.priceMax));
  }

  if (params?.sort === 'price_asc') {
    result = [...result].sort((a, b) => a.price - b.price);
  } else if (params?.sort === 'price_desc') {
    result = [...result].sort((a, b) => b.price - a.price);
  } else if (params?.sort === 'newest') {
    result = [...result].sort((a, b) => Date.parse(b.createdAt ?? '') - Date.parse(a.createdAt ?? ''));
  }

  return result;
}

async function getProductsFromDetailFallback(params?: Record<string, string>) {
  const limit = Number(params?.limit ?? 24);
  const ids = Array.from({ length: limit }, (_, index) => String(index + 1));
  const settled = await Promise.allSettled(
    ids.map((id) => apiClient.get(API_ENDPOINTS.PRODUCTS.BY_ID(id)))
  );
  const products = settled
    .filter((result): result is PromiseFulfilledResult<any> => result.status === 'fulfilled')
    .map((result) => normalizeProduct(result.value))
    .filter((product) => product?.is_active !== false);

  return applyClientFilters(products, params);
}

export const productService = {
  async getAll(params?: Record<string, string>): Promise<any> {
    try {
      const payload = await apiClient.get<any>(API_ENDPOINTS.PRODUCTS.LIST, toBackendParams(params));
      const products = Array.isArray(payload) ? payload : payload?.products ?? [];
      return products.map(normalizeProduct);
    } catch (error) {
      if (error instanceof ApiError && error.status >= 500) {
        return getProductsFromDetailFallback(params);
      }
      throw error;
    }
  },

  async getById(id: string): Promise<any> {
    return normalizeProduct(await apiClient.get(API_ENDPOINTS.PRODUCTS.BY_ID(id)));
  },

  async create(formData: FormData): Promise<any> {
    return apiClient.post(API_ENDPOINTS.PRODUCTS.LIST, formData);
  },

  async update(id: string, formData: FormData): Promise<any> {
    return apiClient.patch(API_ENDPOINTS.PRODUCTS.BY_ID(id), formData);
  },

  async delete(id: string): Promise<any> {
    return apiClient.delete(API_ENDPOINTS.PRODUCTS.BY_ID(id));
  },

  async getProductReviews(productId: string): Promise<any> {
    return apiClient.get(API_ENDPOINTS.PRODUCTS.REVIEWS(productId));
  },
};
