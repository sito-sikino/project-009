"""
Memory System Unit Tests - TDD Phase 8 (Red/Green Phase)

テスト対象: DiscordMemorySystem (Redis Hot Memory + PostgreSQL Cold Memory) 
目的: Memory System全機能のテスト検証
"""

import pytest
import pytest_asyncio
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any
from datetime import datetime, timedelta

# テスト対象をインポート
from src.infrastructure.memory_system import ImprovedDiscordMemorySystem as DiscordMemorySystem, MemoryItem, create_improved_memory_system as create_memory_system


class TestMemoryItem:
    """MemoryItem基本構造テスト"""
    
    def test_memory_item_creation(self):
        """MemoryItem作成テスト"""
        # ARRANGE & ACT
        item = MemoryItem(
            content="テストメッセージ",
            timestamp=datetime.now(),
            channel_id="12345",
            user_id="67890",
            agent="spectra",
            confidence=0.95,
            metadata={"test": True}
        )
        
        # ASSERT
        assert item.content == "テストメッセージ"
        assert item.channel_id == "12345"
        assert item.agent == "spectra"
        assert item.confidence == 0.95
        assert item.metadata["test"] is True
    
    def test_memory_item_to_dict(self):
        """MemoryItem辞書変換テスト"""
        # ARRANGE
        timestamp = datetime.now()
        item = MemoryItem(
            content="辞書変換テスト",
            timestamp=timestamp,
            channel_id="111",
            user_id="222", 
            agent="lynq",
            confidence=0.88
        )
        
        # ACT
        item_dict = item.to_dict()
        
        # ASSERT
        assert item_dict["content"] == "辞書変換テスト"
        assert item_dict["timestamp"] == timestamp.isoformat()
        assert item_dict["channel_id"] == "111"
        assert item_dict["agent"] == "lynq"
        assert item_dict["confidence"] == 0.88
        assert item_dict["metadata"] == {}


class TestDiscordMemorySystem:
    """DiscordMemorySystem主要機能テスト"""
    
    @pytest_asyncio.fixture
    async def memory_system(self):
        """Memory Systemテスト用セットアップ"""
        system = DiscordMemorySystem(
            redis_url="redis://localhost:6379/15",  # テスト用DB
            postgres_url="postgresql://test:test@localhost:5432/test_db",
            gemini_api_key="test_gemini_key"
        )
        return system
    
    @pytest_asyncio.fixture
    async def mock_redis_client(self):
        """Redisクライアントモック"""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_redis.lpush = AsyncMock(return_value=1)
        mock_redis.ltrim = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.llen = AsyncMock(return_value=0)
        mock_redis.close = AsyncMock()
        return mock_redis
    
    @pytest_asyncio.fixture
    async def mock_postgres_pool(self):
        """PostgreSQLプールモック"""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_conn.fetch = AsyncMock(return_value=[{"extname": "vector"}])
        mock_conn.execute = AsyncMock()
        
        # Context manager設定 - 正しい実装
        def create_context_manager():
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            return mock_context_manager
        
        # acquireは非同期関数ではないので、MagicMockを使用
        mock_pool.acquire = MagicMock(side_effect=create_context_manager)
        mock_pool.close = AsyncMock()
        return mock_pool
    
    @pytest_asyncio.fixture
    async def mock_embeddings_client(self):
        """Embeddingsクライアントモック"""
        mock_client = MagicMock()
        mock_client.embed_query = MagicMock(return_value=[0.1] * 768)  # 768次元ベクトル
        return mock_client

    def test_memory_system_initialization(self, memory_system):
        """Memory System初期化テスト"""
        # ASSERT
        assert memory_system.redis_url.endswith("/15")
        assert "test_db" in memory_system.postgres_url
        assert memory_system.hot_memory_limit == 20
        assert memory_system.embedding_model == "text-embedding-004"
        assert memory_system.similarity_threshold == 0.7
        assert memory_system.max_cold_results == 10

    @pytest.mark.asyncio
    async def test_memory_system_initialize_success(self, memory_system, mock_redis_client, mock_postgres_pool):
        """Memory System初期化成功テスト"""
        # ARRANGE: モッククライアント設定  
        with patch('redis.asyncio.from_url', return_value=mock_redis_client), \
             patch('asyncpg.create_pool', new_callable=AsyncMock, return_value=mock_postgres_pool), \
             patch('langchain_google_genai.GoogleGenerativeAIEmbeddings'):
            
            # PostgreSQL拡張確認モック - fixtureでsetupしたmock_connを使用
            
            # ACT
            result = await memory_system.initialize()
            
            # ASSERT
            assert result is True
            assert memory_system.redis == mock_redis_client
            assert memory_system.postgres_pool == mock_postgres_pool

    @pytest.mark.asyncio
    async def test_load_hot_memory_success(self, memory_system, mock_redis_client):
        """Hot Memory読み込み成功テスト"""
        # ARRANGE
        memory_system.redis = mock_redis_client
        test_messages = [
            json.dumps({
                "timestamp": datetime.now().isoformat(),
                "content": "メッセージ1",
                "agent": "spectra"
            }),
            json.dumps({
                "timestamp": datetime.now().isoformat(),
                "content": "メッセージ2", 
                "agent": "lynq"
            })
        ]
        mock_redis_client.lrange.return_value = test_messages
        
        # ACT
        result = await memory_system.load_hot_memory("12345")
        
        # ASSERT
        assert len(result) == 2
        assert result[0]["content"] == "メッセージ1"
        assert result[1]["agent"] == "lynq"
        mock_redis_client.lrange.assert_called_once_with("channel:12345:messages", 0, 19)

    @pytest.mark.asyncio
    async def test_load_hot_memory_empty(self, memory_system, mock_redis_client):
        """Hot Memory空データテスト"""
        # ARRANGE
        memory_system.redis = mock_redis_client
        mock_redis_client.lrange.return_value = []
        
        # ACT
        result = await memory_system.load_hot_memory("empty")
        
        # ASSERT
        assert result == []

    @pytest.mark.asyncio
    async def test_load_cold_memory_success(self, memory_system, mock_postgres_pool, mock_embeddings_client):
        """Cold Memory検索成功テスト"""
        # ARRANGE
        memory_system.postgres_pool = mock_postgres_pool
        memory_system.embeddings_client = mock_embeddings_client
        
        # Mock embedding生成
        with patch.object(memory_system, 'generate_embedding_with_rate_limit', return_value=[0.1] * 768):
            # Mock PostgreSQL応答
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[
                {
                    'memory_id': 'uuid-123',
                    'content': '関連する記憶',
                    'similarity': 0.85,
                    'created_at': datetime.now(),
                    'selected_agent': 'paz',
                    'importance_score': 0.9
                }
            ])
            # Use the same context manager pattern as the fixture
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_postgres_pool.acquire = MagicMock(return_value=mock_context_manager)
            
            # ACT
            result = await memory_system.load_cold_memory("検索クエリ")
            
            # ASSERT
            assert len(result) == 1
            assert result[0]['content'] == '関連する記憶'
            assert result[0]['similarity'] == 0.85
            assert result[0]['selected_agent'] == 'paz'

    @pytest.mark.asyncio
    async def test_update_memory_success(self, memory_system, mock_redis_client, mock_postgres_pool):
        """Memory更新成功テスト"""
        # ARRANGE
        memory_system.redis = mock_redis_client
        memory_system.postgres_pool = mock_postgres_pool
        
        conversation_data = {
            'messages': [{'role': 'user', 'content': 'テスト会話'}],
            'selected_agent': 'spectra',
            'response_content': 'テスト応答',
            'channel_id': '12345',
            'confidence': 0.92
        }
        
        # Mock embedding生成
        with patch.object(memory_system, 'generate_embedding_with_rate_limit', return_value=[0.1] * 768):
            # Mock PostgreSQL
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_postgres_pool.acquire = MagicMock(return_value=mock_context_manager)
            
            # ACT
            result = await memory_system.update_memory_transactional(conversation_data)
            
            # ASSERT
            assert result is True
            
            # Hot Memory更新確認
            mock_redis_client.lpush.assert_called_once()
            mock_redis_client.ltrim.assert_called_once()
            mock_redis_client.expire.assert_called_once()
            
            # Cold Memory更新確認
            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, memory_system, mock_embeddings_client):
        """Embedding生成成功テスト"""
        # ARRANGE
        memory_system.embeddings_client = mock_embeddings_client
        test_text = "埋め込みベクトル生成テスト"
        
        # ACT
        with patch('asyncio.to_thread', return_value=[0.1] * 768) as mock_to_thread:
            result = await memory_system.generate_embedding_with_rate_limit(test_text)
            
            # ASSERT
            assert len(result) == 768
            assert all(isinstance(x, float) for x in result)
            mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, memory_system):
        """Embedding生成空テキストテスト"""
        # ACT
        result = await memory_system.generate_embedding_with_rate_limit("")
        
        # ASSERT
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_embedding_long_text(self, memory_system, mock_embeddings_client):
        """Embedding生成長文テスト"""
        # ARRANGE
        memory_system.embeddings_client = mock_embeddings_client
        long_text = "テスト" * 3000  # 長いテキスト
        
        # ACT
        with patch('asyncio.to_thread', return_value=[0.1] * 768) as mock_to_thread:
            result = await memory_system.generate_embedding_with_rate_limit(long_text)
            
            # ASSERT
            assert result is not None
            mock_to_thread.assert_called_once()
            # 引数のテキストが適切に切り詰められていることを確認
            called_args = mock_to_thread.call_args[0]
            assert len(called_args[1]) <= 8192  # 2048 * 4

    @pytest.mark.asyncio
    async def test_get_memory_stats(self, memory_system, mock_redis_client, mock_postgres_pool):
        """Memory統計取得テスト"""
        # ARRANGE
        memory_system.redis = mock_redis_client
        memory_system.postgres_pool = mock_postgres_pool
        
        # Mock Redis統計
        mock_redis_client.keys.return_value = ["channel:1:messages", "channel:2:messages"]
        mock_redis_client.llen.return_value = 15
        
        # Mock PostgreSQL統計
        mock_conn = AsyncMock()
        mock_conn.fetchval.side_effect = [100, 5]  # memories, summaries
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_postgres_pool.acquire = MagicMock(return_value=mock_context_manager)
        
        # ACT
        stats = await memory_system.get_memory_stats()
        
        # ASSERT
        assert stats['status'] == 'connected'
        assert stats['hot_memory']['total_channels'] == 2
        assert stats['hot_memory']['total_messages'] == 30  # 15 * 2
        assert stats['cold_memory']['total_memories'] == 100
        assert stats['cold_memory']['total_summaries'] == 5

    @pytest.mark.asyncio
    async def test_cleanup_success(self, memory_system, mock_redis_client, mock_postgres_pool):
        """Memory System正常終了テスト"""
        # ARRANGE
        memory_system.redis = mock_redis_client
        memory_system.postgres_pool = mock_postgres_pool
        
        # ACT
        await memory_system.cleanup()
        
        # ASSERT
        mock_redis_client.close.assert_called_once()
        mock_postgres_pool.close.assert_called_once()


class TestMemorySystemFactory:
    """Memory System Factory テスト"""
    
    def test_create_memory_system(self):
        """Memory System生成テスト"""
        # ARRANGE & ACT
        with patch.dict('os.environ', {
            'REDIS_URL': 'redis://test:6379',
            'POSTGRESQL_URL': 'postgresql://test:test@localhost/test',
            'GEMINI_API_KEY': 'test_key'
        }):
            system = create_memory_system()
            
            # ASSERT
            assert isinstance(system, DiscordMemorySystem)
            assert system.redis_url == 'redis://test:6379'
            assert 'test:test@localhost/test' in system.postgres_url


class TestMemorySystemIntegration:
    """Memory System統合テスト"""
    
    @pytest.mark.asyncio
    async def test_hot_to_cold_memory_integration(self):
        """Hot→Cold Memory統合テスト"""
        # TODO: 実際のRedis/PostgreSQL接続が必要
        # 本テストは docker-compose up 環境でのみ実行
        pytest.skip("Requires actual Redis/PostgreSQL containers")
    
    @pytest.mark.asyncio
    async def test_embedding_search_integration(self):
        """Embedding検索統合テスト"""
        # TODO: Gemini API Key必要
        pytest.skip("Requires GEMINI_API_KEY for text-embedding-004")
    
    @pytest.mark.asyncio
    async def test_memory_system_with_langgraph(self):
        """Memory System + LangGraph統合テスト"""
        # TODO: LangGraph Supervisor統合テスト
        pytest.skip("Requires full system integration test")


# TDD Memory Phase確認用のテスト実行
if __name__ == "__main__":
    print("🧠 TDD Memory Phase: Memory System Validation")
    print("これらのテストはMemory System全機能を検証します")
    
    # Memory System実装確認
    try:
        from src.infrastructure.memory_system import ImprovedDiscordMemorySystem as DiscordMemorySystem
        print("✅ Memory System tests ready: DiscordMemorySystem available")
    except ImportError as e:
        print(f"❌ Memory System test requirements not met: {e}")


class TestMemorySystemPhase2Features:
    """Phase 2実装予定機能の失敗テスト（TDD RED段階）"""
    
    @pytest.mark.asyncio
    async def test_hot_memory_ttl_environment_variable(self):
        """HOT_MEMORY_TTL_SECONDS環境変数読み込みテスト（失敗）"""
        with patch.dict('os.environ', {'HOT_MEMORY_TTL_SECONDS': '7200'}):
            memory_system = DiscordMemorySystem()
            
            # 現在はハードコーディング86400のため、環境変数7200は反映されない（失敗）
            assert memory_system.hot_memory_ttl == 7200  # 期待: 環境変数値、実際: 86400
    
    @pytest.mark.asyncio
    async def test_migrate_to_cold_memory_method_exists(self):
        """migrate_to_cold_memory()メソッド存在テスト（失敗）"""
        memory_system = DiscordMemorySystem()
        
        # メソッドが存在しないためAttributeErrorで失敗
        with pytest.raises(AttributeError):
            await memory_system.migrate_to_cold_memory("test_channel", 10)
    
    @pytest.mark.asyncio
    async def test_unified_memories_table_operations(self):
        """unified_memoriesテーブル操作テスト（失敗）"""
        memory_system = DiscordMemorySystem()
        
        with patch.object(memory_system, 'postgres_pool') as mock_pool:
            mock_conn = AsyncMock()
            mock_pool.acquire().__aenter__.return_value = mock_conn
            mock_conn.fetch.return_value = []
            
            # load_cold_memory()は一時無効化でempty listを返す（失敗）
            result = await memory_system.load_cold_memory("test query", "channel123")
            
            # 期待: PostgreSQL検索結果、実際: 空配列（一時無効化）
            assert len(result) > 0  # 失敗するはず
    
    @pytest.mark.asyncio
    async def test_redis_expire_with_configurable_ttl(self):
        """Redis EXPIRE設定可能TTLテスト（失敗）"""
        memory_system = DiscordMemorySystem()
        
        with patch.object(memory_system, 'redis') as mock_redis:
            mock_redis.lpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            mock_redis.expire = AsyncMock()
            
            # 個別TTL設定機能が存在しないため、固定TTLのみ使用（失敗）
            conversation_data = {
                'channel_id': '12345',
                'messages': [{'content': 'test'}],
                'custom_ttl': 3600  # カスタムTTL指定
            }
            
            await memory_system.update_memory_transactional(conversation_data)
            
            # 期待: カスタムTTL(3600)使用、実際: 固定TTL(86400)使用
            mock_redis.expire.assert_called_with('channel:12345:messages', 3600)  # 失敗するはず
    
    @pytest.mark.asyncio
    async def test_postgresql_vector_search_active(self):
        """PostgreSQL pgvector検索アクティブテスト（失敗）"""
        memory_system = DiscordMemorySystem()
        
        with patch.object(memory_system, 'postgres_pool') as mock_pool:
            mock_conn = AsyncMock()
            mock_pool.acquire().__aenter__.return_value = mock_conn
            mock_conn.fetch.return_value = [
                {'memory_id': '1', 'content': 'test', 'similarity': 0.8}
            ]
            
            # load_cold_memory()が実際に検索を実行することを期待（失敗）
            result = await memory_system.load_cold_memory("test query")
            
            # 期待: PostgreSQL検索実行、実際: 一時無効化で空配列
            assert len(result) == 1  # 失敗するはず（一時無効化のため）
            assert result[0]['memory_id'] == '1'  # 失敗するはず
    
    @pytest.mark.asyncio
    async def test_environment_variable_configuration_support(self):
        """環境変数設定サポートテスト（失敗）"""
        env_vars = {
            'HOT_MEMORY_TTL_SECONDS': '7200',
            'COLD_MEMORY_RETENTION_DAYS': '60',
            'MEMORY_MIGRATION_BATCH_SIZE': '200'
        }
        
        with patch.dict('os.environ', env_vars):
            memory_system = DiscordMemorySystem()
            
            # 環境変数読み込み機能が未実装のため失敗
            assert memory_system.hot_memory_ttl == 7200  # 失敗: ハードコーディング値
            assert hasattr(memory_system, 'cold_retention_days')  # 失敗: 属性未実装
            assert hasattr(memory_system, 'migration_batch_size')  # 失敗: 属性未実装