-- Stage 1 provider/scoring/alert review hardening.
-- Keeps V1 research and paper-trading only; no live trading credentials or private keys are stored.

ALTER TABLE wallet_movements
    ADD COLUMN IF NOT EXISTS data_quality_reasons JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE agent_alerts
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'open',
    ADD COLUMN IF NOT EXISTS analyst_notes TEXT,
    ADD COLUMN IF NOT EXISTS candidate_decision TEXT NOT NULL DEFAULT 'manual_review';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'agent_alerts_status_check'
    ) THEN
        ALTER TABLE agent_alerts
            ADD CONSTRAINT agent_alerts_status_check
            CHECK (status IN ('open', 'acknowledged', 'dismissed', 'escalated'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'agent_alerts_candidate_decision_check'
    ) THEN
        ALTER TABLE agent_alerts
            ADD CONSTRAINT agent_alerts_candidate_decision_check
            CHECK (candidate_decision IN ('watch', 'manual_review', 'ignore', 'paper_copy_candidate'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_agent_alerts_status_created
    ON agent_alerts (status, created_at DESC);
