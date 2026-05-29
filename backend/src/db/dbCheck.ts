import { pool } from "./pool.js";
import { logger } from "../utils/logger.js";

export async function checkDatabaseConnection() {
  const client = await pool.connect();

  try {
    const result = await client.query("SELECT NOW() AS now");
    logger.info({ dbTime: result.rows[0].now }, "PostgreSQL connected");
  } finally {
    client.release();
  }
}