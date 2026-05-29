import { Pool } from "pg";
import { env } from "../config/env.js";
import { logger } from "../utils/logger.js";

export const pool = new Pool({
  connectionString: env.DATABASE_URL,
});

pool.on("error", (err) => {
  logger.error({ err }, "Unexpected PostgreSQL pool error");
});