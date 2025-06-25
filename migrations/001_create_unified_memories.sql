-- v0.3.0 長期記憶システム - unified_memories テーブル作成
-- 原子的記憶による個別具体的要素の完全検索・進捗追跡システム

-- pgvector拡張が必要（インストール確認）
CREATE EXTENSION IF NOT EXISTS vector;

-- 既存テーブルが存在する場合は削除して再作成
DROP TABLE IF EXISTS unified_memories CASCADE;

-- unified_memories テーブル作成
CREATE TABLE unified_memories (
    -- 基本識別情報
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Discord関連情報
    channel_id BIGINT NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    message_id VARCHAR(255),
    
    -- 記憶内容
    content TEXT NOT NULL,
    memory_type VARCHAR(50) NOT NULL, -- 'task', 'conversation', 'progress', 'entity' など
    
    -- 構造化メタデータ
    metadata JSONB NOT NULL DEFAULT '{}',
    
    -- セマンティック検索用 embedding
    embedding vector(768), -- text-embedding-004 の次元数
    
    -- 重複検出用ハッシュ（datasketch MinHash用）
    minhash_signature BYTEA,
    
    -- 検索・分析用フィールド
    entities JSONB DEFAULT '[]', -- 抽出されたエンティティ（人名、技術、プロジェクト等）
    progress_type VARCHAR(100), -- 進捗タイプ（学習、開発、創作等）
    importance_score FLOAT DEFAULT 0.0, -- 重要度スコア（0.0-1.0）
    
    -- インデックス用タイムスタンプ
    date_key DATE GENERATED ALWAYS AS (memory_timestamp::DATE) STORED
);

-- インデックス作成

-- 1. pgvector コサイン類似度検索用（最重要）
CREATE INDEX IF NOT EXISTS idx_unified_memories_embedding 
ON unified_memories USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 2. 日付範囲検索用
CREATE INDEX IF NOT EXISTS idx_unified_memories_date 
ON unified_memories (date_key DESC, memory_timestamp DESC);

-- 3. チャンネル・ユーザー検索用
CREATE INDEX IF NOT EXISTS idx_unified_memories_channel_user 
ON unified_memories (channel_id, user_id, memory_timestamp DESC);

-- 4. 記憶タイプ別検索用
CREATE INDEX IF NOT EXISTS idx_unified_memories_type 
ON unified_memories (memory_type, memory_timestamp DESC);

-- 5. エンティティ検索用（JSONB GIN）
CREATE INDEX IF NOT EXISTS idx_unified_memories_entities 
ON unified_memories USING gin (entities);

-- 6. メタデータ検索用（JSONB GIN）
CREATE INDEX IF NOT EXISTS idx_unified_memories_metadata 
ON unified_memories USING gin (metadata);

-- 7. 重要度・進捗検索用
CREATE INDEX IF NOT EXISTS idx_unified_memories_progress 
ON unified_memories (progress_type, importance_score DESC, memory_timestamp DESC);

-- 既存関数削除（戻り値型変更のため）
DROP FUNCTION IF EXISTS search_unified_memories(vector, double precision, integer, date, character varying[]);

-- セマンティック検索関数
CREATE OR REPLACE FUNCTION search_unified_memories(
    query_embedding vector(768),
    similarity_threshold FLOAT DEFAULT 0.7,
    limit_count INT DEFAULT 20,
    date_filter DATE DEFAULT NULL,
    memory_types VARCHAR[] DEFAULT NULL
) RETURNS TABLE (
    id UUID,
    memory_timestamp TIMESTAMP,
    channel_id BIGINT,
    user_id VARCHAR(255),
    content TEXT,
    memory_type VARCHAR(50),
    metadata JSONB,
    entities JSONB,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.memory_timestamp,
        m.channel_id,
        m.user_id,
        m.content,
        m.memory_type,
        m.metadata,
        m.entities,
        (1 - (m.embedding <=> query_embedding))::FLOAT as similarity
    FROM unified_memories m
    WHERE 
        (1 - (m.embedding <=> query_embedding)) > similarity_threshold
        AND (date_filter IS NULL OR m.date_key >= date_filter)
        AND (memory_types IS NULL OR m.memory_type = ANY(memory_types))
    ORDER BY similarity DESC, m.memory_timestamp DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- 既存ビュー削除
DROP VIEW IF EXISTS daily_entity_progress CASCADE;

-- 進捗追跡ビュー（日別エンティティ進捗）
CREATE VIEW daily_entity_progress AS
SELECT 
    date_key,
    entity->>'name' as entity_name,
    entity->>'type' as entity_type,
    COUNT(*) as mention_count,
    AVG(importance_score) as avg_importance,
    array_agg(DISTINCT memory_type) as memory_types,
    array_agg(DISTINCT channel_id) as channels
FROM unified_memories,
     jsonb_array_elements(entities) as entity
WHERE entities IS NOT NULL AND jsonb_array_length(entities) > 0
GROUP BY date_key, entity->>'name', entity->>'type'
ORDER BY date_key DESC, avg_importance DESC;

-- データ保持ポリシー（30日以上の古いデータ削除用）
CREATE OR REPLACE FUNCTION cleanup_old_memories(days_to_keep INT DEFAULT 30)
RETURNS INT AS $$
DECLARE
    deleted_count INT;
BEGIN
    DELETE FROM unified_memories 
    WHERE memory_timestamp < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 統計・メタデータ更新関数
CREATE OR REPLACE FUNCTION refresh_memory_statistics()
RETURNS VOID AS $$
BEGIN
    -- 統計情報の更新
    ANALYZE unified_memories;
    
    -- pgvectorインデックスの再構築（必要に応じて）
    -- REINDEX INDEX idx_unified_memories_embedding;
END;
$$ LANGUAGE plpgsql;

-- 初期化完了ログ
DO $$
BEGIN
    RAISE NOTICE 'unified_memories テーブルと関連機能が正常に作成されました';
    RAISE NOTICE '- テーブル: unified_memories';
    RAISE NOTICE '- インデックス: 7個（embedding, date, channel_user, type, entities, metadata, progress）';
    RAISE NOTICE '- 関数: search_unified_memories, cleanup_old_memories, refresh_memory_statistics';
    RAISE NOTICE '- ビュー: daily_entity_progress';
END $$;