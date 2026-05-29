import { Request, Response, NextFunction } from "express";
import { StatusCodes } from "http-status-codes";
import { z } from "zod";
import { chatService } from "../services/chat.service.js";
import { sendResponse } from "../utils/apiResponse.js";

const chatRequestSchema = z.object({
  query: z.string().trim().min(1, "Query is required").max(500, "Query must be at most 500 characters"),
  session_id: z.string().trim().min(1).max(100).optional(),
});

export class ChatController {
  async sendMessage(req: Request, res: Response, next: NextFunction) {
    const parsed = chatRequestSchema.safeParse(req.body);

    if (!parsed.success) {
      return sendResponse(res, StatusCodes.BAD_REQUEST, "Validation failed", null, parsed.error.flatten().fieldErrors);
    }

    try {
      const result = await chatService.sendMessage(parsed.data, req.user!.id);
      sendResponse(res, StatusCodes.OK, "Message processed successfully", result);
    } catch (error: unknown) {
      next(error);
    }
  }
}

export const chatController = new ChatController();
