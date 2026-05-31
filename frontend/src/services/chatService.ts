import apiClient from '../lib/apiClient';
import { API_ENDPOINTS } from '../config/api';

export type ChatbotResponse = {
  query: string;
  response: string;
  context_used: Array<Record<string, unknown>>;
  algorithm: string;
  session_id: string;
};

export const chatService = {
  async sendMessage(query: string, sessionId?: string): Promise<ChatbotResponse> {
    return apiClient.post(API_ENDPOINTS.CHAT.BASE, {
      query,
      ...(sessionId ? { session_id: sessionId } : {}),
    });
  },
};
