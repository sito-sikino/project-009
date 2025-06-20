-- Discord Multi-Agent System - PostgreSQL + pgvector 初期化
-- Cold Memory長期記憶・セマンティック検索用データベースセットアップ

-- pgvector拡張有効化
CREATE EXTENSION IF NOT EXISTS vector;

-- UUID拡張有効化 (ID生成用)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- memories テーブル作成 (長期記憶保存)
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Discord関連情報
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    
    -- メッセージ内容
    original_content TEXT NOT NULL,
    processed_content TEXT NOT NULL,  -- 前処理済みテキスト
    
    -- エージェント選択情報
    selected_agent VARCHAR(20) NOT NULL,
    agent_response TEXT NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 0.0,
    
    -- セマンティック検索用ベクトル (text-embedding-004: 768次元)
    content_embedding vector(768),
    response_embedding vector(768),
    
    -- メタデータ
    conversation_context JSONB DEFAULT '{}',
    sentiment FLOAT DEFAULT 0.0,  -- センチメント分析 (-1.0 to 1.0)
    topic_tags TEXT[] DEFAULT '{}',  -- トピックタグ
    importance_score FLOAT DEFAULT 0.5,  -- 重要度スコア (0.0 to 1.0)
    
    -- 検索・統計用インデックス
    day_partition DATE GENERATED ALWAYS AS (DATE(created_at)) STORED,
    hour_partition INTEGER GENERATED ALWAYS AS (EXTRACT(HOUR FROM created_at)) STORED
);

-- パフォーマンス用インデックス作成
CREATE INDEX IF NOT EXISTS idx_memories_guild_channel ON memories(guild_id, channel_id);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_day_partition ON memories(day_partition);
CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(selected_agent);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance_score DESC);

-- セマンティック検索用ベクトルインデックス (HNSW: 高速近似検索)
CREATE INDEX IF NOT EXISTS idx_memories_content_embedding 
ON memories USING hnsw (content_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_memories_response_embedding 
ON memories USING hnsw (response_embedding vector_cosine_ops);

-- コンポジットインデックス (チャンネル別セマンティック検索最適化)
CREATE INDEX IF NOT EXISTS idx_memories_channel_embedding 
ON memories USING hnsw (content_embedding vector_cosine_ops) 
WHERE channel_id IS NOT NULL;

-- conversation_summaries テーブル (会話要約保存)
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Discord関連情報
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    
    -- 要約期間
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- 要約内容
    summary_text TEXT NOT NULL,
    summary_embedding vector(768),
    
    -- 統計情報
    message_count INTEGER NOT NULL DEFAULT 0,
    participant_count INTEGER NOT NULL DEFAULT 0,
    main_topics TEXT[] DEFAULT '{}',
    dominant_agent VARCHAR(20),
    
    -- メタデータ
    summary_metadata JSONB DEFAULT '{}'
);

-- 要約テーブルインデックス
CREATE INDEX IF NOT EXISTS idx_summaries_guild_channel ON conversation_summaries(guild_id, channel_id);
CREATE INDEX IF NOT EXISTS idx_summaries_time_range ON conversation_summaries(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_summaries_embedding 
ON conversation_summaries USING hnsw (summary_embedding vector_cosine_ops);

-- agent_performance テーブル (エージェント性能統計)
CREATE TABLE IF NOT EXISTS agent_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 統計期間
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- エージェント情報
    agent_name VARCHAR(20) NOT NULL,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    
    -- 性能指標
    total_responses INTEGER NOT NULL DEFAULT 0,
    average_confidence FLOAT NOT NULL DEFAULT 0.0,
    response_time_avg FLOAT NOT NULL DEFAULT 0.0,  -- 秒
    response_time_p95 FLOAT NOT NULL DEFAULT 0.0,  -- 95パーセンタイル
    
    -- 品質指標
    user_satisfaction FLOAT DEFAULT 0.0,  -- ユーザー満足度推定
    topic_accuracy FLOAT DEFAULT 0.0,     -- トピック的中率
    conversation_flow FLOAT DEFAULT 0.0,  -- 会話の流れの自然さ
    
    -- メタデータ
    performance_metadata JSONB DEFAULT '{}'
);

-- 性能統計インデックス
CREATE INDEX IF NOT EXISTS idx_performance_agent_period ON agent_performance(agent_name, period_start);
CREATE INDEX IF NOT EXISTS idx_performance_guild_channel ON agent_performance(guild_id, channel_id);

-- memory_migrations テーブル (Hot→Cold Memory移行記録)
CREATE TABLE IF NOT EXISTS memory_migrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    migrated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 移行情報
    source_type VARCHAR(20) NOT NULL,  -- 'redis_hot'
    target_type VARCHAR(20) NOT NULL,  -- 'postgres_cold'
    
    -- 統計
    messages_migrated INTEGER NOT NULL DEFAULT 0,
    migration_duration FLOAT NOT NULL DEFAULT 0.0,  -- 秒
    
    -- エラー情報
    errors_encountered INTEGER DEFAULT 0,
    error_details JSONB DEFAULT '{}',
    
    -- メタデータ
    migration_metadata JSONB DEFAULT '{}'
);

-- マイグレーション記録インデックス
CREATE INDEX IF NOT EXISTS idx_migrations_migrated_at ON memory_migrations(migrated_at DESC);
CREATE INDEX IF NOT EXISTS idx_migrations_source_target ON memory_migrations(source_type, target_type);

-- トリガー関数: updated_at自動更新
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- updated_atトリガー設定
CREATE TRIGGER update_memories_updated_at 
    BEFORE UPDATE ON memories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- セマンティック検索用関数 (類似度検索)
CREATE OR REPLACE FUNCTION find_similar_memories(
    query_embedding vector(768),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10,
    target_channel_id BIGINT DEFAULT NULL
)
RETURNS TABLE (
    memory_id UUID,
    content TEXT,
    similarity FLOAT,
    created_at TIMESTAMP WITH TIME ZONE,
    selected_agent VARCHAR(20),
    importance_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.processed_content,
        1 - (m.content_embedding <=> query_embedding) as similarity,
        m.created_at,
        m.selected_agent,
        m.importance_score
    FROM memories m
    WHERE 
        (target_channel_id IS NULL OR m.channel_id = target_channel_id)
        AND (1 - (m.content_embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY similarity DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- 会話要約検索関数
CREATE OR REPLACE FUNCTION find_relevant_summaries(
    query_embedding vector(768),
    similarity_threshold FLOAT DEFAULT 0.6,
    max_results INTEGER DEFAULT 5,
    target_channel_id BIGINT DEFAULT NULL
)
RETURNS TABLE (
    summary_id UUID,
    summary_text TEXT,
    similarity FLOAT,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    message_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.summary_text,
        1 - (s.summary_embedding <=> query_embedding) as similarity,
        s.start_time,
        s.end_time,
        s.message_count
    FROM conversation_summaries s
    WHERE 
        (target_channel_id IS NULL OR s.channel_id = target_channel_id)
        AND (1 - (s.summary_embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY similarity DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- データベース設定最適化
ALTER SYSTEM SET shared_preload_libraries = 'vector';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- 初期統計情報更新
ANALYZE memories;
ANALYZE conversation_summaries;
ANALYZE agent_performance;

-- 初期化完了ログ
INSERT INTO memories (
    guild_id, channel_id, user_id, message_id,
    original_content, processed_content,
    selected_agent, agent_response, confidence,
    content_embedding, response_embedding,
    importance_score
) VALUES (
    0, 0, 0, 0,
    'System initialization', 'Discord Multi-Agent Memory System initialized',
    'system', 'PostgreSQL + pgvector Cold Memory system ready',
    1.0,
    array_fill(0.0, ARRAY[768])::vector,
    array_fill(0.0, ARRAY[768])::vector,
    1.0
);

-- 初期化完了
\echo 'PostgreSQL + pgvector Cold Memory system initialization completed successfully!'