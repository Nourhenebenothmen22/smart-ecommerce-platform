import axios, { AxiosError, type AxiosRequestConfig } from 'axios';
import { API_BASE_URL } from '../config/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export class ApiError extends Error {
  status: number;
  errors: unknown;

  constructor(status: number, message: string, errors?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errors = errors;
  }
}

interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
  errors?: unknown;
}

function getValidationMessage(errors: unknown) {
  if (!Array.isArray(errors)) return '';
  return errors
    .map((error) => {
      if (error && typeof error === 'object' && 'message' in error) {
        return String(error.message);
      }
      return '';
    })
    .filter(Boolean)
    .join(' ');
}

function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;

  if (error instanceof AxiosError) {
    const status = error.response?.status ?? 0;
    const body = error.response?.data as Partial<ApiResponse> | undefined;
    const message =
      getValidationMessage(body?.errors) ||
      body?.message ||
      error.message ||
      'An unexpected error occurred.';

    if (status === 401) {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    }

    if (status === 403) {
      window.dispatchEvent(new CustomEvent('auth:forbidden'));
    }

    return new ApiError(status, message, body?.errors);
  }

  return new ApiError(0, 'Network error. Please check your connection.');
}

class ApiClient {
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const requestConfig = { ...config };
      if (requestConfig.data instanceof FormData) {
        const headers = { ...(requestConfig.headers as Record<string, string>) };
        delete headers['Content-Type'];
        requestConfig.headers = headers;
      }

      const response = await api.request<ApiResponse<T>>(requestConfig);
      const body = response.data;

      if (!body?.success) {
        throw new ApiError(
          response.status,
          getValidationMessage(body?.errors) || body?.message || 'An unexpected error occurred.',
          body?.errors
        );
      }

      return body.data as T;
    } catch (error) {
      throw toApiError(error);
    }
  }

  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    return this.request<T>({
      method: 'GET',
      url: endpoint,
      params,
    });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>({
      method: 'POST',
      url: endpoint,
      data,
    });
  }

  async patch<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>({
      method: 'PATCH',
      url: endpoint,
      data,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>({
      method: 'DELETE',
      url: endpoint,
    });
  }
}

const apiClient = new ApiClient();

export default apiClient;
