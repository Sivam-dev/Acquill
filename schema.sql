CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    last_touched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    next_review_at TIMESTAMP WITH TIME ZONE,
    review_interval_days INTEGER NOT NULL DEFAULT 1,
    mistake_patterns JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topic_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    prerequisite_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(topic_id, prerequisite_id)
);

CREATE TABLE IF NOT EXISTS topic_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('solved', 'struggled', 'asked')),
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_topic_history_topic_id ON topic_history(topic_id);
CREATE INDEX IF NOT EXISTS idx_topic_history_created_at ON topic_history(created_at);
CREATE INDEX IF NOT EXISTS idx_topic_history_event_type ON topic_history(event_type);
CREATE INDEX IF NOT EXISTS idx_documents_topic_id ON documents(topic_id);
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_topic_dependencies_topic_id ON topic_dependencies(topic_id);
CREATE INDEX IF NOT EXISTS idx_topic_dependencies_prerequisite_id ON topic_dependencies(prerequisite_id);
