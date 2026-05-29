import { Router, Request, Response } from "express";
import { metrics } from "../utils/metrics.js";
import { pool } from "../db/pool.js";

const router = Router();

router.get("/health", async (_req: Request, res: Response) => {
  let dbStatus = "disconnected";
  let dbPoolStats: Record<string, number> = {};

  try {
    const client = await pool.connect();
    await client.query("SELECT 1");
    client.release();
    dbStatus = "connected";

    dbPoolStats = {
      total: pool.totalCount,
      idle: pool.idleCount,
      waiting: pool.waitingCount,
    };
  } catch {
    dbStatus = "error";
  }

  res.status(dbStatus === "connected" ? 200 : 503).json({
    status: dbStatus === "connected" ? "healthy" : "unhealthy",
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    database: dbStatus,
    pool: dbPoolStats,
  });
});

router.get("/metrics", async (_req: Request, res: Response) => {
  try {
    const contentType = await metrics.getMetricsContentType();
    const data = await metrics.getMetrics();
    res.setHeader("Content-Type", contentType);
    res.end(data);
  } catch (err) {
    res.status(500).json({
      success: false,
      message: "Failed to collect metrics",
    });
  }
});

export { router as observabilityRouter };
