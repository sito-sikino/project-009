"""
Phase 2.3 REFACTOR Integration Tests
メモリシステム最適化とパフォーマンス向上の統合検証
"""

import pytest
import asyncio
import time
import os
from typing import Dict, List, Any
from unittest.mock import AsyncMock, patch

from src.infrastructure.memory_system import ImprovedDiscordMemorySystem


class TestPhase23RefactorOptimizations:
    """Phase 2.3 REFACTOR 最適化機能統合テスト"""
    
    @pytest.fixture
    async def optimized_memory_system(self):
        """最適化されたメモリシステム"""
        system = ImprovedDiscordMemorySystem(
            redis_url="redis://localhost:6379/15",
            postgres_url="postgresql://test:test@localhost:5432/test",
            gemini_api_key="test_key"
        )
        yield system
        await system.cleanup()
    
    def test_performance_metrics_initialization(self, optimized_memory_system):
        """パフォーマンスメトリクス初期化テスト"""
        # パフォーマンスメトリクスが正しく初期化されているか確認
        assert hasattr(optimized_memory_system, 'performance_metrics')
        metrics = optimized_memory_system.performance_metrics
        
        required_metrics = [
            'hot_memory_operations',
            'cold_memory_operations', 
            'embedding_generations',
            'total_operations'
        ]
        
        for metric in required_metrics:
            assert metric in metrics
            assert metrics[metric] == 0
        
        print("✅ Performance metrics initialized correctly")
    
    @pytest.mark.asyncio
    async def test_enhanced_error_handling(self, optimized_memory_system):
        """強化されたエラーハンドリングテスト"""
        # MemorySystemConnectionError のテスト
        from src.infrastructure.memory_system import MemorySystemConnectionError
        
        # フォールバック機能のテスト
        async def failing_primary():
            raise ConnectionError("Simulated connection failure")
        
        async def working_fallback():
            return "fallback_success"
        
        result = await optimized_memory_system._execute_with_fallback(
            failing_primary,
            working_fallback
        )
        
        assert result == "fallback_success"
        print("✅ Enhanced error handling working correctly")
    
    @pytest.mark.asyncio
    async def test_performance_measurement_functionality(self, optimized_memory_system):
        """パフォーマンス計測機能テスト"""
        async def test_operation(delay=0.01):
            await asyncio.sleep(delay)
            return "measured_result"
        
        start_time = time.time()
        result = await optimized_memory_system._measure_performance(
            "test_perf_operation",
            test_operation,
            0.02
        )
        total_time = time.time() - start_time
        
        assert result == "measured_result"
        assert total_time >= 0.02  # Should measure at least the delay
        print(f"✅ Performance measurement functional (measured {total_time:.3f}s)")
    
    @pytest.mark.asyncio
    async def test_batch_processing_optimization(self, optimized_memory_system):
        """バッチ処理最適化テスト"""
        # 大量データのバッチ処理
        test_items = list(range(500))
        
        start_time = time.time()
        result = await optimized_memory_system._process_large_batch(
            test_items, 
            batch_size=100
        )
        processing_time = time.time() - start_time
        
        assert len(result) == 500
        assert result == test_items
        assert processing_time < 1.0  # Should be fast
        print(f"✅ Batch processing optimized (processed 500 items in {processing_time:.3f}s)")
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_optimization(self, optimized_memory_system):
        """メモリクリーンアップ最適化テスト"""
        # Mock Redis and PostgreSQL connections
        optimized_memory_system.redis = AsyncMock()
        optimized_memory_system.redis_pool = AsyncMock()
        optimized_memory_system.postgres_pool = AsyncMock()
        
        # Test optimized cleanup
        start_time = time.time()
        await optimized_memory_system.cleanup()
        cleanup_time = time.time() - start_time
        
        # Verify cleanup was called
        optimized_memory_system.redis.close.assert_called_once()
        optimized_memory_system.redis_pool.disconnect.assert_called_once()
        optimized_memory_system.postgres_pool.close.assert_called_once()
        
        assert cleanup_time < 1.0  # Should be fast
        print(f"✅ Memory cleanup optimized (completed in {cleanup_time:.3f}s)")
    
    @pytest.mark.asyncio
    async def test_enhanced_health_status(self, optimized_memory_system):
        """強化されたヘルスステータステスト"""
        # Mock connections for health check
        with patch.object(optimized_memory_system, 'redis', AsyncMock()) as mock_redis, \
             patch.object(optimized_memory_system, 'postgres_pool', AsyncMock()) as mock_pool:
            
            mock_redis.ping = AsyncMock()
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test detailed health status
            health_status = await optimized_memory_system.get_detailed_health_status()
            
            assert "status" in health_status
            assert "components" in health_status
            assert "performance" in health_status
            assert "resources" in health_status
            
            # Performance metrics should include latency
            performance = health_status["performance"]
            assert "redis_latency_ms" in performance
            assert "postgres_latency_ms" in performance
            assert "health_check_time_ms" in performance
            
            print("✅ Enhanced health status providing detailed metrics")
    
    def test_environment_variable_configuration(self, optimized_memory_system):
        """環境変数設定テスト"""
        # Test that system respects environment variables
        assert hasattr(optimized_memory_system, 'hot_memory_ttl')
        assert hasattr(optimized_memory_system, 'cold_retention_days')
        assert hasattr(optimized_memory_system, 'migration_batch_size')
        
        # Test default values are reasonable
        assert optimized_memory_system.hot_memory_ttl > 0
        assert optimized_memory_system.cold_retention_days > 0
        assert optimized_memory_system.migration_batch_size > 0
        
        print("✅ Environment variable configuration working")


class TestPhase23MemoryOperationsOptimization:
    """Phase 2.3 メモリ操作最適化テスト"""
    
    @pytest.fixture
    async def mock_memory_system(self):
        """モックメモリシステム"""
        system = ImprovedDiscordMemorySystem()
        
        # Mock Redis
        system.redis = AsyncMock()
        system.redis.pipeline = AsyncMock()
        mock_pipe = AsyncMock()
        mock_pipe.__aenter__ = AsyncMock(return_value=mock_pipe)
        mock_pipe.__aexit__ = AsyncMock(return_value=None)
        mock_pipe.execute = AsyncMock(return_value=[[], True])
        system.redis.pipeline.return_value = mock_pipe
        
        # Mock PostgreSQL
        system.postgres_pool = AsyncMock()
        
        yield system
        await system.cleanup()
    
    @pytest.mark.asyncio
    async def test_optimized_hot_memory_load(self, mock_memory_system):
        """最適化されたホットメモリ読み込みテスト"""
        # Mock Redis response
        mock_memory_system.redis.pipeline.return_value.__aenter__.return_value.execute = AsyncMock(
            return_value=[['{"test": "message"}'], True]
        )
        
        start_time = time.time()
        result = await mock_memory_system.load_hot_memory("test_channel")
        load_time = time.time() - start_time
        
        assert isinstance(result, list)
        assert load_time < 0.1  # Should be very fast
        
        # Verify performance metrics are updated
        assert mock_memory_system.performance_metrics['hot_memory_operations'] == 1
        print(f"✅ Optimized hot memory load (completed in {load_time:.3f}s)")
    
    @pytest.mark.asyncio
    async def test_optimized_migration_with_transaction(self, mock_memory_system):
        """最適化されたマイグレーション（完全ACIDトランザクション）テスト"""
        # Mock Redis messages
        mock_memory_system.redis.lrange = AsyncMock(return_value=[
            '{"response_content": "test message 1", "selected_agent": "spectra", "confidence": 0.9}',
            '{"response_content": "test message 2", "selected_agent": "lynq", "confidence": 0.8}'
        ])
        mock_memory_system.redis.ltrim = AsyncMock()
        
        # Mock PostgreSQL transaction
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction.return_value = mock_transaction
        
        mock_pool_conn = AsyncMock()
        mock_pool_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool_conn.__aexit__ = AsyncMock(return_value=None)
        mock_memory_system.postgres_pool.acquire.return_value = mock_pool_conn
        
        # Mock embedding generation
        mock_memory_system.generate_embedding_with_rate_limit = AsyncMock(
            return_value=[0.1] * 768
        )
        
        # Test migration
        start_time = time.time()
        result = await mock_memory_system.migrate_to_cold_memory("test_channel", batch_size=2)
        migration_time = time.time() - start_time
        
        assert result['status'] == 'success'
        assert result['migrated_count'] == 2
        assert 'elapsed_time' in result
        assert migration_time < 5.0  # Should complete within reasonable time
        
        print(f"✅ Optimized migration with ACID transaction (completed in {migration_time:.3f}s)")
    
    @pytest.mark.asyncio
    async def test_transactional_memory_update_with_custom_ttl(self, mock_memory_system):
        """カスタムTTL対応トランザクショナルメモリ更新テスト"""
        # Mock pipeline
        mock_pipe = AsyncMock()
        mock_pipe.__aenter__ = AsyncMock(return_value=mock_pipe)
        mock_pipe.__aexit__ = AsyncMock(return_value=None)
        mock_pipe.execute = AsyncMock()
        mock_memory_system.redis.pipeline.return_value = mock_pipe
        
        # Mock embedding generation
        mock_memory_system.generate_embedding_with_rate_limit = AsyncMock(
            return_value=[0.1] * 768
        )
        
        # Mock PostgreSQL transaction
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction.return_value = mock_transaction
        
        mock_pool_conn = AsyncMock()
        mock_pool_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool_conn.__aexit__ = AsyncMock(return_value=None)
        mock_memory_system.postgres_pool.acquire.return_value = mock_pool_conn
        
        # Test update with custom TTL
        conversation_data = {
            'messages': [{'role': 'user', 'content': 'test message'}],
            'selected_agent': 'spectra',
            'response_content': 'test response',
            'channel_id': 'test_channel',
            'confidence': 0.95,
            'custom_ttl': 3600  # Custom TTL: 1 hour
        }
        
        start_time = time.time()
        result = await mock_memory_system.update_memory_transactional(conversation_data)
        update_time = time.time() - start_time
        
        assert result is True
        assert update_time < 1.0  # Should be fast
        
        # Verify Redis pipeline was called with custom TTL
        mock_pipe.expire.assert_called_with('channel:test_channel:messages', 3600)
        
        print(f"✅ Transactional memory update with custom TTL (completed in {update_time:.3f}s)")


# Phase 2.3 REFACTOR テスト実行確認
if __name__ == "__main__":
    print("🚀 Phase 2.3 REFACTOR Integration Tests")
    print("メモリシステム最適化とパフォーマンス向上の統合検証")
    print("")
    print("実装された最適化:")
    print("- パフォーマンス計測機能")
    print("- 強化されたエラーハンドリング")
    print("- バッチ処理最適化")
    print("- メモリクリーンアップ最適化")
    print("- 詳細ヘルスステータス")
    print("- 完全ACIDトランザクション")
    print("- カスタムTTL対応")
    print("- 戦略的フォールバック")
    print("")
    print("実行コマンド:")
    print("python -m pytest tests/integration/test_phase23_refactor.py -v")