import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';
import { normalizeUser } from './userService';

function unwrapUserResponse(data: any) {
  return normalizeUser(data?.user ?? data);
}

function toBackendAuthPayload(data: any) {
  return {
    ...data,
    first_name: data.first_name ?? data.firstName,
    last_name: data.last_name ?? data.lastName,
  };
}

export const authService = {
  async register(data: unknown): Promise<any> {
    return unwrapUserResponse(await apiClient.post(API_ENDPOINTS.AUTH.REGISTER, toBackendAuthPayload(data)));
  },

  async login(data: unknown): Promise<any> {
    return unwrapUserResponse(await apiClient.post(API_ENDPOINTS.AUTH.LOGIN, data));
  },

  async logout(): Promise<void> {
    return apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
  },

  async registerAdmin(data: unknown): Promise<any> {
    return unwrapUserResponse(await apiClient.post(API_ENDPOINTS.AUTH.REGISTER_ADMIN, toBackendAuthPayload(data)));
  },
};
