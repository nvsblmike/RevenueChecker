CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id VARCHAR(100) UNIQUE NOT NULL,
  email VARCHAR(320) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_app_users_email ON app_users(email);

CREATE TABLE IF NOT EXISTS assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES app_users(id),
  business_name VARCHAR(120) NOT NULL,
  industry VARCHAR(80) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'completed',
  input_data JSONB NOT NULL,
  report_data JSONB NOT NULL,
  leakage_low NUMERIC(18,2) NOT NULL,
  leakage_high NUMERIC(18,2) NOT NULL,
  recovery_low NUMERIC(18,2) NOT NULL,
  recovery_high NUMERIC(18,2) NOT NULL,
  confidence VARCHAR(20) NOT NULL,
  ai_model VARCHAR(80) NOT NULL,
  consent_to_email BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_assessments_user_id ON assessments(user_id);
CREATE INDEX IF NOT EXISTS ix_assessments_created_at ON assessments(created_at);

CREATE TABLE IF NOT EXISTS email_deliveries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES assessments(id),
  recipient VARCHAR(320) NOT NULL,
  status VARCHAR(30) NOT NULL,
  provider_message_id VARCHAR(100),
  error_message TEXT,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_email_deliveries_assessment_id ON email_deliveries(assessment_id);
