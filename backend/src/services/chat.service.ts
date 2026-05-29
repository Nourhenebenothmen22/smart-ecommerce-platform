import { env } from "../config/env.js";
import { AppError } from "../utils/AppError.js";
import { StatusCodes } from "http-status-codes";

export interface ChatInput {
  query: string;
  session_id?: string;
}

export interface ChatResult {
  query: string;
  response: string;
  context_used: Array<Record<string, unknown>>;
  algorithm: string;
  session_id: string;
}

export class ChatService {
  async sendMessage(input: ChatInput, userId: number): Promise<ChatResult> {
    if (!env.ML_SERVICE_TOKEN) {
      throw new AppError("ML service token is not configured", StatusCodes.SERVICE_UNAVAILABLE);
    }

    const endpoint = new URL("/chat", env.ML_SERVICE_URL);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), env.ML_REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-ML-Service-Token": env.ML_SERVICE_TOKEN,
          "X-ML-User-Id": String(userId),
        },
        body: JSON.stringify(input),
        signal: controller.signal,
      });

      if (!response.ok) {
        const message = await response.text();
        throw new AppError(
          `Chat service error: ${message || response.statusText}`,
          response.status >= 400 && response.status < 500
            ? StatusCodes.BAD_GATEWAY
            : StatusCodes.SERVICE_UNAVAILABLE
        );
      }

      return (await response.json()) as ChatResult;
    } catch (error) {
      if (error instanceof AppError) {
        throw error;
      }
      if (error instanceof Error && error.name === "AbortError") {
        throw new AppError("Chat service timed out", StatusCodes.GATEWAY_TIMEOUT);
      }
      throw new AppError("Chat service is unavailable", StatusCodes.SERVICE_UNAVAILABLE);
    } finally {
      clearTimeout(timeout);
    }
  }
}

export const chatService = new ChatService();
