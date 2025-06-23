#!/usr/bin/env python3
"""
v0.3.0 Long-term Memory System Integration Tests
長期記憶システム統合テスト
"""

import pytest
import asyncio
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

# テスト対象インポート
from src.infrastructure.long_term_memory import LongTermMemoryProcessor, ProcessedMemory
from src.infrastructure.deduplication_system import MinHashDeduplicator, MemoryItem
from src.core.daily_report_system import (
    DailyReportGenerator, 
    IntegratedMessageSystem, 
    EventDrivenWorkflowOrchestrator
)


class TestLongTermMemoryProcessor:
    """長期記憶処理システムのテスト"""
    
    @pytest.fixture
    def processor(self):
        """LongTermMemoryProcessorのテストフィクスチャ"""
        return LongTermMemoryProcessor(
            redis_url="redis://localhost:6379",
            postgres_url="postgresql://test:test@localhost:5432/test_db",
            gemini_api_key="test_api_key"
        )
    
    @pytest.fixture
    def sample_redis_memories(self):
        """サンプルRedis記憶データ"""
        return [
            {
                "id": str(uuid.uuid4()),
                "content": "TypeScriptでReactアプリケーションを開発しています",
                "timestamp": datetime.now().isoformat(),
                "channel_id": "123456789",
                "user_id": "user001",
                "metadata": {"type": "development"}
            },
            {
                "id": str(uuid.uuid4()),
                "content": "転職活動の進捗を報告します",
                "timestamp": datetime.now().isoformat(),
                "channel_id": "123456789",
                "user_id": "user002",
                "metadata": {"type": "personal"}
            },
            {
                "id": str(uuid.uuid4()),
                "content": "新しいプロジェクトのアイデアを考えています",
                "timestamp": datetime.now().isoformat(),
                "channel_id": "987654321",
                "user_id": "user003",
                "metadata": {"type": "creation"}
            }
        ]
    
    @pytest.mark.asyncio
    async def test_api_quota_check(self, processor):
        """API使用量制限チェックテスト"""
        target_date = datetime.now()
        
        # 初回チェック（制限内）
        assert processor._check_api_quota(target_date) == True
        
        # API使用量を3回に設定
        processor.api_usage_count = 3
        processor.last_processing_date = target_date.date()
        
        # 制限超過チェック
        assert processor._check_api_quota(target_date) == False
        
        # 新しい日になった場合のリセット
        next_day = target_date + timedelta(days=1)
        assert processor._check_api_quota(next_day) == True
        assert processor.api_usage_count == 0
    
    @pytest.mark.asyncio
    @patch('src.infrastructure.long_term_memory.redis.from_url')
    async def test_fetch_daily_memories(self, mock_redis, processor, sample_redis_memories):
        """Redis記憶データ取得テスト"""
        # Redisクライアントモック
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        # Redisキー検索結果モック
        mock_redis_client.keys.return_value = [
            b"memory:2024-01-15:msg001",
            b"memory:2024-01-15:msg002"
        ]
        
        # データ取得結果モック
        mock_redis_client.hgetall.side_effect = [
            {b"id": b"test001", b"content": b"test content 1"},
            {b"id": b"test002", b"content": b"test content 2"}
        ]
        
        target_date = datetime(2024, 1, 15)
        memories = await processor._fetch_daily_memories(target_date)
        
        assert len(memories) == 2
        assert memories[0]["id"] == "test001"
        assert memories[1]["content"] == "test content 2"
        
        # Redisクライアントのクローズ確認
        mock_redis_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.infrastructure.long_term_memory.GoogleGenerativeAI')
    async def test_api1_unified_analysis(self, mock_gemini, processor, sample_redis_memories):
        """API 1: Gemini統合分析テスト"""
        # Gemini応答モック
        mock_response = """
        [
          {
            "id": "test001",
            "structured_content": "TypeScript React開発",
            "memory_type": "learning",
            "entities": [{"name": "TypeScript", "type": "technology"}],
            "importance_score": 0.8,
            "progress_indicators": {"skill_development": "TypeScript"}
          }
        ]
        """
        
        mock_gemini_instance = AsyncMock()
        mock_gemini_instance.ainvoke.return_value = mock_response
        processor.gemini_flash = mock_gemini_instance
        
        processed = await processor._api1_unified_analysis(sample_redis_memories)
        
        assert len(processed) == 1
        assert processed[0].structured_content == "TypeScript React開発"
        assert processed[0].importance_score == 0.8
        assert len(processed[0].entities) == 1
        assert processed[0].entities[0]["name"] == "TypeScript"
        
        # Gemini呼び出し確認
        mock_gemini_instance.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.infrastructure.long_term_memory.GoogleGenerativeAIEmbeddings')
    async def test_api3_batch_embeddings(self, mock_embeddings, processor):
        """API 3: バッチembedding生成テスト"""
        # サンプル処理済み記憶
        memories = [
            ProcessedMemory(
                id="test001",
                original_content="test content",
                structured_content="structured test",
                timestamp=datetime.now(),
                channel_id=123,
                user_id="user001",
                memory_type="conversation",
                entities=[],
                importance_score=0.7,
                progress_indicators={},
                metadata={}
            )
        ]
        
        # Embedding結果モック
        mock_embeddings_instance = AsyncMock()
        mock_embeddings_instance.aembed_documents.return_value = [
            [0.1, 0.2, 0.3, 0.4]  # 4次元テストembedding
        ]
        processor.embeddings_client = mock_embeddings_instance
        
        result = await processor._api3_batch_embeddings(memories)
        
        assert len(result) == 1
        assert result[0].embedding == [0.1, 0.2, 0.3, 0.4]
        
        # Embedding API呼び出し確認
        mock_embeddings_instance.aembed_documents.assert_called_once_with(["structured test"])


class TestMinHashDeduplicator:
    """重複検出システムのテスト"""
    
    @pytest.fixture
    def deduplicator(self):
        """MinHashDeduplicatorのテストフィクスチャ"""
        return MinHashDeduplicator(threshold=0.8, num_perm=64)
    
    def test_content_normalization(self):
        """コンテンツ正規化テスト"""
        from src.infrastructure.deduplication_system import ContentNormalizer
        
        # URL、メンション、記号の除去テスト
        original = "Hello @user123! Check https://example.com for more info!!!"
        normalized = ContentNormalizer.normalize_text(original)
        
        assert "https://example.com" not in normalized
        assert "@user123" not in normalized
        assert normalized.lower() == normalized  # 小文字化確認
    
    def test_memory_deduplication(self, deduplicator):
        """記憶重複除去テスト"""
        # 類似した記憶アイテム
        memory1 = MemoryItem(
            id="mem001",
            content="TypeScriptでReactアプリを開発しています",
            timestamp=datetime.now(),
            channel_id=123,
            user_id="user001",
            memory_type="conversation",
            metadata={}
        )
        
        memory2 = MemoryItem(
            id="mem002", 
            content="ReactアプリをTypeScriptで開発中です",
            timestamp=datetime.now(),
            channel_id=123,
            user_id="user001",
            memory_type="conversation",
            metadata={}
        )
        
        memory3 = MemoryItem(
            id="mem003",
            content="Pythonでバックエンド実装をしています",
            timestamp=datetime.now(),
            channel_id=456,
            user_id="user002",
            memory_type="task",
            metadata={}
        )
        
        # バッチ重複除去実行
        unique_memories = deduplicator.batch_deduplicate([memory1, memory2, memory3])
        
        # 類似記憶（memory1, memory2）は1つに重複除去されることを期待
        assert len(unique_memories) <= 2
        assert any(mem.id == memory3.id for mem in unique_memories)  # memory3は残存
    
    def test_similarity_calculation(self, deduplicator):
        """類似度計算テスト"""
        memory1 = MemoryItem(
            id="mem001",
            content="同じ内容です",
            timestamp=datetime.now(),
            channel_id=123,
            user_id="user001",
            memory_type="conversation", 
            metadata={}
        )
        
        memory2 = MemoryItem(
            id="mem002",
            content="同じ内容です",
            timestamp=datetime.now(),
            channel_id=123,
            user_id="user001",
            memory_type="conversation",
            metadata={}
        )
        
        # 記憶追加
        deduplicator.add_memory(memory1)
        deduplicator.add_memory(memory2)
        
        # 類似度計算
        similarity = deduplicator.get_similarity("mem001", "mem002")
        
        # 完全一致なので高い類似度
        assert similarity > 0.8


class TestDailyReportSystem:
    """日報システムのテスト"""
    
    @pytest.fixture
    def report_generator(self):
        """DailyReportGeneratorのテストフィクスチャ"""
        return DailyReportGenerator()
    
    @pytest.fixture
    def sample_processed_memories(self):
        """サンプル処理済み記憶"""
        return [
            ProcessedMemory(
                id="mem001",
                original_content="TypeScript学習中",
                structured_content="TypeScript技術習得",
                timestamp=datetime.now(),
                channel_id=123,
                user_id="user001",
                memory_type="learning",
                entities=[{"name": "TypeScript", "type": "technology"}],
                importance_score=0.8,
                progress_indicators={"skill_development": "TypeScript"},
                metadata={}
            ),
            ProcessedMemory(
                id="mem002",
                original_content="新しいデザインアイデア",
                structured_content="UIデザイン企画",
                timestamp=datetime.now(),
                channel_id=456,
                user_id="user002",
                memory_type="progress",
                entities=[{"name": "UIデザイン", "type": "creative"}],
                importance_score=0.7,
                progress_indicators={"project_advancement": "デザイン企画"},
                metadata={}
            )
        ]
    
    def test_daily_report_generation(self, report_generator, sample_processed_memories):
        """日報生成テスト"""
        from src.infrastructure.long_term_memory import ProgressDifferential
        
        progress_diff = ProgressDifferential(
            date=datetime.now(),
            new_entities=["TypeScript"],
            progressed_entities=["UIデザイン"],
            stagnant_entities=[],
            completed_tasks=[],
            new_skills=["TypeScript"],
            overall_summary="技術学習と創作活動が進展"
        )
        
        processing_stats = {
            "processing_time": 8.5,
            "memory_count": 2,
            "api_usage": 3
        }
        
        daily_report = report_generator.generate_daily_report(
            sample_processed_memories, progress_diff, processing_stats
        )
        
        assert daily_report.date.date() == datetime.now().date()
        assert len(daily_report.departments) == 3  # Command Center, Creation, Development
        assert daily_report.processing_stats["memory_count"] == 2
        assert "技術学習" in daily_report.overall_summary or "進展" in daily_report.overall_summary
    
    @pytest.mark.asyncio
    async def test_integrated_message_system(self):
        """統合メッセージシステムテスト"""
        # モックボット作成
        mock_spectra_bot = MagicMock()
        mock_channel = AsyncMock()
        mock_spectra_bot.get_channel.return_value = mock_channel
        
        output_bots = {"spectra": mock_spectra_bot}
        message_system = IntegratedMessageSystem(output_bots)
        
        # サンプル日報
        from src.core.daily_report_system import DailyReport, DepartmentReport
        sample_report = DailyReport(
            date=datetime.now(),
            departments=[
                DepartmentReport(
                    name="Development",
                    emoji="🗃️",
                    themes=["TypeScript"],
                    details=["技術習得中"],
                    progress_score=0.8
                )
            ],
            overall_summary="開発活動が活発",
            processing_stats={"processing_time": 5.0}
        )
        
        # 統合メッセージ送信テスト
        success = await message_system.send_integrated_morning_message(
            sample_report, 123456789
        )
        
        # 送信成功確認
        assert success == True
        mock_channel.send.assert_called_once()
        
        # 送信内容確認
        call_args = mock_channel.send.call_args
        assert "Morning Meeting" in call_args.kwargs['content']
        assert call_args.kwargs['embed'] is not None


class TestEventDrivenWorkflow:
    """イベントドリブンワークフロー統合テスト"""
    
    @pytest.mark.asyncio
    async def test_morning_workflow_orchestration(self):
        """統合朝次ワークフロー統括テスト"""
        # モックコンポーネント
        mock_long_term_processor = AsyncMock()
        mock_report_generator = MagicMock()
        mock_message_system = AsyncMock()
        
        # ワークフロー統括システム
        orchestrator = EventDrivenWorkflowOrchestrator(
            long_term_memory_processor=mock_long_term_processor,
            daily_report_generator=mock_report_generator,
            integrated_message_system=mock_message_system,
            command_center_channel_id=123456789
        )
        
        # 長期記憶処理結果モック
        mock_memories = [MagicMock()]
        mock_progress_diff = MagicMock()
        mock_long_term_processor.daily_memory_consolidation.return_value = (mock_memories, mock_progress_diff)
        
        # 日報生成結果モック
        mock_daily_report = MagicMock()
        mock_report_generator.generate_daily_report.return_value = mock_daily_report
        
        # 統合メッセージ送信成功モック
        mock_message_system.send_integrated_morning_message.return_value = True
        
        # ワークフロー実行
        success = await orchestrator.execute_morning_workflow()
        
        # 実行結果確認
        assert success == True
        
        # 各ステップの実行確認
        mock_long_term_processor.daily_memory_consolidation.assert_called_once()
        mock_report_generator.generate_daily_report.assert_called_once()
        mock_message_system.send_integrated_morning_message.assert_called_once()


# テスト設定
@pytest.fixture(scope="session")
def event_loop():
    """テスト用イベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])