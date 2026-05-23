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

  test("users table supports token version based session revocation", () => {
    const sql = fs.readFileSync(path.join(sqlDir, "001_tables.sql"), "utf-8");

    expect(sql).toContain("token_version INTEGER NOT NULL DEFAULT 0");
    expect(sql).toContain("ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version");
  });
});
