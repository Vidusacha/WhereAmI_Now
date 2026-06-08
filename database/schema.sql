-- schema.sql
-- Antigravity 2.0 (AGY) Database Schema

-- 1. Prompts Library
CREATE TABLE IF NOT EXISTS prompts_library (
    id TEXT NOT NULL,
    version INTEGER NOT NULL,
    prompt_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, version)
);

-- 2. Axes Dictionary
CREATE TABLE IF NOT EXISTS axes_dictionary (
    id TEXT PRIMARY KEY,
    pole_minus_1 TEXT NOT NULL,
    pole_plus_1 TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_review'
);

-- 3. Parties Registry
CREATE TABLE IF NOT EXISTS parties_registry (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Dynamic Questionnaires
CREATE TABLE IF NOT EXISTS dynamic_questionnaires (
    id TEXT NOT NULL,
    questionnaire_version TEXT NOT NULL,
    axis_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, questionnaire_version),
    FOREIGN KEY (axis_id) REFERENCES axes_dictionary(id)
);

-- 5. Party Simulations
CREATE TABLE IF NOT EXISTS party_simulations (
    snapshot_id TEXT NOT NULL,
    party_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    questionnaire_version TEXT NOT NULL,
    score REAL NOT NULL,
    justification_quote TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (snapshot_id, party_id, question_id, questionnaire_version),
    FOREIGN KEY (party_id) REFERENCES parties_registry(id),
    FOREIGN KEY (question_id, questionnaire_version) REFERENCES dynamic_questionnaires(id, questionnaire_version)
);

-- 6. User Sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT NOT NULL,
    questionnaire_version TEXT NOT NULL,
    question_id TEXT NOT NULL,
    score REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, questionnaire_version, question_id),
    FOREIGN KEY (question_id, questionnaire_version) REFERENCES dynamic_questionnaires(id, questionnaire_version)
);
