import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';

export const orderService = {
  async create(data: unknown): Promise<any> {
    return apiClient.post(API_ENDPOINTS.ORDERS.LIST, data);
  },

  async getMyOrders(): Promise<any> {
    return apiClient.get(API_ENDPOINTS.ORDERS.MY);
  },

  async getAll(): Promise<any> {
    return apiClient.get(API_ENDPOINTS.ORDERS.LIST);
  },

  async getById(id: string): Promise<any> {
    return apiClient.get(API_ENDPOINTS.ORDERS.BY_ID(id));
  },

  async updateStatus(id: string, status: string): Promise<any> {
    return apiClient.patch(API_ENDPOINTS.ORDERS.STATUS(id), { status });
  },

  async delete(id: string): Promise<any> {
    return apiClient.delete(API_ENDPOINTS.ORDERS.BY_ID(id));
  },
};
