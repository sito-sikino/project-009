"""
Complete Message Flow Integration Tests - TDD Phase 6 (Red Phase)

テスト対象: Reception→LangGraph→OutputBots 完全統合フロー
目的: システム全体のエンドツーエンド動作検証
"""

import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import discord

# テスト対象をインポート（統合テストなので実装済みコンポーネント）
try:
    from src.discord_clients import ReceptionClient
    from src.message_processor import PriorityQueue
    from src.langgraph_supervisor import AgentSupervisor
    from src.gemini_client import GeminiClient
    from src.output_bots import SpectraBot, LynQBot, PazBot
    from src.message_router import MessageRouter
except ImportError as e:
    # 統合テスト用に未実装コンポーネントをスキップ
    pytest.skip(f"Integration test dependencies not available: {e}", allow_module_level=True)


class TestCompleteMessageFlow:
    """完全メッセージフロー統合テスト"""
    
    @pytest.fixture
    def mock_discord_message(self):
        """Discord メッセージモック"""
        message = MagicMock()
        message.id = 123456789
        message.content = "こんにちは、議論を整理してもらえますか？"
        message.author = MagicMock()
        message.author.id = 987654321
        message.author.bot = False
        message.channel = MagicMock()
        message.channel.id = 111222333
        message.mentions = []
        message.guild = MagicMock()
        message.guild.id = 444555666
        return message
    
    @pytest.fixture
    def mock_mention_message(self):
        """@メンション Discord メッセージモック"""
        message = MagicMock()
        message.id = 987654321
        message.content = "@Spectra 今日の会議の議論を整理してください"
        message.author = MagicMock()
        message.author.id = 123456789
        message.author.bot = False
        message.channel = MagicMock()
        message.channel.id = 111222333
        
        # Bot mention - matching the test user ID
        bot_user = MagicMock()
        bot_user.id = 555666777  # Reception bot ID
        message.mentions = [bot_user]
        message.guild = MagicMock()
        message.guild.id = 444555666
        return message
    
    @pytest_asyncio.fixture
    async def integrated_system(self):
        """統合システムセットアップ"""
        # PriorityQueue
        priority_queue = PriorityQueue()
        
        # Reception Client with mocked user
        reception_client = ReceptionClient(priority_queue=priority_queue)
        # Store user ID directly for mention detection
        reception_client._test_user_id = 555666777
        
        # Gemini Client (Mock)
        gemini_client = GeminiClient(api_key="test_key")
        
        # Agent Supervisor
        supervisor = AgentSupervisor(
            gemini_client=gemini_client,
            memory_system=None  # Mock or None for tests
        )
        
        # Output Bots
        spectra_bot = SpectraBot(token="test_spectra_token")
        lynq_bot = LynQBot(token="test_lynq_token")
        paz_bot = PazBot(token="test_paz_token")
        
        # Mock Discord sending
        for bot in [spectra_bot, lynq_bot, paz_bot]:
            bot.get_channel = MagicMock()
            bot.get_channel.return_value = MagicMock()
            bot.get_channel.return_value.send = AsyncMock()
        
        # Message Router
        bots = {
            "spectra": spectra_bot,
            "lynq": lynq_bot,
            "paz": paz_bot
        }
        router = MessageRouter(bots=bots)
        
        return {
            "reception_client": reception_client,
            "priority_queue": priority_queue,
            "supervisor": supervisor,
            "gemini_client": gemini_client,
            "router": router,
            "bots": bots
        }

    @pytest.mark.asyncio
    async def test_complete_mention_flow_under_9_seconds(self, integrated_system, mock_mention_message):
        """@メンション完全フロー：9秒以内完了テスト"""
        # ARRANGE: システムコンポーネント取得
        reception = integrated_system["reception_client"]
        priority_queue = integrated_system["priority_queue"]
        supervisor = integrated_system["supervisor"]
        router = integrated_system["router"]
        
        # Gemini API レスポンスモック
        with patch.object(supervisor.gemini_client, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                'selected_agent': 'spectra',
                'response_content': '議論を整理させていただきます。まず要点を確認しましょう。',
                'confidence': 0.95,
                'reasoning': 'メタ進行役として議論整理が適切'
            }
            
            # ACT: 完全フロー実行（時間測定）
            start_time = time.time()
            
            # Step 1: Reception Client がメッセージ受信
            await reception.on_message(mock_mention_message)
            
            # Step 2: Priority Queue からメッセージ取得
            message_data = await priority_queue.dequeue()
            priority = message_data['priority']
            discord_message = message_data['message']
            
            # Step 3: LangGraph Supervisor で処理
            initial_state = {
                'messages': [{'role': 'user', 'content': discord_message.content}],
                'channel_id': str(discord_message.channel.id)
            }
            supervisor_result = await supervisor.process_message(initial_state)
            
            # Step 4: Message Router で適切なBotに配信
            await router.route_message(supervisor_result)
            
            elapsed_time = time.time() - start_time
            
            # ASSERT: 9秒以内完了
            assert elapsed_time < 9.0
            
            # ASSERT: 正しい優先度（メンション = priority 1）
            assert priority == 1
            
            # ASSERT: Spectraが選択された
            assert supervisor_result['selected_agent'] == 'spectra'
            
            # ASSERT: Spectra Bot が実際に送信された
            spectra_bot = integrated_system["bots"]["spectra"]
            spectra_bot.get_channel.assert_called_once_with(111222333)
            spectra_bot.get_channel.return_value.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_normal_message_flow_agent_selection(self, integrated_system, mock_discord_message):
        """通常メッセージフロー：エージェント選択テスト"""
        # ARRANGE: システムコンポーネント
        reception = integrated_system["reception_client"]
        priority_queue = integrated_system["priority_queue"]
        supervisor = integrated_system["supervisor"]
        router = integrated_system["router"]
        
        # Test scenarios: 異なる内容 → 異なるエージェント
        test_scenarios = [
            {
                "content": "新しいアイデアをブレインストーミングしたい",
                "expected_agent": "paz",
                "reasoning": "創造的テーマなのでPazが適切"
            },
            {
                "content": "この技術的な問題を分析して解決策を教えて",
                "expected_agent": "lynq",
                "reasoning": "論理的分析が必要なのでLynQが適切"
            },
            {
                "content": "今日の議題を整理して議論の進行をお願いします",
                "expected_agent": "spectra",
                "reasoning": "メタ進行役としてSpectraが適切"
            }
        ]
        
        for scenario in test_scenarios:
            # メッセージ内容を変更
            mock_discord_message.content = scenario["content"]
            
            # Gemini API レスポンスモック
            with patch.object(supervisor.gemini_client, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = {
                    'selected_agent': scenario["expected_agent"],
                    'response_content': f'{scenario["expected_agent"]}としての応答です。',
                    'confidence': 0.90,
                    'reasoning': scenario["reasoning"]
                }
                
                # ACT: フロー実行
                await reception.on_message(mock_discord_message)
                message_data = await priority_queue.dequeue()
                priority = message_data['priority']
                discord_message = message_data['message']
                
                initial_state = {
                    'messages': [{'role': 'user', 'content': discord_message.content}],
                    'channel_id': str(discord_message.channel.id)
                }
                supervisor_result = await supervisor.process_message(initial_state)
                
                # ASSERT: 期待されるエージェントが選択された
                assert supervisor_result['selected_agent'] == scenario["expected_agent"]
                assert priority == 2  # 通常メッセージ priority

    @pytest.mark.asyncio
    async def test_error_handling_fallback_flow(self, integrated_system, mock_discord_message):
        """エラーハンドリング：フォールバック動作テスト"""
        # ARRANGE: システムコンポーネント
        reception = integrated_system["reception_client"]
        priority_queue = integrated_system["priority_queue"]
        supervisor = integrated_system["supervisor"]
        router = integrated_system["router"]
        
        # Gemini API エラーシミュレーション
        with patch.object(supervisor.gemini_client, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("Gemini API Error")
            
            # ACT: エラー発生時のフロー
            await reception.on_message(mock_discord_message)
            message_data = await priority_queue.dequeue()
            discord_message = message_data['message']
            
            initial_state = {
                'messages': [{'role': 'user', 'content': discord_message.content}],
                'channel_id': str(discord_message.channel.id)
            }
            supervisor_result = await supervisor.process_message(initial_state)
            await router.route_message(supervisor_result)
            
            # ASSERT: Spectraにフォールバック
            assert supervisor_result['selected_agent'] == 'spectra'
            
            # ASSERT: エラーメッセージが含まれる
            assert '処理中にエラーが発生しました' in supervisor_result['response_content']
            
            # ASSERT: Spectra Bot が呼ばれた
            spectra_bot = integrated_system["bots"]["spectra"]
            spectra_bot.get_channel.return_value.send.assert_called()

    @pytest.mark.asyncio
    async def test_priority_queue_ordering_integration(self, integrated_system):
        """優先度キュー：統合順序テスト"""
        # ARRANGE: システムコンポーネント
        reception = integrated_system["reception_client"]
        priority_queue = integrated_system["priority_queue"]
        
        # 異なる優先度のメッセージ作成
        normal_msg = MagicMock()
        normal_msg.id = 111
        normal_msg.content = "通常メッセージ"
        normal_msg.author.bot = False
        normal_msg.channel.id = 123
        normal_msg.mentions = []
        
        mention_msg = MagicMock()
        mention_msg.id = 222
        mention_msg.content = "@Bot メンションメッセージ"
        mention_msg.author.bot = False
        mention_msg.channel.id = 123
        mention_msg.mentions = [MagicMock(id=555666777)]  # Use test bot ID
        
        # ACT: 逆順で投入（通常→メンション）
        await reception.on_message(normal_msg)
        await reception.on_message(mention_msg)
        
        # ASSERT: メンションが先に取得される（priority 1 < 2）
        first_data = await priority_queue.dequeue()
        second_data = await priority_queue.dequeue()
        
        assert first_data['priority'] == 1  # mention
        assert second_data['priority'] == 2  # normal
        assert first_data['message'].id == 222  # mention message
        assert second_data['message'].id == 111  # normal message

    @pytest.mark.asyncio
    async def test_parallel_output_bots_no_conflicts(self, integrated_system):
        """並行OutputBots：競合なしテスト"""
        # ARRANGE: 複数メッセージ同時処理
        router = integrated_system["router"]
        
        messages = [
            {
                'selected_agent': 'spectra',
                'response_content': 'Spectraメッセージ',
                'channel_id': '111',
                'confidence': 0.9
            },
            {
                'selected_agent': 'lynq',
                'response_content': 'LynQメッセージ',
                'channel_id': '222',
                'confidence': 0.9
            },
            {
                'selected_agent': 'paz',
                'response_content': 'Pazメッセージ',
                'channel_id': '333',
                'confidence': 0.9
            }
        ]
        
        # ACT: 並行ルーティング
        tasks = [router.route_message(msg) for msg in messages]
        await asyncio.gather(*tasks)
        
        # ASSERT: 各Botが正確に1回呼ばれた
        bots = integrated_system["bots"]
        bots["spectra"].get_channel.assert_called_once_with(111)
        bots["lynq"].get_channel.assert_called_once_with(222)
        bots["paz"].get_channel.assert_called_once_with(333)


class TestSystemResilience:
    """システム耐障害性統合テスト"""
    
    @pytest_asyncio.fixture
    async def integrated_system(self):
        """統合システムセットアップ（SystemResilience用）"""
        # PriorityQueue
        priority_queue = PriorityQueue()
        
        # Reception Client with mocked user
        reception_client = ReceptionClient(priority_queue=priority_queue)
        # Store user ID directly for mention detection
        reception_client._test_user_id = 555666777
        
        # Gemini Client (Mock)
        gemini_client = GeminiClient(api_key="test_key")
        
        # Agent Supervisor
        supervisor = AgentSupervisor(
            gemini_client=gemini_client,
            memory_system=None  # Mock or None for tests
        )
        
        # Output Bots
        spectra_bot = SpectraBot(token="test_spectra_token")
        lynq_bot = LynQBot(token="test_lynq_token")
        paz_bot = PazBot(token="test_paz_token")
        
        # Mock Discord sending
        for bot in [spectra_bot, lynq_bot, paz_bot]:
            bot.get_channel = MagicMock()
            bot.get_channel.return_value = MagicMock()
            bot.get_channel.return_value.send = AsyncMock()
        
        # Message Router
        bots = {
            "spectra": spectra_bot,
            "lynq": lynq_bot,
            "paz": paz_bot
        }
        router = MessageRouter(bots=bots)
        
        return {
            "reception_client": reception_client,
            "priority_queue": priority_queue,
            "supervisor": supervisor,
            "gemini_client": gemini_client,
            "router": router,
            "bots": bots
        }
    
    @pytest.mark.asyncio
    async def test_component_failure_isolation(self, integrated_system):
        """コンポーネント障害分離テスト"""
        # ARRANGE: 一部コンポーネント障害シミュレーション
        router = integrated_system["router"]
        
        # 1つのBotを障害状態に
        faulty_bot = integrated_system["bots"]["lynq"]
        faulty_bot.send_message = AsyncMock(side_effect=Exception("Bot offline"))
        
        # ACT: 障害Botへのメッセージ送信試行
        faulty_message = {
            'selected_agent': 'lynq',
            'response_content': 'テストメッセージ',
            'channel_id': '123',
            'confidence': 0.9
        }
        
        # 障害が発生しても例外が伝播しないことを確認
        try:
            await router.route_message(faulty_message)
            # フォールバック動作確認
            spectra_bot = integrated_system["bots"]["spectra"]
            # Fallback logic would call Spectra
        except Exception as e:
            pytest.fail(f"System should handle component failures gracefully: {e}")

    @pytest.mark.asyncio
    async def test_memory_system_integration_placeholder(self):
        """メモリシステム統合テスト（プレースホルダー）"""
        # TODO: Memory System実装後に詳細テスト追加
        # - Hot Memory (Redis) 読み込み
        # - Cold Memory (PostgreSQL) セマンティック検索
        # - Memory統合による文脈保持
        pytest.skip("Memory system integration pending implementation")

    @pytest.mark.asyncio
    async def test_rate_limiting_system_integration(self):
        """レート制限システム統合テスト"""
        # TODO: Gemini API制限統合テスト
        # - 15RPM制限遵守
        # - キュー処理における制限考慮
        # - エラー時のバックオフ戦略
        pytest.skip("Rate limiting integration testing pending")


# TDD Red Phase確認用のテスト実行
if __name__ == "__main__":
    print("🔴 TDD Red Phase: Complete Message Flow Integration Tests")
    print("これらのテストは統合実装の検証を行います")
    
    # 基本的な統合可能性チェック
    try:
        from src.discord_clients import ReceptionClient
        from src.langgraph_supervisor import AgentSupervisor
        from src.output_bots import SpectraBot
        from src.message_router import MessageRouter
        print("✅ 統合テスト実行可能: 全コンポーネント利用可能")
    except ImportError as e:
        print(f"❌ 統合テスト要件不足: {e}")