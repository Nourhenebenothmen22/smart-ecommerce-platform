import { app } from "./app.js";
import { env } from "./config/env.js";
import { checkDatabaseConnection } from "./db/dbCheck.js";
import { pool } from "./db/pool.js";

async function bootstrap() {
  try {
    // 1. Check and establish DB connection
    await checkDatabaseConnection();

    // 2. Start Express server
    const server = app.listen(env.PORT, () => {
      console.log(`🚀 Server running on http://localhost:${env.PORT}`);
      console.log(`📚 Swagger docs available at http://localhost:${env.PORT}/api/docs`);
      console.log(`🌍 Environment: ${env.NODE_ENV}`);
      console.log(`🔗 API base URL: http://localhost:${env.PORT}/api`);
    });

    // 3. Graceful Shutdown handlers
    const shutdown = async (signal: string) => {
      console.log(`\n🛑 Received ${signal}. Closing server and database pool...`);
      server.close(async () => {
        console.log("✔ Express server closed.");
        await pool.end();
        console.log("✔ Database pool closed.");
        process.exit(0);
      });
    };

    process.on("SIGINT", () => shutdown("SIGINT"));
    process.on("SIGTERM", () => shutdown("SIGTERM"));

  } catch (error) {
    console.error("❌ Application startup failed:", error);
    process.exit(1);
  }
}

bootstrap();