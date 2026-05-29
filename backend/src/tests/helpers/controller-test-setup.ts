import { jest } from "@jest/globals";
import { Request, Response, NextFunction } from "express";

export interface MockExpress {
  mockRequest: Partial<Request>;
  mockResponse: Partial<Response>;
  mockNext: NextFunction;
  jsonMock: jest.Mock;
  statusMock: jest.Mock;
}

export type UserOverrides = {
  id?: number;
  role?: string;
  email?: string;
};

const DEFAULTS = {
  user: { id: 1, role: "customer", email: "user@example.com" },
};

export function mockResponse() {
  const json = jest.fn<any>();
  const status = jest.fn<any>().mockReturnValue({ json });
  return { status, json } as unknown as Response;
}

export function mockRequest(data: Record<string, unknown> = {}) {
  return data as unknown as Request;
}

export function createMockExpress(overrides?: {
  user?: UserOverrides | null;
}): MockExpress {
  const jsonMock = jest.fn<any>();
  const statusMock = jest.fn<any>().mockReturnValue({ json: jsonMock });
  const mockNext = jest.fn<any>();
  const cookie = jest.fn<any>();
  const clearCookie = jest.fn<any>();

  const user = overrides?.user === null
    ? undefined
    : { ...DEFAULTS.user, ...overrides?.user };

  const mockRequest: Partial<Request> = {
    params: {},
    body: {},
    query: {},
    ...(user ? { user: user as any } : {}),
  };

  const mockResponse: Partial<Response> = {
    status: statusMock as any,
    cookie: cookie as any,
    clearCookie: clearCookie as any,
    json: jsonMock as any,
  };

  return {
    mockRequest,
    mockResponse,
    mockNext,
    jsonMock,
    statusMock,
  };
}
