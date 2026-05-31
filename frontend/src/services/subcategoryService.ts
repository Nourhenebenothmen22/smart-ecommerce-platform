import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';

export const subcategoryService = {
  async getAll(): Promise<any> {
    return apiClient.get(API_ENDPOINTS.SUBCATEGORIES.LIST);
  },

  async getById(id: string): Promise<any> {
    return apiClient.get(API_ENDPOINTS.SUBCATEGORIES.BY_ID(id));
  },

  async create(data: unknown): Promise<any> {
    return apiClient.post(API_ENDPOINTS.SUBCATEGORIES.LIST, data);
  },

  async update(id: string, data: unknown): Promise<any> {
    return apiClient.patch(API_ENDPOINTS.SUBCATEGORIES.BY_ID(id), data);
  },

  async delete(id: string): Promise<any> {
    return apiClient.delete(API_ENDPOINTS.SUBCATEGORIES.BY_ID(id));
  },
};
