-- Discord Multi-Agent Memory System Schema
-- PostgreSQL + pgvector テーブル定義

-- Enable pgvector extension (should already be enabled by 01_init_pgvector.sql)
CREATE EXTENSION IF NOT EXISTS vector;

-- Long-term Memory Storage (Cold Memory)
CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    channel_id VARCHAR(20) NOT NULL,
    user_id VARCHAR(20) NOT NULL,
    agent VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 0.0,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    embedding vector(768), -- Gemini text-embedding-004 dimension
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversation Summaries for Long-term Context
CREATE TABLE IF NOT EXISTS summaries (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(20) NOT NULL,
    summary_text TEXT NOT NULL,
    time_range_start TIMESTAMP WITH TIME ZONE NOT NULL,
    time_range_end TIMESTAMP WITH TIME ZONE NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    embedding vector(768), -- Gemini text-embedding-004 dimension
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Performance Metrics
CREATE TABLE IF NOT EXISTS agent_metrics (
    id SERIAL PRIMARY KEY,
    agent VARCHAR(50) NOT NULL,
    channel_id VARCHAR(20) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    confidence_score FLOAT NOT NULL,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_memories_channel_timestamp ON memories(channel_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memories_user_timestamp ON memories(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent);
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_summaries_channel_timerange ON summaries(channel_id, time_range_start DESC, time_range_end DESC);
CREATE INDEX IF NOT EXISTS idx_summaries_embedding ON summaries USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_agent_metrics_timestamp ON agent_metrics(agent, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_channel ON agent_metrics(channel_id, timestamp DESC);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_summaries_updated_at BEFORE UPDATE ON summaries
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO discord_agent;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO discord_agent;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO discord_agent;