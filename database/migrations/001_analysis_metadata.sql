-- Additive migration. Does not alter users or remove existing records.
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS detection_method VARCHAR(40) NOT NULL DEFAULT 'legacy';
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS model_version VARCHAR(40) NOT NULL DEFAULT 'legacy';
ALTER TABLE analysis_indicators ADD COLUMN IF NOT EXISTS evidence TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_analyses_user_created ON analyses (user_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_indicators_analysis ON analysis_indicators (analysis_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_analysis ON recommendations (analysis_id);
