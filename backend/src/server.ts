import { app } from "./app.js";
import { env } from "./config/env.js";
import { checkDatabaseConnection } from "./db/dbCheck.js";

async function bootstrap() {
  try {
    await checkDatabaseConnection();

    app.listen(env.PORT, () => {
      console.log(`Server running on http://localhost:${env.PORT}`);
    });
  } catch (error) {
    console.error("Application startup failed:", error);
    process.exit(1);
  }
}

bootstrap();