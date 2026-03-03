-- Database initialization script for Spotify Churn Prediction Backend
-- For PostgreSQL 14+

-- ============================================================================
-- CREATE EXTENSIONS
-- ============================================================================

-- Enable UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSON support (already included in PG 9.3+)
CREATE EXTENSION IF NOT EXISTS "plpgsql";

-- ============================================================================
-- CREATE SEQUENCES
-- ============================================================================

CREATE SEQUENCE IF NOT EXISTS prediction_log_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE IF NOT EXISTS explanation_log_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE IF NOT EXISTS playbook_execution_log_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE IF NOT EXISTS chat_session_log_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE IF NOT EXISTS api_call_log_seq START WITH 1 INCREMENT BY 1;

-- ============================================================================
-- CREATE INDEXES (will be created automatically by SQLAlchemy)
-- ============================================================================

-- These indexes are created via SQLAlchemy, but you can create them manually:

-- Prediction table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_prediction_user_date 
ON prediction_logs(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_prediction_risk_segment 
ON prediction_logs(risk_segment);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_prediction_churn_prob 
ON prediction_logs(churn_probability DESC);

-- Explanation table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_explanation_user_date 
ON explanation_logs(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_explanation_prediction 
ON explanation_logs(prediction_id);

-- Playbook table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_playbook_user_date 
ON playbook_execution_logs(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_playbook_status 
ON playbook_execution_logs(status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_playbook_playbook_id 
ON playbook_execution_logs(playbook_id);

-- Chat table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_chat_user_date 
ON chat_session_logs(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_chat_playbook 
ON chat_session_logs(playbook_recommended);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_chat_message_session 
ON chat_message_logs(session_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_chat_message_user 
ON chat_message_logs(user_id);

-- API call table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_api_endpoint_date 
ON api_call_logs(endpoint, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_api_status_code 
ON api_call_logs(status_code);

-- ============================================================================
-- CREATE MATERIALIZED VIEWS FOR ANALYTICS
-- ============================================================================

-- Daily prediction statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_prediction_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_predictions,
    AVG(churn_probability) as avg_churn_probability,
    COUNT(CASE WHEN risk_segment = 'high_risk' THEN 1 END) as high_risk_count,
    COUNT(CASE WHEN risk_segment = 'medium_risk' THEN 1 END) as medium_risk_count,
    COUNT(CASE WHEN risk_segment = 'low_risk' THEN 1 END) as low_risk_count
FROM prediction_logs
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- User engagement summary
CREATE MATERIALIZED VIEW IF NOT EXISTS user_engagement_summary AS
SELECT 
    pl.user_id,
    COUNT(DISTINCT pl.prediction_id) as total_predictions,
    MAX(pl.created_at) as last_prediction_date,
    MAX(pl.churn_probability) as current_churn_probability,
    pl.risk_segment,
    COUNT(DISTINCT cs.session_id) as chat_session_count
FROM prediction_logs pl
LEFT JOIN chat_session_logs cs ON pl.user_id = cs.user_id
GROUP BY pl.user_id, pl.risk_segment;

-- Playbook effectiveness
CREATE MATERIALIZED VIEW IF NOT EXISTS playbook_effectiveness AS
SELECT 
    playbook_id,
    COUNT(*) as executions,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
    ROUND(COUNT(CASE WHEN status = 'completed' THEN 1 END)::numeric / 
          COUNT(*)::numeric * 100, 2) as success_rate
FROM playbook_execution_logs
GROUP BY playbook_id;

-- ============================================================================
-- CREATE VIEWS FOR EASY QUERYING
-- ============================================================================

-- High-risk users requiring intervention
CREATE OR REPLACE VIEW high_risk_users AS
SELECT 
    user_id,
    MAX(prediction_id) as latest_prediction_id,
    MAX(churn_probability) as current_churn_risk,
    MAX(created_at) as last_assessed
FROM prediction_logs
WHERE risk_segment = 'high_risk'
  AND created_at > NOW() - INTERVAL '30 days'
GROUP BY user_id;

-- Recent chat interactions
CREATE OR REPLACE VIEW recent_chat_interactions AS
SELECT 
    cs.session_id,
    cs.user_id,
    cs.turn_count,
    cs.playbook_recommended,
    cs.playbook_accepted,
    COUNT(DISTINCT cm.id) as message_count,
    MAX(cm.created_at) as last_message_time
FROM chat_session_logs cs
LEFT JOIN chat_message_logs cm ON cs.session_id = cm.session_id
WHERE cs.created_at > NOW() - INTERVAL '7 days'
GROUP BY cs.session_id, cs.user_id, cs.turn_count, cs.playbook_recommended, cs.playbook_accepted;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Create application user (if not exists)
DO $$ 
BEGIN 
    CREATE USER spotify_app WITH PASSWORD 'secure_password_change_me';
EXCEPTION WHEN DUPLICATE_OBJECT THEN
    ALTER USER spotify_app WITH PASSWORD 'secure_password_change_me';
END $$;

-- Grant permissions to application user
GRANT CONNECT ON DATABASE spotify_churn TO spotify_app;
GRANT USAGE ON SCHEMA public TO spotify_app;
GRANT ALL TABLES IN SCHEMA public TO spotify_app;
GRANT ALL SEQUENCES IN SCHEMA public TO spotify_app;
GRANT SELECT ON ALL VIEWS IN SCHEMA public TO spotify_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO spotify_app;

-- ============================================================================
-- CREATE BACKUP PROCEDURE
-- ============================================================================

CREATE OR REPLACE FUNCTION backup_predict_tables()
RETURNS void AS $$
BEGIN
    -- Create backup tables if they don't exist
    CREATE TABLE IF NOT EXISTS prediction_logs_backup AS TABLE prediction_logs WITH NO DATA;
    CREATE TABLE IF NOT EXISTS chatbot_sessions_backup AS TABLE chat_session_logs WITH NO DATA;
    
    -- Backup recent data
    INSERT INTO prediction_logs_backup 
    SELECT * FROM prediction_logs 
    WHERE created_at > NOW() - INTERVAL '30 days'
    ON CONFLICT DO NOTHING;
    
    RAISE NOTICE 'Backup completed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- CREATE MAINTENANCE PROCEDURES
-- ============================================================================

-- Refresh materialized views
CREATE OR REPLACE PROCEDURE refresh_statistics()
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_prediction_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_engagement_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY playbook_effectiveness;
    RAISE NOTICE 'Statistics refreshed at %', NOW();
END;
$$;

-- Archive old logs (runs daily via cron)
CREATE OR REPLACE PROCEDURE archive_old_logs()
LANGUAGE plpgsql
AS $$
BEGIN
    -- Archive predictions older than 90 days
    DELETE FROM prediction_logs 
    WHERE created_at < NOW() - INTERVAL '90 days' 
    AND id NOT IN (SELECT prediction_id FROM playbook_execution_logs LIMIT 1000000);
    
    -- Archive chat messages older than 60 days
    DELETE FROM chat_message_logs 
    WHERE created_at < NOW() - INTERVAL '60 days' 
    AND session_id NOT IN (SELECT session_id FROM chat_session_logs WHERE playbook_accepted = true LIMIT 100000);
    
    RAISE NOTICE 'Old logs archived at %', NOW();
END;
$$;

-- ============================================================================
-- INSERT SAMPLE DATA (FOR TESTING)
-- ============================================================================

-- Insert sample predictions
INSERT INTO prediction_logs 
(id, user_id, prediction_id, churn_probability, risk_segment, prediction_label, confidence_score, model_version, created_at)
VALUES
    ('id_001', 'user_001', 'pred_001', 0.85, 'high_risk', 1, 0.92, '1.0', NOW() - INTERVAL '1 day'),
    ('id_002', 'user_002', 'pred_002', 0.45, 'medium_risk', 0, 0.88, '1.0', NOW() - INTERVAL '2 days'),
    ('id_003', 'user_003', 'pred_003', 0.15, 'low_risk', 0, 0.95, '1.0', NOW() - INTERVAL '3 days')
ON CONFLICT DO NOTHING;

-- Insert sample chat sessions
INSERT INTO chat_session_logs
(id, session_id, user_id, turn_count, playbook_recommended, playbook_accepted, created_at)
VALUES
    ('chat_id_001', 'sess_001', 'user_001', 4, 'PB_HIGH_RISK_CONVERT', true, NOW() - INTERVAL '1 day'),
    ('chat_id_002', 'sess_002', 'user_002', 2, 'PB_ENGAGEMENT', false, NOW() - INTERVAL '2 days')
ON CONFLICT DO NOTHING;

-- Refresh materialized views
-- CALL refresh_statistics();

-- ============================================================================
-- GENERATE REPORTS
-- ============================================================================

-- High-risk users report
-- SELECT * FROM high_risk_users;

-- Playbook effectiveness report
-- SELECT * FROM playbook_effectiveness;

-- Daily statistics
-- SELECT * FROM daily_prediction_stats ORDER BY date DESC LIMIT 30;

-- ============================================================================
-- END OF INITIALIZATION SCRIPT
-- ============================================================================
