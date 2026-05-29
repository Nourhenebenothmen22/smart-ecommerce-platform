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
        metrics: `http://localhost:${env.PORT}/api/observability/metrics`,
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