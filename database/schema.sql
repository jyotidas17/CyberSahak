-- =========================================
-- CyberSahak Database Schema
-- =========================================

-- USERS
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ANALYSES
CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL,

    analysis_type VARCHAR(20) NOT NULL,

    input_text TEXT,

    risk_score DECIMAL(5,2),

    threat_type VARCHAR(100),

    confidence DECIMAL(5,2),

    status VARCHAR(30) DEFAULT 'completed',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_analysis_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


-- ANALYSIS INDICATORS
CREATE TABLE IF NOT EXISTS analysis_indicators (
    id SERIAL PRIMARY KEY,

    analysis_id INTEGER NOT NULL,

    indicator TEXT NOT NULL,

    severity VARCHAR(20),

    CONSTRAINT fk_indicator_analysis
        FOREIGN KEY (analysis_id)
        REFERENCES analyses(id)
        ON DELETE CASCADE
);


-- RECOMMENDATIONS
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,

    analysis_id INTEGER NOT NULL,

    recommendation TEXT NOT NULL,

    priority VARCHAR(20),

    CONSTRAINT fk_recommendation_analysis
        FOREIGN KEY (analysis_id)
        REFERENCES analyses(id)
        ON DELETE CASCADE
);psql -U postgres -h 127.0.0.1 -d cybersahak_db -f schema.sql