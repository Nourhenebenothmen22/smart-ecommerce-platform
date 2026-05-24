import { pool } from "../db/pool.js";
import fs from "fs/promises";
import { existsSync } from "fs";
import path from "path";
import { StatusCodes } from "http-status-codes";
import { env } from "../config/env.js";
import { AppError } from "../utils/AppError.js";

function resolveUserFeaturesSqlPath(): string {
  const candidates = [
    path.resolve(process.cwd(), "..", "ml", "data", "sql", "upsert_user_features.sql"),
    path.resolve(process.cwd(), "ml", "data", "sql", "upsert_user_features.sql"),
  ];

  const found = candidates.find((candidate) => existsSync(candidate));
  return found ?? candidates[0];
}

export interface PricePredictionInput {
  product_id?: number;
  title?: string;
  description?: string;
  brand?: string;
  category_id?: number;
  subcategory_id?: number;
  category_name?: string;
  subcategory_name?: string;
  discount_percent?: number;
  rating_avg?: number;
  review_count?: number;
  stock?: number;
  tags?: string[];
  is_active?: boolean;
}

export interface PricePredictionResult {
  product_id?: number | null;
  predicted_price: number;
  currency: string;
  model_name: string;
  model_version: string;
  model_algorithm: string;
  metrics?: Record<string, unknown>;
  features_used?: string[];
}

export class MLService {
  /**
   * Recalculates user features by executing the upsert SQL script.
   * This aggregates data from the analytical view and populates the user_features table.
   */
  async recalculateUserFeatures(): Promise<void> {
    const client = await pool.connect();
    try {
      // Resolve from backend or repository root working directories.
      const sqlPath = resolveUserFeaturesSqlPath();
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
          segment.confidence ?? null
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
        model_name, model_version, model_type, algorithm, metrics, parameters, artifact_path, is_active, trained_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, true, NOW())
      ON CONFLICT (model_name, model_version) DO UPDATE SET
        model_type = EXCLUDED.model_type,
        algorithm = EXCLUDED.algorithm,
        metrics = EXCLUDED.metrics,
        parameters = EXCLUDED.parameters,
        artifact_path = EXCLUDED.artifact_path,
        is_active = true,
        trained_at = NOW();
    `;

    await pool.query(query, [
      modelData.model_name,
      modelData.model_version,
      modelData.model_type,
      modelData.algorithm,
      modelData.metrics ?? {},
      modelData.parameters ?? {},
      modelData.artifact_path ?? null
    ]);
  }

  /**
   * Calls the trusted FastAPI ML service for product price prediction and stores
   * the result for traceability.
   */
  async predictProductPrice(input: PricePredictionInput): Promise<PricePredictionResult> {
    if (!env.ML_SERVICE_TOKEN) {
      throw new AppError("ML service token is not configured", StatusCodes.SERVICE_UNAVAILABLE);
    }

    const endpoint = new URL("/price/predict", env.ML_SERVICE_URL);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), env.ML_REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-ML-Service-Token": env.ML_SERVICE_TOKEN,
        },
        body: JSON.stringify(input),
        signal: controller.signal,
      });

      if (!response.ok) {
        const message = await response.text();
        throw new AppError(
          `ML price prediction failed: ${message || response.statusText}`,
          response.status >= 400 && response.status < 500
            ? StatusCodes.BAD_GATEWAY
            : StatusCodes.SERVICE_UNAVAILABLE
        );
      }

      const result = (await response.json()) as PricePredictionResult;
      await this.recordPricePrediction(input, result);
      return result;
    } catch (error) {
      if (error instanceof AppError) {
        throw error;
      }
      if (error instanceof Error && error.name === "AbortError") {
        throw new AppError("ML price prediction timed out", StatusCodes.GATEWAY_TIMEOUT);
      }
      throw new AppError("ML price prediction service is unavailable", StatusCodes.SERVICE_UNAVAILABLE);
    } finally {
      clearTimeout(timeout);
    }
  }

  async recordPricePrediction(input: PricePredictionInput, result: PricePredictionResult): Promise<void> {
    const productId = result.product_id ?? input.product_id ?? null;
    await pool.query(
      `
      INSERT INTO product_price_predictions (
        product_id, predicted_price, currency, model_name, model_version, input_features, metrics_snapshot, created_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
      `,
      [
        productId,
        result.predicted_price,
        result.currency,
        result.model_name,
        result.model_version,
        input,
        result.metrics ?? {},
      ]
    );
  }
}

export const mlService = new MLService();
