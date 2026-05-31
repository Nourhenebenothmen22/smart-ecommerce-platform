import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';

export const voiceService = {
  async initiateCall(orderId: string): Promise<any> {
    return apiClient.post(API_ENDPOINTS.VOICE.INITIATE(orderId));
  },

  async getContext(orderId: string): Promise<any> {
    return apiClient.get(API_ENDPOINTS.VOICE.CONTEXT(orderId));
  },
};
