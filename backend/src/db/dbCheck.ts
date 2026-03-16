import { pool } from "./pool.js";

export async function checkDatabaseConnection() {
  const client = await pool.connect();

  try {
    const result = await client.query("SELECT NOW() AS now");
    console.log("PostgreSQL connected at:", result.rows[0].now);
  } finally {
    client.release();
  }
}