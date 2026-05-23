-- ============================================================
-- 012_voice_confirmations_extend.sql
-- Extends the existing voice_confirmations table with fields
-- required for the phone-confirmation agent.
-- Safe to run multiple times (uses IF NOT EXISTS / IF EXISTS).
-- ============================================================

-- Missing columns
ALTER TABLE voice_confirmations
  ADD COLUMN IF NOT EXISTS retry_count      INTEGER      NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS provider_call_id VARCHAR(255),
  ADD COLUMN IF NOT EXISTS updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW();

-- Allow orders table to carry the new status values
-- orders.status is VARCHAR(30) so no type change needed; values are free-form.

-- Unique partial index: only one active (non-terminal) call per order at a time.
-- This is the database-level duplicate-call prevention.
CREATE UNIQUE INDEX IF NOT EXISTS uq_voice_confirmations_active_order
  ON voice_confirmations (order_id)
  WHERE call_status NOT IN ('completed', 'failed', 'cancelled');

-- Index for fast webhook lookups by provider_call_id
CREATE INDEX IF NOT EXISTS idx_voice_confirmations_provider_call_id
  ON voice_confirmations (provider_call_id)
  WHERE provider_call_id IS NOT NULL;

-- Auto-update updated_at on row change
CREATE OR REPLACE FUNCTION update_voice_confirmations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_voice_confirmations_updated_at ON voice_confirmations;
CREATE TRIGGER trg_voice_confirmations_updated_at
  BEFORE UPDATE ON voice_confirmations
  FOR EACH ROW EXECUTE FUNCTION update_voice_confirmations_updated_at();
