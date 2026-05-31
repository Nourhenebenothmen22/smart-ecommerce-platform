import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';

export const cartService = {
  async getCart(): Promise<any> {
    return apiClient.get(API_ENDPOINTS.CART.BASE);
  },

  async addItem(productId: string, quantity: number): Promise<any> {
    return apiClient.post(API_ENDPOINTS.CART.BASE, { product_id: Number(productId), quantity });
  },

  async updateItem(productId: string, quantity: number): Promise<any> {
    return apiClient.patch(API_ENDPOINTS.CART.ITEM(productId), { quantity });
  },

  async removeItem(productId: string): Promise<any> {
    return apiClient.delete(API_ENDPOINTS.CART.ITEM(productId));
  },
};
