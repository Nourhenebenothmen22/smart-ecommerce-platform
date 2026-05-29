import { jest } from "@jest/globals";

export function createMockPoolQuery() {
  return jest.fn<any>();
}

export function createMockPoolClient() {
  return {
    query: jest.fn<any>(),
    release: jest.fn<any>(),
  };
}

export function mockPoolModule() {
  return {
    pool: {
      connect: jest.fn<any>().mockResolvedValue(createMockPoolClient()),
      query: jest.fn<any>(),
    },
  };
}

export function mockPoolSimple() {
  return {
    pool: {
      query: jest.fn<any>(),
    },
  };
}
