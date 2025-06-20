"""
Output Bots Unit Tests - TDD Phase 5 (Red Phase)

テスト対象: 個別送信Bot(Spectra/LynQ/Paz) + MessageRouter
目的: 統合受信→個別送信アーキテクチャの送信部分検証
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import discord

# テスト対象をインポート（まだ存在しないため失敗する）
try:
    from src.output_bots import OutputBot, SpectraBot, LynQBot, PazBot
    from src.message_router import MessageRouter
except ImportError:
    # TDD Red Phase: 実装前なのでインポートエラーは期待通り
    OutputBot = None
    SpectraBot = None
    LynQBot = None
    PazBot = None
    MessageRouter = None


class TestOutputBot:
    """OutputBot基本クラステスト"""
    
    @pytest.fixture
    def mock_discord_channel(self):
        """Discord Channel モック"""
        channel = AsyncMock()
        channel.send = AsyncMock()
        channel.id = 12345
        return channel
    
    @pytest.fixture
    def sample_message_data(self):
        """サンプルメッセージデータ"""
        return {
            'content': 'こんにちは！',
            'channel_id': '12345',
            'selected_agent': 'spectra',
            'confidence': 0.95,
            'original_user': 'test_user',
            'timestamp': '2025-06-20T10:00:00Z'
        }

    def test_output_bot_initialization(self):
        """OutputBot基本クラス初期化テスト"""
        if OutputBot is None:
            pytest.skip("OutputBot not implemented yet - TDD Red Phase")
        
        # ACT: OutputBot作成
        bot = OutputBot(
            token="test_token",
            bot_name="test_bot",
            personality="テスト用Bot"
        )
        
        # ASSERT: 正常に初期化されること
        assert bot.bot_name == "test_bot"
        assert bot.personality == "テスト用Bot"
        assert hasattr(bot, 'send_message')

    @pytest.mark.asyncio
    async def test_output_bot_send_message(self, mock_discord_channel, sample_message_data):
        """OutputBot メッセージ送信テスト"""
        if OutputBot is None:
            pytest.skip("OutputBot not implemented yet - TDD Red Phase")
        
        bot = OutputBot(
            token="test_token",
            bot_name="test_bot",
            personality="テスト用Bot"
        )
        
        # Mock get_channel
        bot.get_channel = MagicMock(return_value=mock_discord_channel)
        
        # ACT: メッセージ送信
        await bot.send_message(sample_message_data)
        
        # ASSERT: Discord send が呼ばれること
        mock_discord_channel.send.assert_called_once_with('こんにちは！')

    def test_output_bot_personality_validation(self):
        """OutputBot パーソナリティ検証テスト"""
        if OutputBot is None:
            pytest.skip("OutputBot not implemented yet - TDD Red Phase")
        
        # ACT & ASSERT: パーソナリティが設定されること
        bot = OutputBot(
            token="test_token",
            bot_name="spectra",
            personality="メタ進行役・議論構造化"
        )
        
        assert "メタ進行役" in bot.personality
        assert bot.bot_name == "spectra"


class TestSpecificBots:
    """個別Bot（Spectra/LynQ/Paz）テスト"""
    
    def test_spectra_bot_initialization(self):
        """SpectraBot初期化テスト"""
        if SpectraBot is None:
            pytest.skip("SpectraBot not implemented yet - TDD Red Phase")
        
        # ACT: SpectraBot作成
        bot = SpectraBot(token="test_token")
        
        # ASSERT: Spectra特性が設定されること
        assert bot.bot_name == "spectra"
        assert "メタ進行役" in bot.personality
        assert "議論の構造化" in bot.personality

    def test_lynq_bot_initialization(self):
        """LynQBot初期化テスト"""
        if LynQBot is None:
            pytest.skip("LynQBot not implemented yet - TDD Red Phase")
        
        # ACT: LynQBot作成
        bot = LynQBot(token="test_token")
        
        # ASSERT: LynQ特性が設定されること
        assert bot.bot_name == "lynq"
        assert "論理収束役" in bot.personality
        assert "技術的検証" in bot.personality

    def test_paz_bot_initialization(self):
        """PazBot初期化テスト"""
        if PazBot is None:
            pytest.skip("PazBot not implemented yet - TDD Red Phase")
        
        # ACT: PazBot作成
        bot = PazBot(token="test_token")
        
        # ASSERT: Paz特性が設定されること
        assert bot.bot_name == "paz"
        assert "発散創造役" in bot.personality
        assert "革新的アイデア" in bot.personality


class TestMessageRouter:
    """MessageRouter統合テスト"""
    
    @pytest.fixture
    def mock_bots(self):
        """3つのBotのモック"""
        spectra = AsyncMock()
        spectra.bot_name = "spectra"
        spectra.send_message = AsyncMock()
        
        lynq = AsyncMock()
        lynq.bot_name = "lynq"
        lynq.send_message = AsyncMock()
        
        paz = AsyncMock()
        paz.bot_name = "paz"
        paz.send_message = AsyncMock()
        
        return {"spectra": spectra, "lynq": lynq, "paz": paz}
    
    @pytest.fixture
    def sample_routing_data(self):
        """ルーティング用サンプルデータ"""
        return {
            'selected_agent': 'lynq',
            'response_content': '論理的に分析すると...',
            'channel_id': '12345',
            'confidence': 0.88,
            'original_user': 'test_user'
        }

    def test_message_router_initialization(self, mock_bots):
        """MessageRouter初期化テスト"""
        if MessageRouter is None:
            pytest.skip("MessageRouter not implemented yet - TDD Red Phase")
        
        # ACT: MessageRouter作成
        router = MessageRouter(bots=mock_bots)
        
        # ASSERT: 正常に初期化されること
        assert len(router.bots) == 3
        assert "spectra" in router.bots
        assert "lynq" in router.bots
        assert "paz" in router.bots

    @pytest.mark.asyncio
    async def test_message_routing_to_specific_agent(self, mock_bots, sample_routing_data):
        """特定エージェントへのルーティングテスト"""
        if MessageRouter is None:
            pytest.skip("MessageRouter not implemented yet - TDD Red Phase")
        
        router = MessageRouter(bots=mock_bots)
        
        # ACT: LynQへのルーティング
        await router.route_message(sample_routing_data)
        
        # ASSERT: 正しいBotが呼ばれること（MessageRouterが変換するデータ構造で検証）
        expected_call_data = {
            'content': '論理的に分析すると...',
            'channel_id': '12345',
            'original_user': 'test_user',
            'confidence': 0.88,
            'selected_agent': 'lynq'
        }
        mock_bots["lynq"].send_message.assert_called_once_with(expected_call_data)
        mock_bots["spectra"].send_message.assert_not_called()
        mock_bots["paz"].send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_message_routing_fallback_to_spectra(self, mock_bots):
        """不明エージェントのSpectraフォールバックテスト"""
        if MessageRouter is None:
            pytest.skip("MessageRouter not implemented yet - TDD Red Phase")
        
        router = MessageRouter(bots=mock_bots)
        
        # ARRANGE: 不明エージェント指定
        invalid_data = {
            'selected_agent': 'unknown_agent',
            'response_content': 'フォールバックテスト',
            'channel_id': '12345'
        }
        
        # ACT: 不明エージェントでルーティング
        await router.route_message(invalid_data)
        
        # ASSERT: Spectraにフォールバックすること
        mock_bots["spectra"].send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_message_routing(self, mock_bots):
        """並行メッセージルーティングテスト"""
        if MessageRouter is None:
            pytest.skip("MessageRouter not implemented yet - TDD Red Phase")
        
        router = MessageRouter(bots=mock_bots)
        
        # ARRANGE: 複数メッセージ
        messages = [
            {'selected_agent': 'spectra', 'response_content': 'Message 1', 'channel_id': '1'},
            {'selected_agent': 'lynq', 'response_content': 'Message 2', 'channel_id': '2'},
            {'selected_agent': 'paz', 'response_content': 'Message 3', 'channel_id': '3'}
        ]
        
        # ACT: 並行ルーティング
        await asyncio.gather(*[router.route_message(msg) for msg in messages])
        
        # ASSERT: 各Botが1回ずつ呼ばれること
        mock_bots["spectra"].send_message.assert_called_once()
        mock_bots["lynq"].send_message.assert_called_once()
        mock_bots["paz"].send_message.assert_called_once()

    def test_bot_availability_check(self, mock_bots):
        """Bot可用性チェックテスト"""
        if MessageRouter is None:
            pytest.skip("MessageRouter not implemented yet - TDD Red Phase")
        
        router = MessageRouter(bots=mock_bots)
        
        # ACT & ASSERT: 各Botが利用可能であること
        assert router.is_bot_available("spectra") is True
        assert router.is_bot_available("lynq") is True
        assert router.is_bot_available("paz") is True
        assert router.is_bot_available("unknown") is False


class TestOutputBotsIntegration:
    """Output Bots統合テスト"""
    
    @pytest.mark.asyncio
    async def test_full_output_flow_integration(self):
        """完全な出力フロー統合テスト"""
        if None in [OutputBot, MessageRouter, SpectraBot]:
            pytest.skip("Output components not implemented yet - TDD Red Phase")
        
        # ARRANGE: 実際のBot作成（テスト用トークン）
        spectra = SpectraBot(token="test_spectra_token")
        lynq = LynQBot(token="test_lynq_token")
        paz = PazBot(token="test_paz_token")
        
        bots = {"spectra": spectra, "lynq": lynq, "paz": paz}
        router = MessageRouter(bots=bots)
        
        # Mock Discord send
        for bot in bots.values():
            bot.get_channel = MagicMock()
            bot.get_channel.return_value.send = AsyncMock()
        
        # ARRANGE: LangGraphからの出力データ
        langgraph_output = {
            'selected_agent': 'paz',
            'response_content': '創造的なアイデアを提案します！',
            'channel_id': '12345',
            'confidence': 0.92
        }
        
        # ACT: 統合フロー実行
        await router.route_message(langgraph_output)
        
        # ASSERT: Pazが正しく呼ばれること（channel_idはintに変換される）
        paz.get_channel.assert_called_once_with(12345)


# TDD Red Phase確認用のテスト実行
if __name__ == "__main__":
    print("🔴 TDD Red Phase: Output Bots失敗するテストを確認")
    print("これらのテストは実装前なので失敗することが期待されます")
    
    # 基本的なインポートテスト
    try:
        from src.output_bots import OutputBot
        print("❌ 予期しない成功: OutputBotが既に存在")
    except ImportError:
        print("✅ 期待通りの失敗: OutputBotはまだ実装されていません")
    
    try:
        from src.message_router import MessageRouter
        print("❌ 予期しない成功: MessageRouterが既に存在")
    except ImportError:
        print("✅ 期待通りの失敗: MessageRouterはまだ実装されていません")