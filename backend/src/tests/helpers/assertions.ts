import { expect } from "@jest/globals";

type JsonLike = { success?: boolean; message?: string; data?: unknown };

export function assertSuccessResponse(jsonPayload: unknown) {
  const body = jsonPayload as JsonLike;
  expect(body.success).toBe(true);
}

export function assertErrorResponse(jsonPayload: unknown) {
  const body = jsonPayload as JsonLike;
  expect(body.success).toBe(false);
}

export function assertForwardedError(next: jest.Mock, error?: Error) {
  if (error) {
    expect(next).toHaveBeenCalledWith(error);
  } else {
    expect(next).toHaveBeenCalledWith(expect.any(Error));
  }
}

export function assertStatusCalled(statusMock: jest.Mock, expected: number) {
  expect(statusMock).toHaveBeenCalledWith(expected);
}
