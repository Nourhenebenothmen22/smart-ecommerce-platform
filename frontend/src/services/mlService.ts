import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';

export const mlService = {
  async recalculateFeatures(): Promise<any> {
    return apiClient.post(API_ENDPOINTS.ML.RECALCULATE_FEATURES);
  },

  async updateSegments(segments: unknown): Promise<any> {
    return apiClient.post(API_ENDPOINTS.ML.SEGMENTS, segments);
  },

  async registerModel(data: unknown): Promise<any> {
    return apiClient.post(API_ENDPOINTS.ML.MODELS, data);
  },

  async predictPrice(data: unknown): Promise<any> {
    return apiClient.post(API_ENDPOINTS.ML.PRICE_PREDICT, data);
  },
};
