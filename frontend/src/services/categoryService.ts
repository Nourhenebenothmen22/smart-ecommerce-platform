import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';

export const categoryService = {
  async getAll(): Promise<any> {
    return apiClient.get(API_ENDPOINTS.CATEGORIES.LIST);
  },

  async getById(id: string): Promise<any> {
    return apiClient.get(API_ENDPOINTS.CATEGORIES.BY_ID(id));
  },

  async getSubcategories(categoryId: string): Promise<any> {
    return apiClient.get(API_ENDPOINTS.CATEGORIES.SUBCATEGORIES(categoryId));
  },

  async create(data: unknown): Promise<any> {
    return apiClient.post(API_ENDPOINTS.CATEGORIES.LIST, data);
  },

  async update(id: string, data: unknown): Promise<any> {
    return apiClient.patch(API_ENDPOINTS.CATEGORIES.BY_ID(id), data);
  },

  async delete(id: string): Promise<any> {
    return apiClient.delete(API_ENDPOINTS.CATEGORIES.BY_ID(id));
  },
};
