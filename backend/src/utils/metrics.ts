let totalRequests = 0;
let activeRequests = 0;

function recordRequest(_req: { method?: string; route?: { path?: string }; originalUrl?: string; path?: string }): (statusCode: number) => void {
  totalRequests++;
  activeRequests++;

  return (_statusCode: number) => {
    activeRequests = Math.max(0, activeRequests - 1);
  };
}

async function getMetricsContentType(): Promise<string> {
  return "text/plain; version=0.0.4; charset=utf-8";
}

async function getMetrics(): Promise<string> {
  const uptime = process.uptime();
  const mem = process.memoryUsage();
  return [
    "# HELP app_uptime_seconds Application uptime in seconds",
    "# TYPE app_uptime_seconds gauge",
    `app_uptime_seconds ${uptime.toFixed(2)}`,
    "# HELP http_requests_total Total number of HTTP requests",
    "# TYPE http_requests_total counter",
    `http_requests_total ${totalRequests}`,
    "# HELP http_requests_active Number of active HTTP requests",
    "# TYPE http_requests_active gauge",
    `http_requests_active ${activeRequests}`,
    "# HELP process_resident_memory_bytes Resident memory size in bytes",
    "# TYPE process_resident_memory_bytes gauge",
    `process_resident_memory_bytes ${mem.rss}`,
  ].join("\n") + "\n";
}

export const metrics = {
  recordRequest,
  getMetrics,
  getMetricsContentType,
};
