export function mockEnvModule(overrides?: Record<string, string | number>) {
  return {
    env: {
      ML_SERVICE_TOKEN: "a".repeat(32),
      ML_SERVICE_URL: "http://127.0.0.1:8000",
      ML_REQUEST_TIMEOUT_MS: 1000,
      NODE_ENV: "test",
      ...overrides,
    },
  };
}
