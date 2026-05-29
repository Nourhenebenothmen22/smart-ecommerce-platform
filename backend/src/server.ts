import { app } from "./app.js";
import { env } from "./config/env.js";
import { checkDatabaseConnection } from "./db/dbCheck.js";
import { pool } from "./db/pool.js";
import { logger } from "./utils/logger.js";

async function bootstrap() {
  try {
    await checkDatabaseConnection();

    const server = app.listen(env.PORT, env.HOST, () => {
      logger.info({
        port: env.PORT,
        host: env.HOST,
        env: env.NODE_ENV,
        swagger: `http://localhost:${env.PORT}/api/docs`,
        api: `http://localhost:${env.PORT}/api`,
        prometheus: `http://localhost:9090`,
        grafana: `http://localhost:3000`,
        alertmanager: `http://localhost:9093`,
        alertRules: `http://localhost:9090/alerts`,
        grafanaDashboards: `http://localhost:3000/dashboards`,
      }, `Server started on http://${env.HOST}:${env.PORT}`);
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