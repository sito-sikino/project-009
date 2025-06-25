-- v0.3.0 長期記憶システム - ベクトルインデックス最適化
-- 768次元ベクトル（text-embedding-004）用の最適化されたHNSWインデックス

-- 既存のIVFFlatインデックスを削除（存在する場合）
DROP INDEX IF EXISTS idx_unified_memories_embedding;

-- インデックス構築用のメモリ設定
SET maintenance_work_mem = '8GB';
SET max_parallel_maintenance_workers = 7;

-- 最適化されたHNSWインデックスを作成
-- m=32: 各層での接続数（本番環境での推奨値）
-- ef_construction=200: 構築時の品質パラメータ
CREATE INDEX CONCURRENTLY idx_unified_memories_embedding_hnsw
ON unified_memories USING hnsw (embedding vector_cosine_ops)
WITH (m = 32, ef_construction = 200);

-- コメントを追加
COMMENT ON INDEX idx_unified_memories_embedding_hnsw IS 
'HNSW index optimized for 768-dimensional text-embedding-004 vectors with high recall';

-- 検索パフォーマンス用の推奨設定を記録
DO $$
BEGIN
    RAISE NOTICE '=== HNSW Index Optimization Complete ===';
    RAISE NOTICE 'Recommended query settings:';
    RAISE NOTICE '  SET hnsw.ef_search = 150;  -- For balanced performance';
    RAISE NOTICE '  SET hnsw.ef_search = 200;  -- For higher recall';
    RAISE NOTICE '  SET hnsw.ef_search = 100;  -- For faster queries';
    RAISE NOTICE '';
    RAISE NOTICE 'Index details:';
    RAISE NOTICE '  - Algorithm: HNSW (Hierarchical Navigable Small World)';
    RAISE NOTICE '  - Distance: Cosine (normalized for text-embedding-004)';
    RAISE NOTICE '  - Dimensions: 768';
    RAISE NOTICE '  - Build parameters: m=32, ef_construction=200';
END $$;

-- パフォーマンス監視用のビューを作成
CREATE OR REPLACE VIEW vector_search_performance AS
SELECT 
    current_setting('hnsw.ef_search')::int as current_ef_search,
    pg_size_pretty(pg_relation_size('idx_unified_memories_embedding_hnsw')) as index_size,
    pg_size_pretty(pg_total_relation_size('unified_memories')) as total_table_size,
    (SELECT count(*) FROM unified_memories WHERE embedding IS NOT NULL) as indexed_vectors;

-- 統計情報を更新
ANALYZE unified_memories;