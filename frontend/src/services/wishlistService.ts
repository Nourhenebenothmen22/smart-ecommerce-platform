import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';
import { normalizeProduct } from './productService';

export const wishlistService = {
  async getWishlist(): Promise<any> {
    const items = await apiClient.get<any[]>(API_ENDPOINTS.WISHLIST.BASE);
    return items.map((item) => ({
      ...item,
      product: normalizeProduct({
        id: item.product_id,
        title: item.title,
        price: item.price,
        final_price: item.final_price,
        thumbnail: item.thumbnail,
        stock: item.stock,
        is_active: item.is_active,
        category_name: item.category_name,
        subcategory_name: item.subcategory_name,
      }),
    }));
  },

  async addItem(productId: string): Promise<any> {
    return apiClient.post(API_ENDPOINTS.WISHLIST.BASE, { product_id: Number(productId) });
  },

  async removeItem(productId: string): Promise<any> {
    return apiClient.delete(API_ENDPOINTS.WISHLIST.ITEM(productId));
  },
};
