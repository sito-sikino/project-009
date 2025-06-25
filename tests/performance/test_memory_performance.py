"""
Memory System Performance Tests - TDD Phase 10

テスト対象: Memory System性能要件
目的: Hot Memory <0.1秒, Cold Memory <3.0秒性能検証
"""

import pytest
import pytest_asyncio
import asyncio
import time
import statistics
import os
from typing import List, Dict, Any
from datetime import datetime

from src.infrastructure.memory_system import ImprovedDiscordMemorySystem as DiscordMemorySystem


class TestMemoryPerformanceBenchmarks:
    """Memory System性能ベンチマークテスト"""
    
    @pytest_asyncio.fixture
    async def performance_memory_system(self):
        """性能テスト用Memory System"""
        system = DiscordMemorySystem(
            redis_url="redis://localhost:6379/14",  # 性能テスト専用DB
            postgres_url="postgresql://discord_agent:discord_agent_password@localhost:5432/discord_agent",
            gemini_api_key=os.getenv('GEMINI_API_KEY', 'test_key')
        )
        
        # 初期化
        initialized = await system.initialize()
        if not initialized:
            pytest.skip("Memory system initialization failed")
        
        yield system
        await system.cleanup()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_hot_memory_load_performance_target(self, performance_memory_system):
        """Hot Memory読み込み性能テスト: 目標0.1秒以内"""
        if not os.getenv('PERFORMANCE_TESTS_ENABLED'):
            pytest.skip("Performance tests disabled. Set PERFORMANCE_TESTS_ENABLED=1")
        
        memory_system = performance_memory_system
        test_channel = "hot_performance_test"
        
        # 事前にテストデータ準備
        for i in range(20):  # 最大容量まで追加
            await memory_system.update_memory({
                'messages': [{'role': 'user', 'content': f'性能テストメッセージ{i}'}],
                'selected_agent': 'performance_agent',
                'response_content': f'性能テスト応答{i}',
                'channel_id': test_channel,
                'confidence': 0.85
            })
        
        # 性能測定 (100回実行)
        execution_times = []
        
        for _ in range(100):
            start_time = time.perf_counter()
            
            result = await memory_system.load_hot_memory(test_channel)
            
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            # 結果確認
            assert len(result) <= 20
        
        # 統計計算
        avg_time = statistics.mean(execution_times)
        median_time = statistics.median(execution_times)
        p95_time = statistics.quantiles(execution_times, n=20)[18]  # 95パーセンタイル
        max_time = max(execution_times)
        
        # 性能要件確認
        assert avg_time < 0.1, f"Hot Memory平均応答時間目標未達: {avg_time:.4f}s > 0.1s"
        assert p95_time < 0.1, f"Hot Memory 95%応答時間目標未達: {p95_time:.4f}s > 0.1s"
        
        # 性能レポート
        print(f"\n📊 Hot Memory Performance Report:")
        print(f"   平均応答時間: {avg_time:.4f}s")
        print(f"   中央値応答時間: {median_time:.4f}s") 
        print(f"   95%応答時間: {p95_time:.4f}s")
        print(f"   最大応答時間: {max_time:.4f}s")
        print(f"   ✅ 目標達成: <0.1秒")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_hot_memory_update_performance_target(self, performance_memory_system):
        """Hot Memory更新性能テスト: 目標0.1秒以内"""
        if not os.getenv('PERFORMANCE_TESTS_ENABLED'):
            pytest.skip("Performance tests disabled")
        
        memory_system = performance_memory_system
        test_channel = "hot_update_performance_test"
        
        # 性能測定 (50回実行)
        execution_times = []
        
        for i in range(50):
            conversation_data = {
                'messages': [{'role': 'user', 'content': f'更新性能テスト{i}'}],
                'selected_agent': 'update_test_agent',
                'response_content': f'更新応答{i}',
                'channel_id': test_channel,
                'confidence': 0.9
            }
            
            start_time = time.perf_counter()
            
            result = await memory_system.update_memory(conversation_data)
            
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            assert result is True
        
        # 統計計算
        avg_time = statistics.mean(execution_times)
        p95_time = statistics.quantiles(execution_times, n=20)[18]
        
        # 性能要件確認 (更新は多少余裕を持たせて0.15秒)
        assert avg_time < 0.15, f"Hot Memory更新平均時間目標未達: {avg_time:.4f}s > 0.15s"
        
        print(f"\n📊 Hot Memory Update Performance Report:")
        print(f"   平均更新時間: {avg_time:.4f}s")
        print(f"   95%更新時間: {p95_time:.4f}s")
        print(f"   ✅ 目標達成: <0.15秒")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cold_memory_search_performance_target(self, performance_memory_system):
        """Cold Memory検索性能テスト: 目標3.0秒以内"""
        if not os.getenv('PERFORMANCE_TESTS_ENABLED'):
            pytest.skip("Performance tests disabled")
        
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY required for embedding generation")
        
        memory_system = performance_memory_system
        
        # 性能測定 (10回実行 - API制限考慮)
        execution_times = []
        search_queries = [
            "Discord機能について",
            "画像生成に関する質問",
            "プログラミングサポート",
            "データ分析のヘルプ",
            "クリエイティブなアイデア",
            "技術的な問題解決",
            "学習サポート",
            "情報検索",
            "創作活動支援",
            "総合的な相談"
        ]
        
        for i, query in enumerate(search_queries):
            try:
                start_time = time.perf_counter()
                
                result = await memory_system.load_cold_memory(query)
                
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                # 結果確認
                assert isinstance(result, list)
                assert len(result) <= 10  # max_cold_results制限
                
                # API制限回避のため小休止
                await asyncio.sleep(0.5)
                
            except Exception as e:
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    print(f"⚠️  API制限でテスト中断: {e}")
                    break
                else:
                    raise
        
        if not execution_times:
            pytest.skip("Cold Memory tests skipped due to API limitations")
        
        # 統計計算
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        # 性能要件確認
        assert avg_time < 3.0, f"Cold Memory平均検索時間目標未達: {avg_time:.4f}s > 3.0s"
        assert max_time < 5.0, f"Cold Memory最大検索時間許容範囲超過: {max_time:.4f}s > 5.0s"
        
        print(f"\n📊 Cold Memory Search Performance Report:")
        print(f"   実行回数: {len(execution_times)}")
        print(f"   平均検索時間: {avg_time:.4f}s")
        print(f"   最大検索時間: {max_time:.4f}s")
        print(f"   ✅ 目標達成: <3.0秒")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_embedding_generation_performance_target(self, performance_memory_system):
        """Embedding生成性能テスト: 目標2.0秒以内"""
        if not os.getenv('PERFORMANCE_TESTS_ENABLED'):
            pytest.skip("Performance tests disabled")
        
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY required")
        
        memory_system = performance_memory_system
        
        # 性能測定 (5回実行 - API制限考慮)
        execution_times = []
        test_texts = [
            "短いテキストの埋め込みベクトル生成テスト",
            "中程度の長さのテキストを使用した埋め込みベクトル生成の性能評価を行います。" * 5,
            "長いテキストの埋め込みベクトル生成テスト。" * 20,
            "日本語の自然言語処理における埋め込みベクトルの重要性について説明します。" * 10,
            "technical performance evaluation for embedding generation using text-embedding-004 model"
        ]
        
        for i, text in enumerate(test_texts):
            try:
                start_time = time.perf_counter()
                
                embedding = await memory_system.generate_embedding(text)
                
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                # 結果確認
                if embedding:
                    assert len(embedding) == 768  # text-embedding-004
                    assert all(isinstance(x, float) for x in embedding)
                
                # API制限回避
                await asyncio.sleep(1.0)
                
            except Exception as e:
                if "quota" in str(e).lower():
                    print(f"⚠️  API制限でテスト中断: {e}")
                    break
                else:
                    raise
        
        if not execution_times:
            pytest.skip("Embedding tests skipped due to API limitations")
        
        # 統計計算
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        # 性能要件確認 
        assert avg_time < 2.0, f"Embedding生成平均時間目標未達: {avg_time:.4f}s > 2.0s"
        
        print(f"\n📊 Embedding Generation Performance Report:")
        print(f"   実行回数: {len(execution_times)}")
        print(f"   平均生成時間: {avg_time:.4f}s")
        print(f"   最大生成時間: {max_time:.4f}s")
        print(f"   ✅ 目標達成: <2.0秒")


class TestMemorySystemScalabilityTests:
    """Memory System スケーラビリティテスト"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_multiple_channels_concurrent_access(self):
        """複数チャンネル同時アクセス性能テスト"""
        if not os.getenv('PERFORMANCE_TESTS_ENABLED'):
            pytest.skip("Performance tests disabled")
        
        memory_system = DiscordMemorySystem(
            redis_url="redis://localhost:6379/13"  # スケーラビリティテスト専用
        )
        
        initialized = await memory_system.initialize()
        if not initialized:
            pytest.skip("Memory system initialization failed")
        
        # 10チャンネル同時アクセステスト
        channels = [f"scale_test_channel_{i}" for i in range(10)]
        
        async def channel_operations(channel_id: str):
            """チャンネル別操作"""
            operations_time = []
            
            for i in range(5):
                # 更新操作
                start_time = time.perf_counter()
                await memory_system.update_memory({
                    'messages': [{'role': 'user', 'content': f'{channel_id}_message_{i}'}],
                    'selected_agent': 'scale_agent',
                    'response_content': f'{channel_id}_response_{i}',
                    'channel_id': channel_id,
                    'confidence': 0.8
                })
                
                # 読み込み操作
                await memory_system.load_hot_memory(channel_id)
                end_time = time.perf_counter()
                
                operations_time.append(end_time - start_time)
            
            return operations_time
        
        # 同時実行
        start_total = time.perf_counter()
        
        tasks = [channel_operations(channel) for channel in channels]
        results = await asyncio.gather(*tasks)
        
        end_total = time.perf_counter()
        total_time = end_total - start_total
        
        # 性能確認
        all_operation_times = [time for result in results for time in result]
        avg_operation_time = statistics.mean(all_operation_times)
        
        # 同時アクセスでも平均操作時間が0.2秒以内
        assert avg_operation_time < 0.2, f"同時アクセス時の操作時間目標未達: {avg_operation_time:.4f}s > 0.2s"
        assert total_time < 10.0, f"全体実行時間目標未達: {total_time:.2f}s > 10.0s"
        
        print(f"\n📊 Concurrent Access Performance Report:")
        print(f"   チャンネル数: {len(channels)}")
        print(f"   総操作数: {len(all_operation_times)}")
        print(f"   平均操作時間: {avg_operation_time:.4f}s")
        print(f"   総実行時間: {total_time:.2f}s")
        print(f"   ✅ スケーラビリティ目標達成")
        
        await memory_system.cleanup()
    
    @pytest.mark.performance
    @pytest.mark.asyncio 
    async def test_memory_system_resource_usage(self):
        """Memory System リソース使用量テスト"""
        if not os.getenv('PERFORMANCE_TESTS_ENABLED'):
            pytest.skip("Performance tests disabled")
        
        memory_system = DiscordMemorySystem(
            redis_url="redis://localhost:6379/12"  # リソーステスト専用
        )
        
        initialized = await memory_system.initialize()
        if not initialized:
            pytest.skip("Memory system initialization failed")
        
        # 大量データ処理テスト
        test_channel = "resource_test_channel"
        
        # 1000件のメッセージ処理
        start_time = time.perf_counter()
        
        for i in range(1000):
            await memory_system.update_memory({
                'messages': [{'role': 'user', 'content': f'リソーステスト{i}'}],
                'selected_agent': 'resource_agent',
                'response_content': f'リソース応答{i}',
                'channel_id': test_channel,
                'confidence': 0.7
            })
            
            # 100件ごとに読み込み
            if i % 100 == 0:
                await memory_system.load_hot_memory(test_channel)
        
        end_time = time.perf_counter()
        total_processing_time = end_time - start_time
        
        # 統計確認
        stats = await memory_system.get_memory_stats()
        
        # 性能要件
        assert total_processing_time < 60.0, f"大量データ処理時間目標未達: {total_processing_time:.2f}s > 60.0s"
        assert stats['status'] == 'connected'
        
        print(f"\n📊 Resource Usage Test Report:")
        print(f"   処理件数: 1000件")
        print(f"   総処理時間: {total_processing_time:.2f}s")
        print(f"   平均処理時間: {total_processing_time/1000:.4f}s/件")
        print(f"   Hot Memory使用量: {stats['hot_memory']['total_messages']}件")
        print(f"   ✅ リソース効率性目標達成")
        
        await memory_system.cleanup()


# 性能テスト実行補助
if __name__ == "__main__":
    print("⚡ Memory System Performance Tests")
    print("高負荷性能テストのため、専用環境での実行を推奨")
    print("")
    print("実行例:")
    print("export PERFORMANCE_TESTS_ENABLED=1")
    print("export GEMINI_API_KEY=your_api_key")
    print("docker-compose up -d")
    print("python -m pytest tests/performance/test_memory_performance.py -v -s --tb=short")
    print("")
    print("性能目標:")
    print("- Hot Memory: <0.1秒")
    print("- Cold Memory: <3.0秒")
    print("- Embedding: <2.0秒")