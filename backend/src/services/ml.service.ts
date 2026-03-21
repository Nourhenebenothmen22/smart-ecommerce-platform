import { pool } from "../db/pool.js";
import fs from "fs/promises";
import path from "path";


export class MLService {
  /**
   * Recalculates user features by executing the upsert SQL script.
   * This aggregates data from the analytical view and populates the user_features table.
   */
  async recalculateUserFeatures(): Promise<void> {
    const client = await pool.connect();
    try {
      // Path to the upsert SQL file moved to ml/data
      const sqlPath = path.resolve(process.cwd(), "..", "ml", "data", "upsert_user_features.sql");
      const sql = await fs.readFile(sqlPath, "utf-8");

      await client.query("BEGIN");
      await client.query(sql);
      await client.query("COMMIT");
      
      console.log("User features recalculated successfully.");
    } catch (error) {
      await client.query("ROLLBACK");
      console.error("Error recalculating user features:", error);
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Records a new user segmentation result.
   */
  async recordUserSegments(segments: Array<{
    user_id: number;
    segment_id: number;
    segment_label: string;
    model_name: string;
    model_version: string;
    confidence?: number;
  }>): Promise<void> {
    const client = await pool.connect();
    try {
      await client.query("BEGIN");

      const query = `
        INSERT INTO user_segments (
          user_id, segment_id, segment_label, model_name, model_version, confidence, computed_at
        ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
        ON CONFLICT (user_id, model_name, model_version) DO UPDATE SET
          segment_id = EXCLUDED.segment_id,
          segment_label = EXCLUDED.segment_label,
          confidence = EXCLUDED.confidence,
          computed_at = NOW();
      `;

      for (const segment of segments) {
        await client.query(query, [
          segment.user_id,
          segment.segment_id,
          segment.segment_label,
          segment.model_name,
          segment.model_version,
          segment.confidence || null
        ]);
      }

      await client.query("COMMIT");
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Registers or updates ML model metadata.
   */
  async registerModel(modelData: {
    model_name: string;
    model_version: string;
    model_type: string;
    algorithm: string;
    metrics?: object;
    parameters?: object;
    artifact_path?: string;
  }): Promise<void> {
    const query = `
      INSERT INTO ml_models (
        model_name, model_version, model_type, algorithm, metrics, parameters, artifact_path
      ) VALUES ($1, $2, $3, $4, $5, $6, $7)
      ON CONFLICT (model_name, model_version) DO UPDATE SET
        metrics = EXCLUDED.metrics,
        parameters = EXCLUDED.parameters,
        artifact_path = EXCLUDED.artifact_path;
    `;

    await pool.query(query, [
      modelData.model_name,
      modelData.model_version,
      modelData.model_type,
      modelData.algorithm,
      modelData.metrics || {},
      modelData.parameters || {},
      modelData.artifact_path || null
    ]);
  }
}

export const mlService = new MLService();
