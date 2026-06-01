import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';

export const reviewService = {
  async getAll(): Promise<any> {
    return apiClient.get(API_ENDPOINTS.REVIEWS.LIST);
  },

  async getByProduct(productId: string): Promise<any> {
    const payload = await apiClient.get<any>(API_ENDPOINTS.REVIEWS.BY_PRODUCT(productId));
    return Array.isArray(payload) ? payload : payload?.reviews ?? [];
  },

  async create(data: unknown): Promise<any> {
    return apiClient.post(API_ENDPOINTS.REVIEWS.LIST, data);
  },

  async update(id: string, data: unknown): Promise<any> {
    return apiClient.patch(API_ENDPOINTS.REVIEWS.BY_ID(id), data);
  },

  async delete(id: string): Promise<any> {
    return apiClient.delete(API_ENDPOINTS.REVIEWS.BY_ID(id));
  },
};
