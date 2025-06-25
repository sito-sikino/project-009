"""
Reception Client Unit Tests - TDD Phase 2 (Red Phase)

テスト対象: Discord統合受信専用クライアント
目的: メッセージ受信、優先度判定、キューイング機能の検証
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import discord

# テスト対象をインポート（まだ存在しないため失敗する）
try:
    from src.bots.reception import ReceptionClient
    from src.core.message_processor import PriorityQueue
except ImportError:
    # TDD Red Phase: 実装前なのでインポートエラーは期待通り
    ReceptionClient = None
    PriorityQueue = None


class TestReceptionClient:
    """Reception Client単体テスト"""
    
    @pytest.fixture
    def mock_priority_queue(self):
        """優先度キューのモック"""
        queue = AsyncMock()
        queue.enqueue = AsyncMock()
        return queue
    
    @pytest.fixture
    def mock_message(self):
        """Discordメッセージのモック"""
        message = MagicMock()
        message.author.bot = False
        message.author.id = 123456789
        message.content = "テストメッセージ"
        message.channel.id = 987654321
        message.mentions = []
        return message
    
    @pytest.fixture
    def mock_mention_message(self):
        """メンション付きメッセージのモック"""
        message = MagicMock()
        message.author.bot = False
        message.author.id = 123456789
        message.content = "@Spectra こんにちは"
        message.channel.id = 987654321
        message.mentions = [MagicMock()]  # メンション対象
        return message

    def test_reception_client_initialization(self, mock_priority_queue):
        """Reception Client初期化テスト"""
        # ARRANGE & ACT: Reception Client作成
        client = ReceptionClient(priority_queue=mock_priority_queue)
        
        # ASSERT: 正常に初期化されること
        assert client.priority_queue == mock_priority_queue
        assert client.intents.message_content is True
        assert client.intents.guilds is True

    @pytest.mark.asyncio
    async def test_on_message_normal_priority(self, mock_priority_queue, mock_message):
        """通常メッセージの優先度判定テスト"""
        # ARRANGE: Reception Clientのセットアップ（実装前なので失敗予定）
        if ReceptionClient is None:
            pytest.skip("ReceptionClient not implemented yet - TDD Red Phase")
        
        client = ReceptionClient(priority_queue=mock_priority_queue)
        
        # ACT: 通常メッセージ処理
        await client.on_message(mock_message)
        
        # ASSERT: 通常優先度でキューに追加
        mock_priority_queue.enqueue.assert_called_once()
        call_args = mock_priority_queue.enqueue.call_args[0][0]
        assert call_args['priority'] == 2  # 通常優先度
        assert call_args['message'] == mock_message

    @pytest.mark.asyncio
    async def test_on_message_mention_high_priority(self, mock_priority_queue, mock_mention_message):
        """メンション付きメッセージの高優先度テスト"""
        # ARRANGE: Reception Clientのセットアップ（実装前なので失敗予定）
        if ReceptionClient is None:
            pytest.skip("ReceptionClient not implemented yet - TDD Red Phase")
        
        client = ReceptionClient(priority_queue=mock_priority_queue)
        
        # ACT: メンション付きメッセージ処理
        await client.on_message(mock_mention_message)
        
        # ASSERT: 高優先度でキューに追加
        mock_priority_queue.enqueue.assert_called_once()
        call_args = mock_priority_queue.enqueue.call_args[0][0]
        assert call_args['priority'] == 1  # 高優先度（メンション）
        assert call_args['message'] == mock_mention_message

    @pytest.mark.asyncio
    async def test_ignore_bot_messages(self, mock_priority_queue):
        """Bot自身のメッセージ無視テスト"""
        # ARRANGE: Botメッセージのモック
        bot_message = MagicMock()
        bot_message.author.bot = True
        
        if ReceptionClient is None:
            pytest.skip("ReceptionClient not implemented yet - TDD Red Phase")
        
        client = ReceptionClient(priority_queue=mock_priority_queue)
        
        # ACT: Botメッセージ処理
        await client.on_message(bot_message)
        
        # ASSERT: キューに追加されない
        mock_priority_queue.enqueue.assert_not_called()

    def test_determine_priority_logic(self, mock_priority_queue):
        """優先度判定ロジックテスト"""
        client = ReceptionClient(priority_queue=mock_priority_queue)
        
        # テストケース
        test_cases = [
            # (メンション有無, 期待優先度, 説明)
            (True, 1, "メンション付きは最高優先度"),
            (False, 2, "通常メッセージは標準優先度"),
        ]
        
        for has_mentions, expected_priority, description in test_cases:
            mock_msg = MagicMock()
            mock_msg.mentions = [MagicMock()] if has_mentions else []
            
            # ACT: 優先度判定
            priority = client._determine_priority(mock_msg)
            
            # ASSERT: 期待される優先度
            assert priority == expected_priority, description


class TestPriorityQueue:
    """Priority Queue単体テスト"""
    
    @pytest.mark.asyncio
    async def test_priority_queue_initialization(self):
        """Priority Queue初期化テスト"""
        # ACT: PriorityQueue作成
        queue = PriorityQueue()
        
        # ASSERT: 正常に初期化されること
        assert hasattr(queue, 'enqueue')
        assert hasattr(queue, 'dequeue')
        assert queue.is_empty() is True
        assert queue.size() == 0

    @pytest.mark.asyncio
    async def test_priority_queue_enqueue_dequeue(self):
        """優先度キュー基本操作テスト"""
        if PriorityQueue is None:
            pytest.skip("PriorityQueue not implemented yet - TDD Red Phase")
        
        queue = PriorityQueue()
        
        # ARRANGE: テストメッセージ
        high_priority_msg = {
            'priority': 1,
            'message': 'high priority',
            'timestamp': '2025-06-20T10:00:00'
        }
        low_priority_msg = {
            'priority': 2,
            'message': 'low priority', 
            'timestamp': '2025-06-20T10:01:00'
        }
        
        # ACT: 低優先度→高優先度の順で追加
        await queue.enqueue(low_priority_msg)
        await queue.enqueue(high_priority_msg)
        
        # ASSERT: 高優先度が先に取得される
        first_msg = await queue.dequeue()
        second_msg = await queue.dequeue()
        
        assert first_msg['priority'] == 1, "高優先度メッセージが先に処理される"
        assert second_msg['priority'] == 2, "低優先度メッセージが後に処理される"


# TDD Red Phase確認用のテスト実行
if __name__ == "__main__":
    print("🔴 TDD Red Phase: 失敗するテストを確認")
    print("これらのテストは実装前なので失敗することが期待されます")
    
    # 基本的なインポートテスト
    try:
        from src.bots.reception import ReceptionClient
        print("❌ 予期しない成功: ReceptionClientが既に存在")
    except ImportError:
        print("✅ 期待通りの失敗: ReceptionClientはまだ実装されていません")
    
    try:
        from src.core.message_processor import PriorityQueue
        print("❌ 予期しない成功: PriorityQueueが既に存在")
    except ImportError:
        print("✅ 期待通りの失敗: PriorityQueueはまだ実装されていません")