import apiClient from '../lib/apiClient';
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
  if (params.page) mapped.page = params.page;
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

export const productService = {
  async getAll(params?: Record<string, string>): Promise<{ products: any[]; pagination?: { page: number; limit: number; total: number; totalPages: number } }> {
    const payload = await apiClient.get<any>(API_ENDPOINTS.PRODUCTS.LIST, toBackendParams(params));
    const products = Array.isArray(payload) ? payload : payload?.products ?? [];
    const pagination = payload?.pagination ?? undefined;
    return { products: products.map(normalizeProduct), pagination };
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
