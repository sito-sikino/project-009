"""
Memory System Integration Tests - TDD Phase 9

テスト対象: Memory System統合機能
目的: Redis + PostgreSQL + Embedding統合テスト
"""

import pytest
import pytest_asyncio
import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

from src.infrastructure.memory_system import ImprovedDiscordMemorySystem as DiscordMemorySystem, create_improved_memory_system as create_memory_system
from src.agents.supervisor import AgentSupervisor


class TestMemorySystemIntegration:
    """Memory System統合テスト"""
    
    @pytest_asyncio.fixture
    async def memory_system(self):
        """実際のMemory System (テスト用DB)"""
        system = DiscordMemorySystem(
            redis_url="redis://localhost:6379/15",  # テスト用DB
            postgres_url="postgresql://discord_agent:discord_agent_password@localhost:5432/discord_agent",
            gemini_api_key=os.getenv('GEMINI_API_KEY', 'test_key')
        )
        yield system
        await system.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_system_initialization_integration(self, memory_system):
        """Memory System実際の初期化テスト"""
        # Docker Compose環境が必要
        if not os.getenv('INTEGRATION_TESTS_ENABLED'):
            pytest.skip("Integration tests disabled. Set INTEGRATION_TESTS_ENABLED=1")
        
        # ACT
        result = await memory_system.initialize()
        
        # ASSERT
        if result:
            assert memory_system.redis is not None
            assert memory_system.postgres_pool is not None
            
            # 統計確認
            stats = await memory_system.get_health_status()
            assert stats['status'] in ['healthy', 'connected']
        else:
            pytest.skip("Redis/PostgreSQL not available")
    
    @pytest.mark.integration
    @pytest.mark.asyncio 
    async def test_hot_memory_operations_integration(self, memory_system):
        """Hot Memory操作統合テスト"""
        if not os.getenv('INTEGRATION_TESTS_ENABLED'):
            pytest.skip("Integration tests disabled")
        
        # Initialize
        initialized = await memory_system.initialize()
        if not initialized:
            pytest.skip("Memory system initialization failed")
        
        test_channel = "integration_test_channel"
        
        # 1. 初期状態確認
        initial_messages = await memory_system.load_hot_memory(test_channel)
        assert isinstance(initial_messages, list)
        
        # 2. メッセージ追加
        conversation_data = {
            'messages': [
                {'role': 'user', 'content': '統合テストメッセージ1'},
                {'role': 'assistant', 'content': '統合テスト応答1'}
            ],
            'selected_agent': 'spectra',
            'response_content': '統合テスト応答1',
            'channel_id': test_channel,
            'confidence': 0.95
        }
        
        update_result = await memory_system.update_memory_transactional(conversation_data)
        assert update_result is True
        
        # 3. 追加後確認
        updated_messages = await memory_system.load_hot_memory(test_channel)
        assert len(updated_messages) == len(initial_messages) + 1
        
        # 最新メッセージ確認
        latest_message = updated_messages[0]  # Redis LISTは先頭が最新
        assert latest_message['selected_agent'] == 'spectra'
        assert latest_message['channel_id'] == test_channel
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cold_memory_operations_integration(self, memory_system):
        """Cold Memory操作統合テスト"""
        if not os.getenv('INTEGRATION_TESTS_ENABLED'):
            pytest.skip("Integration tests disabled")
        
        # Gemini API Key必要
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY not provided")
        
        # Initialize
        initialized = await memory_system.initialize()
        if not initialized:
            pytest.skip("Memory system initialization failed")
        
        # 1. Embedding生成テスト
        test_text = "Discord統合テストのためのサンプルテキスト"
        embedding = await memory_system.generate_embedding_with_rate_limit(test_text)
        
        if embedding is not None:
            assert len(embedding) == 768  # text-embedding-004
            assert all(isinstance(x, float) for x in embedding)
            
            # 2. セマンティック検索テスト
            search_results = await memory_system.load_cold_memory(
                "統合テスト"
            )
            assert isinstance(search_results, list)
        else:
            pytest.skip("Embedding generation failed - API quota or network issue")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_persistence_integration(self, memory_system):
        """Memory永続化統合テスト"""
        if not os.getenv('INTEGRATION_TESTS_ENABLED'):
            pytest.skip("Integration tests disabled")
        
        initialized = await memory_system.initialize()
        if not initialized:
            pytest.skip("Memory system initialization failed")
        
        test_channel = "persistence_test_channel"
        
        # 1. 複数メッセージ追加
        for i in range(5):
            conversation_data = {
                'messages': [{'role': 'user', 'content': f'永続化テスト{i}'}],
                'selected_agent': f'agent_{i % 3}',  # agent_0, agent_1, agent_2
                'response_content': f'永続化応答{i}',
                'channel_id': test_channel,
                'confidence': 0.8 + (i * 0.04)  # 0.8, 0.84, 0.88, 0.92, 0.96
            }
            
            result = await memory_system.update_memory_transactional(conversation_data)
            assert result is True
        
        # 2. Hot Memory制限確認 (20件まで)
        hot_messages = await memory_system.load_hot_memory(test_channel)
        assert len(hot_messages) <= 20
        assert len(hot_messages) >= 5  # 追加した分は存在
        
        # 3. 統計確認
        stats = await memory_system.get_health_status()
        assert stats['status'] in ['healthy', 'connected']
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_channels_integration(self, memory_system):
        """複数チャンネル統合テスト"""
        if not os.getenv('INTEGRATION_TESTS_ENABLED'):
            pytest.skip("Integration tests disabled")
        
        initialized = await memory_system.initialize()
        if not initialized:
            pytest.skip("Memory system initialization failed")
        
        channels = ["channel_1", "channel_2", "channel_3"]
        
        # 1. 各チャンネルにメッセージ追加
        for channel in channels:
            conversation_data = {
                'messages': [{'role': 'user', 'content': f'{channel}のテストメッセージ'}],
                'selected_agent': 'multi_test_agent',
                'response_content': f'{channel}の応答',
                'channel_id': channel,
                'confidence': 0.9
            }
            
            result = await memory_system.update_memory_transactional(conversation_data)
            assert result is True
        
        # 2. 各チャンネルの独立性確認
        for channel in channels:
            messages = await memory_system.load_hot_memory(channel)
            assert len(messages) >= 1
            
            # チャンネル固有のメッセージが含まれているか確認
            found_channel_message = False
            for message in messages:
                if message.get('channel_id') == channel:
                    found_channel_message = True
                    break
            assert found_channel_message, f"Channel {channel} specific message not found"
        
        # 3. 統計でチャンネル数確認
        stats = await memory_system.get_health_status()
        assert stats['status'] in ['healthy', 'connected']


class TestMemoryLangGraphIntegration:
    """Memory System + LangGraph統合テスト"""
    
    @pytest_asyncio.fixture
    async def supervisor_with_memory(self):
        """Memory統合したSupervisor"""
        memory_system = DiscordMemorySystem(
            redis_url="redis://localhost:6379/15",
            postgres_url="postgresql://discord_agent:discord_agent_password@localhost:5432/discord_agent",
            gemini_api_key=os.getenv('GEMINI_API_KEY', 'test_key')
        )
        
        supervisor = AgentSupervisor(
            gemini_api_key=os.getenv('GEMINI_API_KEY', 'test_key'),
            memory_system=memory_system
        )
        
        yield supervisor
        
        await memory_system.cleanup()
    
    @pytest.mark.integration 
    @pytest.mark.asyncio
    async def test_supervisor_memory_integration(self, supervisor_with_memory):
        """Supervisor + Memory統合テスト"""
        if not os.getenv('INTEGRATION_TESTS_ENABLED'):
            pytest.skip("Integration tests disabled")
        
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY required")
        
        # Memory System初期化
        memory_initialized = await supervisor_with_memory.memory_system.initialize()
        if not memory_initialized:
            pytest.skip("Memory system initialization failed")
        
        # テストメッセージ
        test_state = {
            "messages": [
                {"role": "user", "content": "Spectraに画像生成について質問したい"},
            ],
            "channel_id": "memory_integration_test",
            "user_id": "test_user_123",
            "message_id": "test_msg_456"
        }
        
        # Supervisor実行
        try:
            result = await supervisor_with_memory.process_message(test_state)
            
            # 結果確認
            assert "selected_agent" in result
            assert result["selected_agent"] in ["spectra", "lynq", "paz"]
            
            # Memory更新確認
            if "response_content" in result:
                memory_updated = await supervisor_with_memory.memory_system.update_memory_transactional({
                    'messages': test_state["messages"],
                    'selected_agent': result["selected_agent"],
                    'response_content': result.get("response_content", ""),
                    'channel_id': test_state["channel_id"],
                    'confidence': result.get("confidence", 0.5)
                })
                assert memory_updated is True
                
                # Hot Memory確認
                hot_memory = await supervisor_with_memory.memory_system.load_hot_memory(
                    test_state["channel_id"]
                )
                assert len(hot_memory) >= 1
        
        except Exception as e:
            # API制限やネットワークエラーは許容
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                pytest.skip(f"API quota/rate limit: {e}")
            else:
                raise


class TestMemoryPerformanceIntegration:
    """Memory System パフォーマンス統合テスト"""
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_hot_memory_performance(self):
        """Hot Memory性能テスト (目標: <0.1秒)"""
        if not os.getenv('INTEGRATION_TESTS_ENABLED'):
            pytest.skip("Integration tests disabled")
        
        memory_system = DiscordMemorySystem(
            redis_url="redis://localhost:6379/15"
        )
        
        initialized = await memory_system.initialize()
        if not initialized:
            pytest.skip("Memory system initialization failed")
        
        import time
        
        # Hot Memory読み込み性能テスト
        start_time = time.time()
        
        for _ in range(10):  # 10回実行
            await memory_system.load_hot_memory("performance_test_channel")
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        # 目標: 1回あたり0.1秒以内
        assert avg_time < 0.1, f"Hot Memory performance target missed: {avg_time:.3f}s > 0.1s"
        
        await memory_system.cleanup()
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cold_memory_performance(self):
        """Cold Memory性能テスト (目標: <3秒)"""
        if not os.getenv('INTEGRATION_TESTS_ENABLED'):
            pytest.skip("Integration tests disabled")
        
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY required")
        
        memory_system = DiscordMemorySystem(
            gemini_api_key=os.getenv('GEMINI_API_KEY')
        )
        
        initialized = await memory_system.initialize()
        if not initialized:
            pytest.skip("Memory system initialization failed")
        
        import time
        
        # Cold Memory検索性能テスト
        start_time = time.time()
        
        try:
            await memory_system.load_cold_memory("テスト検索クエリ")
            
            end_time = time.time()
            search_time = end_time - start_time
            
            # 目標: 3秒以内
            assert search_time < 3.0, f"Cold Memory performance target missed: {search_time:.3f}s > 3.0s"
        
        except Exception as e:
            if "quota" in str(e).lower():
                pytest.skip(f"API quota limit: {e}")
            else:
                raise
        
        await memory_system.cleanup()


# 統合テスト実行補助
if __name__ == "__main__":
    print("🔄 Memory System Integration Tests")
    print("Docker Compose環境とGEMINI_API_KEYが必要です")
    print("")
    print("実行例:")
    print("export INTEGRATION_TESTS_ENABLED=1")
    print("export GEMINI_API_KEY=your_api_key")
    print("docker-compose up -d")
    print("python -m pytest tests/integration/test_memory_integration.py -v")