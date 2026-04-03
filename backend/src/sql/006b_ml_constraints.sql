-- ==========================================
-- ML TRACEABILITY CONSTRAINTS (IDEMPOTENT)
-- Runs AFTER 006_ml_schema.sql creates ml_models and user_segments
-- ==========================================

DO $$
BEGIN
    -- review_analysis -> ml_models (composite FK)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_revanal_ml_model') THEN
        ALTER TABLE review_analysis ADD CONSTRAINT fk_revanal_ml_model
            FOREIGN KEY (model_name, model_version) REFERENCES ml_models(model_name, model_version) ON DELETE RESTRICT;
    END IF;

    -- product_embeddings -> ml_models (composite FK)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_prodembed_ml_model') THEN
        ALTER TABLE product_embeddings ADD CONSTRAINT fk_prodembed_ml_model
            FOREIGN KEY (model_name, model_version) REFERENCES ml_models(model_name, model_version) ON DELETE RESTRICT;
    END IF;

    -- user_segments -> ml_models (composite FK)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_usegs_ml_model') THEN
        ALTER TABLE user_segments ADD CONSTRAINT fk_usegs_ml_model
            FOREIGN KEY (model_name, model_version) REFERENCES ml_models(model_name, model_version) ON DELETE RESTRICT;
    END IF;

    -- user_segments -> users
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_usegs_user') THEN
        ALTER TABLE user_segments ADD CONSTRAINT fk_usegs_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;

    -- user_features -> users
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_ufeat_user') THEN
        ALTER TABLE user_features ADD CONSTRAINT fk_ufeat_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;

    -- user_sessions -> users
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_usess_user') THEN
        ALTER TABLE user_sessions ADD CONSTRAINT fk_usess_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;
