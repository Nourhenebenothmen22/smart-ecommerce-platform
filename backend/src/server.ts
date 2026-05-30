import { app } from "./app.js";
import { env } from "./config/env.js";
import { checkDatabaseConnection } from "./db/dbCheck.js";
import { pool } from "./db/pool.js";
import { logger } from "./utils/logger.js";

async function bootstrap() {
  try {
    await checkDatabaseConnection();

    const server = app.listen(env.PORT, env.HOST, () => {
      logger.info(`Server started on http://${env.HOST}:${env.PORT}`);

      const BASE = `http://localhost:${env.PORT}`;
      const NGINX = `http://localhost:8080`;
      console.log(`
╔══════════════════════════════════════════════════════╗
║                 🚀 E-COMMERCE PLATFORM              ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  ── Backend (Express) ──                             ║
║                                                      ║
║  API Base         ${(BASE + '/api').padEnd(40)}║
║  API Docs (Swagger) ${(BASE + '/api/docs').padEnd(36)}║
║  Health Check     ${(BASE + '/api/health').padEnd(40)}║
║  Metrics (Prometheus) ${(BASE + '/api/observability/metrics').padEnd(28)}║
║                                                      ║
║  ── Via Nginx (port 8080) ──                         ║
║                                                      ║
║  API Proxy        ${(NGINX + '/api').padEnd(40)}║
║  Health Proxy     ${(NGINX + '/health').padEnd(40)}║
║  Metrics Proxy    ${(NGINX + '/api/observability/metrics').padEnd(28)}║
║                                                      ║
║  ── Infrastructure (Docker) ──                       ║
║                                                      ║
║  Prometheus       http://localhost:9090${' '.repeat(23)}║
║  Prometheus Alerts http://localhost:9090/alerts${' '.repeat(17)}║
║  Alertmanager     http://localhost:9093${' '.repeat(23)}║
║  Grafana          http://localhost:3000${' '.repeat(23)}║
║  Grafana Dashboards http://localhost:3000/dashboards${' '.repeat(14)}║
║                                                      ║
╚══════════════════════════════════════════════════════╝
      `);
    });

    const shutdown = async (signal: string) => {
      logger.warn({ signal }, `Received ${signal}, shutting down`);
      server.close(async () => {
        logger.info("Express server closed");
        await pool.end();
        logger.info("Database pool closed");
        process.exit(0);
      });
    };

    process.on("SIGINT", () => shutdown("SIGINT"));
    process.on("SIGTERM", () => shutdown("SIGTERM"));

  } catch (error) {
    logger.error({ err: error }, "Application startup failed");
    process.exit(1);
  }
}

bootstrap();