import client from "prom-client";

const register = new client.Registry();

client.collectDefaultMetrics({
  register,
  eventLoopMonitoringPrecision: 1000,
});

const httpRequestsTotal = new client.Counter({
  name: "http_requests_total",
  help: "Total number of HTTP requests",
  labelNames: ["method", "route", "status_code"] as const,
  registers: [register],
});

const httpRequestDurationSeconds = new client.Histogram({
  name: "http_request_duration_seconds",
  help: "HTTP request duration in seconds",
  labelNames: ["method", "route", "status_code"] as const,
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [register],
});

const httpRequestsActive = new client.Gauge({
  name: "http_requests_active",
  help: "Number of HTTP requests currently in progress",
  labelNames: ["method"] as const,
  registers: [register],
});

function normalizeRoute(req: { method?: string; route?: { path?: string }; originalUrl?: string; path?: string }): string {
  const r = req.route?.path || req.originalUrl || req.path || "/unknown";
  return r.replace(/\/\d+/g, "/:id");
}

function recordRequest(req: { method?: string; route?: { path?: string }; originalUrl?: string; path?: string }): (statusCode: number) => void {
  const route = normalizeRoute(req);
  const method = (req.method || "UNKNOWN").toUpperCase();

  httpRequestsActive.inc({ method });

  const endTimer = httpRequestDurationSeconds.startTimer();

  return (statusCode: number) => {
    const labels = { method, route, status_code: String(statusCode) };
    httpRequestsTotal.inc(labels);
    endTimer(labels);
    httpRequestsActive.dec({ method });
  };
}

async function getMetricsContentType(): Promise<string> {
  return register.contentType;
}

async function getMetrics(): Promise<string> {
  return register.metrics();
}

export const metrics = {
  register,
  recordRequest,
  getMetrics,
  getMetricsContentType,
};
