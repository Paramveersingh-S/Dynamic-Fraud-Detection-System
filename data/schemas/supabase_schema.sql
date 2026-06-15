-- Create these tables in Supabase PostgreSQL:

CREATE TABLE fraud_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL UNIQUE,
    user_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    decision VARCHAR(10) NOT NULL CHECK (decision IN ('APPROVE','REVIEW','STEP_UP','DECLINE')),
    fraud_score FLOAT NOT NULL,
    xgb_score FLOAT,
    nn_score FLOAT,
    if_score FLOAT,
    triggered_rules TEXT[],
    model_version TEXT NOT NULL,
    decision_latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON fraud_decisions (user_id, created_at DESC);
CREATE INDEX ON fraud_decisions (decision, created_at DESC);

CREATE TABLE fraud_labels (
    label_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES fraud_decisions(transaction_id),
    is_fraud BOOLEAN NOT NULL,
    label_source VARCHAR(20) NOT NULL,
    labeled_by TEXT,
    labeled_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE review_queue (
    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL,
    priority INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to TEXT,
    fraud_score FLOAT,
    queue_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX ON review_queue (status, priority, created_at);

-- Enable Supabase Realtime for review queue (investigators get live updates)
ALTER PUBLICATION supabase_realtime ADD TABLE review_queue;
