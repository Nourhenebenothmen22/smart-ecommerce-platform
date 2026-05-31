import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';

export function normalizeUser(user: any): any {
  if (!user) return user;
  return {
    ...user,
    firstName: user.firstName ?? user.first_name ?? '',
    lastName: user.lastName ?? user.last_name ?? '',
    isActive: user.isActive ?? user.is_active,
  };
}

export const userService = {
  async getMe(): Promise<any> {
    return normalizeUser(await apiClient.get(API_ENDPOINTS.USERS.ME));
  },

  async updateMe(data: unknown): Promise<any> {
    return apiClient.patch(API_ENDPOINTS.USERS.ME, data);
  },

  async getAllUsers(): Promise<any> {
    const users = await apiClient.get<any[]>(API_ENDPOINTS.USERS.LIST);
    return users.map(normalizeUser);
  },

  async getUserById(id: string): Promise<any> {
    return normalizeUser(await apiClient.get(API_ENDPOINTS.USERS.BY_ID(id)));
  },

  async updateRole(id: string, role: string): Promise<any> {
    return apiClient.patch(API_ENDPOINTS.USERS.ROLE(id), { role });
  },

  async updateStatus(id: string, isActive: boolean): Promise<any> {
    return apiClient.patch(API_ENDPOINTS.USERS.STATUS(id), { isActive });
  },

  async deleteUser(id: string): Promise<any> {
    return apiClient.delete(API_ENDPOINTS.USERS.BY_ID(id));
  },
};
