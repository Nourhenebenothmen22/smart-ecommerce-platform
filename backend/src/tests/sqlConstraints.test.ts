import fs from "fs";
import path from "path";

const sqlDir = path.resolve(process.cwd(), "src", "sql");

describe("SQL constraint alignment", () => {
  test("order status constraint includes service-managed phone statuses", () => {
    const sql = fs.readFileSync(path.join(sqlDir, "002_constraints.sql"), "utf-8");

    expect(sql).toContain("pending_phone_confirmation");
    expect(sql).toContain("manual_review");
  });

  test("interaction constraint allows review interactions logged by ReviewService", () => {
    const sql = fs.readFileSync(path.join(sqlDir, "002_constraints.sql"), "utf-8");

    expect(sql).toContain("'review'");
  });

  test("voice confirmations use partial active-call uniqueness instead of one row per order", () => {
    const baseConstraints = fs.readFileSync(path.join(sqlDir, "002_constraints.sql"), "utf-8");
    const voiceExtension = fs.readFileSync(path.join(sqlDir, "012_voice_confirmations_extend.sql"), "utf-8");

    expect(baseConstraints).toContain("DROP CONSTRAINT IF EXISTS uq_voice_order");
    expect(voiceExtension).toContain("DROP CONSTRAINT IF EXISTS uq_voice_order");
    expect(voiceExtension).toContain("CREATE UNIQUE INDEX IF NOT EXISTS uq_voice_confirmations_active_order");
    expect(voiceExtension).toContain("WHERE call_status NOT IN ('completed', 'failed', 'cancelled')");
  });

  test("voice confirmation statuses include in_progress and cancelled", () => {
    const sql = fs.readFileSync(path.join(sqlDir, "002_constraints.sql"), "utf-8");
    expect(sql).toContain("chk_voice_status");
    expect(sql).toContain("'pending'");
    expect(sql).toContain("'in_progress'");
    expect(sql).toContain("'completed'");
    expect(sql).toContain("'failed'");
    expect(sql).toContain("'ignored'");
    expect(sql).toContain("'cancelled'");
  });

  test("payment methods are constrained to supported values", () => {
    const sql = fs.readFileSync(path.join(sqlDir, "002_constraints.sql"), "utf-8");
    expect(sql).toContain("chk_payment_method");
    expect(sql).toContain("'credit_card'");
    expect(sql).toContain("'cash_on_delivery'");
    expect(sql).toContain("'apple_pay'");
  });

  test("ml model schema supports active version metadata", () => {
    const sql = fs.readFileSync(path.join(sqlDir, "006_ml_schema.sql"), "utf-8");
    expect(sql).toContain("is_active BOOLEAN");
    expect(sql).toContain("trained_at TIMESTAMPTZ");
    expect(sql).toContain("algorithm VARCHAR");
  });

  test("price prediction schema stores model outputs with traceability", () => {
    const schema = fs.readFileSync(path.join(sqlDir, "006_ml_schema.sql"), "utf-8");
    const constraints = fs.readFileSync(path.join(sqlDir, "006b_ml_constraints.sql"), "utf-8");
    const indexes = fs.readFileSync(path.join(sqlDir, "008_ml_indexes.sql"), "utf-8");

    expect(schema).toContain("CREATE TABLE IF NOT EXISTS product_price_predictions");
    expect(schema).toContain("predicted_price NUMERIC");
    expect(schema).toContain("input_features JSONB");
    expect(schema).toContain("metrics_snapshot JSONB");
    expect(constraints).toContain("fk_pricepred_product");
    expect(constraints).toContain("fk_pricepred_ml_model");
    expect(indexes).toContain("idx_price_predictions_product_created");
  });

  test("users table supports token version based session revocation", () => {
    const sql = fs.readFileSync(path.join(sqlDir, "001_tables.sql"), "utf-8");

    expect(sql).toContain("token_version INTEGER NOT NULL DEFAULT 0");
    expect(sql).toContain("ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version");
  });
});
