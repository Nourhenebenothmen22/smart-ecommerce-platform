import { Response } from "express";

interface ApiResponse {
  success: boolean;
  message: string;
  data?: any;
  errors?: any;
}

/**
 * Standardized API Response Utility
 */
export const sendResponse = (
  res: Response,
  statusCode: number,
  message: string,
  data: any = null,
  errors: any = null
) => {
  const response: ApiResponse = {
    success: statusCode >= 200 && statusCode < 300,
    message,
    data,
    errors,
  };
  return res.status(statusCode).json(response);
};
