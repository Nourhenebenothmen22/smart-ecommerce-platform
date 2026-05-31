export const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5000';

export const API_ENDPOINTS = {
  AUTH: {
    REGISTER: '/api/auth/register',
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    REGISTER_ADMIN: '/api/auth/register-admin',
  },
  USERS: {
    ME: '/api/users/me',
    LIST: '/api/users',
    BY_ID: (id: string) => `/api/users/${id}`,
    ROLE: (id: string) => `/api/users/${id}/role`,
    STATUS: (id: string) => `/api/users/${id}/status`,
  },
  PRODUCTS: {
    LIST: '/api/products',
    BY_ID: (id: string) => `/api/products/${id}`,
    REVIEWS: (productId: string) => `/api/products/${productId}/reviews`,
  },
  CATEGORIES: {
    LIST: '/api/categories',
    BY_ID: (id: string) => `/api/categories/${id}`,
    SUBCATEGORIES: (categoryId: string) => `/api/categories/${categoryId}/subcategories`,
  },
  SUBCATEGORIES: {
    LIST: '/api/subcategories',
    BY_ID: (id: string) => `/api/subcategories/${id}`,
  },
  ORDERS: {
    LIST: '/api/orders',
    MY: '/api/orders/my',
    BY_ID: (id: string) => `/api/orders/${id}`,
    STATUS: (id: string) => `/api/orders/${id}/status`,
  },
  REVIEWS: {
    LIST: '/api/reviews',
    BY_PRODUCT: (id: string) => `/api/reviews/product/${id}`,
    BY_ID: (id: string) => `/api/reviews/${id}`,
  },
  CART: {
    BASE: '/api/cart',
    ITEM: (productId: string) => `/api/cart/${productId}`,
  },
  WISHLIST: {
    BASE: '/api/wishlist',
    ITEM: (productId: string) => `/api/wishlist/${productId}`,
  },
  CHAT: {
    BASE: '/api/chat',
  },
  ML: {
    RECALCULATE_FEATURES: '/api/ml/recalculate-features',
    SEGMENTS: '/api/ml/segments',
    MODELS: '/api/ml/models',
    PRICE_PREDICT: '/api/ml/price/predict',
  },
  VOICE: {
    INITIATE: (id: string) => `/api/voice/initiate/${id}`,
    CONTEXT: (id: string) => `/api/voice/context/${id}`,
  },
} as const;
