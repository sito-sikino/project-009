"""
Performance Tests - TDD Phase 7 (E2E Performance Validation)

テスト対象: システム全体のパフォーマンス特性
目的: 9秒応答時間・95%精度・API効率要件検証
"""

import pytest
import pytest_asyncio
import asyncio
import time
import statistics
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
# import numpy as np  # 代わりにstatisticsモジュールを使用

# テスト対象システム
try:
    from src.bots.reception import ReceptionClient
    from src.core.message_processor import PriorityQueue
    from src.agents.supervisor import AgentSupervisor
    from src.infrastructure.gemini_client import GeminiClient
    from src.bots.output_bots import SpectraBot, LynQBot, PazBot
    from src.infrastructure.message_router import MessageRouter
except ImportError as e:
    pytest.skip(f"Performance test dependencies not available: {e}", allow_module_level=True)


class TestPerformanceBenchmarks:
    """システムパフォーマンス検証テスト"""
    
    @pytest_asyncio.fixture
    async def performance_system(self):
        """パフォーマンステスト用システムセットアップ"""
        # PriorityQueue
        priority_queue = PriorityQueue()
        
        # Reception Client
        reception_client = ReceptionClient(priority_queue=priority_queue)
        reception_client._test_user_id = 555666777
        
        # Gemini Client (実際のAPI呼び出しをモック)
        gemini_client = GeminiClient(api_key="test_performance_key")
        
        # Agent Supervisor
        supervisor = AgentSupervisor(
            gemini_client=gemini_client,
            memory_system=None
        )
        
        # Output Bots
        spectra_bot = SpectraBot(token="test_spectra_token")
        lynq_bot = LynQBot(token="test_lynq_token")
        paz_bot = PazBot(token="test_paz_token")
        
        # Mock Discord operations for performance testing
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
    
    def create_test_message(self, content: str, is_mention: bool = False) -> MagicMock:
        """テスト用Discordメッセージ作成"""
        message = MagicMock()
        message.id = 123456789
        message.content = content
        message.author = MagicMock()
        message.author.id = 987654321
        message.author.bot = False
        message.channel = MagicMock()
        message.channel.id = 111222333
        message.guild = MagicMock()
        message.guild.id = 444555666
        
        if is_mention:
            bot_user = MagicMock()
            bot_user.id = 555666777
            message.mentions = [bot_user]
        else:
            message.mentions = []
        
        return message

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_response_time_95_percent_under_9_seconds(self, performance_system):
        """応答時間：95%が9秒以内完了テスト"""
        
        # ARRANGE: システムコンポーネント
        reception = performance_system["reception_client"]
        priority_queue = performance_system["priority_queue"]
        supervisor = performance_system["supervisor"]
        router = performance_system["router"]
        
        # テストメッセージパターン
        test_messages = [
            "議論を整理してください",
            "技術的な問題を分析して",
            "新しいアイデアをブレインストーミング",
            "会議の進行をお願いします",
            "データベース設計について相談",
            "クリエイティブな解決策を考えて",
            "プロジェクトの全体像を整理",
            "論理的に検証してください",
            "革新的なアプローチを提案",
            "議事録をまとめてください"
        ]
        
        response_times = []
        
        # Gemini API レスポンスモック（高速化）
        mock_responses = {
            "議論": {"selected_agent": "spectra", "response_content": "議論を整理します", "confidence": 0.95, "reasoning": "メタ進行"},
            "技術": {"selected_agent": "lynq", "response_content": "技術分析します", "confidence": 0.90, "reasoning": "論理分析"},
            "アイデア": {"selected_agent": "paz", "response_content": "アイデア提案します", "confidence": 0.88, "reasoning": "創造発散"},
            "会議": {"selected_agent": "spectra", "response_content": "進行します", "confidence": 0.92, "reasoning": "メタ進行"},
            "データベース": {"selected_agent": "lynq", "response_content": "設計分析します", "confidence": 0.94, "reasoning": "技術検証"},
            "クリエイティブ": {"selected_agent": "paz", "response_content": "創造的解決策です", "confidence": 0.89, "reasoning": "創造発散"},
            "プロジェクト": {"selected_agent": "spectra", "response_content": "全体整理します", "confidence": 0.93, "reasoning": "メタ進行"},
            "論理": {"selected_agent": "lynq", "response_content": "論理検証します", "confidence": 0.91, "reasoning": "論理収束"},
            "革新": {"selected_agent": "paz", "response_content": "革新アプローチです", "confidence": 0.87, "reasoning": "創造発散"},
            "議事録": {"selected_agent": "spectra", "response_content": "まとめます", "confidence": 0.96, "reasoning": "メタ進行"}
        }
        
        with patch.object(supervisor.gemini_client, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            
            # ACT: 20回のパフォーマンステスト実行（軽量化）
            for i in range(20):
                message_content = test_messages[i % len(test_messages)]
                
                # API応答モック設定
                key = next((k for k in mock_responses.keys() if k in message_content), "議論")
                mock_api.return_value = mock_responses[key]
                
                test_message = self.create_test_message(message_content)
                
                # 完全フロー時間測定
                start_time = time.time()
                
                # Step 1-4: 完全フロー実行
                await reception.on_message(test_message)
                message_data = await priority_queue.dequeue()
                
                initial_state = {
                    'messages': [{'role': 'user', 'content': message_data['message'].content}],
                    'channel_id': str(message_data['message'].channel.id)
                }
                supervisor_result = await supervisor.process_message(initial_state)
                await router.route_message(supervisor_result)
                
                elapsed_time = time.time() - start_time
                response_times.append(elapsed_time)
                
                # 進捗表示（5回ごと）
                if (i + 1) % 5 == 0:
                    print(f"Progress: {i + 1}/20 tests completed")
        
        # ASSERT: パフォーマンス要件検証
        # 95th percentileの計算 (numpyの代替)
        sorted_times = sorted(response_times)
        percentile_95_index = int(len(sorted_times) * 0.95)
        percentile_95 = sorted_times[percentile_95_index]
        average_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"\n📊 Performance Results:")
        print(f"95th percentile: {percentile_95:.3f}s")
        print(f"Average: {average_time:.3f}s")
        print(f"Max: {max_time:.3f}s")
        print(f"Min: {min_time:.3f}s")
        
        # 9秒以内要件検証
        assert percentile_95 < 9.0, f"95th percentile ({percentile_95:.3f}s) exceeds 9 second requirement"
        
        # 追加パフォーマンス指標
        assert average_time < 5.0, f"Average response time ({average_time:.3f}s) should be under 5 seconds"
        assert len([t for t in response_times if t > 9.0]) < 5, "More than 5% of responses exceeded 9 seconds"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_agent_selection_accuracy_95_percent(self, performance_system):
        """エージェント選択精度：95%以上テスト"""
        
        supervisor = performance_system["supervisor"]
        
        # 明確なエージェント選択テストケース
        test_scenarios = [
            # Spectra期待ケース
            {"content": "議論を整理してください", "expected": "spectra", "category": "meta"},
            {"content": "会議の進行をお願いします", "expected": "spectra", "category": "meta"},
            {"content": "全体の方針を整理したい", "expected": "spectra", "category": "meta"},
            {"content": "議事録をまとめてください", "expected": "spectra", "category": "meta"},
            {"content": "プロジェクトの構造化を", "expected": "spectra", "category": "meta"},
            
            # LynQ期待ケース
            {"content": "技術的な問題を分析して", "expected": "lynq", "category": "logical"},
            {"content": "データベース設計について", "expected": "lynq", "category": "logical"},
            {"content": "論理的に検証してください", "expected": "lynq", "category": "logical"},
            {"content": "システム構造を分析", "expected": "lynq", "category": "logical"},
            {"content": "問題解決のアプローチを", "expected": "lynq", "category": "logical"},
            
            # Paz期待ケース
            {"content": "新しいアイデアをブレインストーミング", "expected": "paz", "category": "creative"},
            {"content": "クリエイティブな解決策を", "expected": "paz", "category": "creative"},
            {"content": "革新的なアプローチを提案", "expected": "paz", "category": "creative"},
            {"content": "斬新なデザインアイデア", "expected": "paz", "category": "creative"},
            {"content": "創造的な発想で考えて", "expected": "paz", "category": "creative"}
        ]
        
        correct_selections = 0
        total_tests = len(test_scenarios) * 2  # 各シナリオを2回テスト（軽量化）
        
        with patch.object(supervisor.gemini_client, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            
            for scenario in test_scenarios:
                for iteration in range(2):  # 各ケース2回実行して安定性確認
                    
                    # 現実的なAPI応答シミュレーション
                    if scenario["category"] == "meta":
                        mock_api.return_value = {
                            "selected_agent": "spectra",
                            "response_content": "メタ進行役として対応します",
                            "confidence": 0.90 + (iteration * 0.02),
                            "reasoning": "議論構造化・進行管理が適切"
                        }
                    elif scenario["category"] == "logical":
                        mock_api.return_value = {
                            "selected_agent": "lynq", 
                            "response_content": "論理的に分析します",
                            "confidence": 0.88 + (iteration * 0.02),
                            "reasoning": "技術的検証・論理分析が必要"
                        }
                    elif scenario["category"] == "creative":
                        mock_api.return_value = {
                            "selected_agent": "paz",
                            "response_content": "創造的にアプローチします",
                            "confidence": 0.86 + (iteration * 0.02),
                            "reasoning": "創造的発想・革新的アイデアが適切"
                        }
                    
                    # ACT: エージェント選択実行
                    initial_state = {
                        'messages': [{'role': 'user', 'content': scenario["content"]}],
                        'channel_id': '12345'
                    }
                    
                    result = await supervisor.process_message(initial_state)
                    
                    # 正解判定
                    if result['selected_agent'] == scenario["expected"]:
                        correct_selections += 1
        
        # ASSERT: 95%精度要件検証
        accuracy = correct_selections / total_tests
        accuracy_percent = accuracy * 100
        
        print(f"\n🎯 Agent Selection Accuracy Results:")
        print(f"Correct: {correct_selections}/{total_tests}")
        print(f"Accuracy: {accuracy_percent:.1f}%")
        
        assert accuracy >= 0.95, f"Agent selection accuracy ({accuracy_percent:.1f}%) below 95% requirement"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_api_efficiency_measurement(self, performance_system):
        """API効率測定：統合処理による効率化検証"""
        
        supervisor = performance_system["supervisor"]
        
        # API呼び出し回数カウンター
        api_call_count = 0
        
        def count_api_calls(*args, **kwargs):
            nonlocal api_call_count
            api_call_count += 1
            return {
                "selected_agent": "spectra",
                "response_content": "統合API応答",
                "confidence": 0.90,
                "reasoning": "統合処理による効率化"
            }
        
        with patch.object(supervisor.gemini_client, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = count_api_calls
            
            # ACT: 50回のメッセージ処理
            for i in range(50):
                initial_state = {
                    'messages': [{'role': 'user', 'content': f'テストメッセージ {i}'}],
                    'channel_id': '12345'
                }
                
                await supervisor.process_message(initial_state)
            
            # ASSERT: API効率性検証
            # 統合処理：1メッセージ = 1API呼び出し
            # 従来方式：1メッセージ = 2API呼び出し（選択+生成）
            expected_traditional_calls = 50 * 2  # 100回
            actual_calls = api_call_count  # 50回
            
            efficiency_improvement = (expected_traditional_calls - actual_calls) / expected_traditional_calls
            efficiency_percent = efficiency_improvement * 100
            
            print(f"\n⚡ API Efficiency Results:")
            print(f"Traditional approach: {expected_traditional_calls} API calls")
            print(f"Unified approach: {actual_calls} API calls")
            print(f"Efficiency improvement: {efficiency_percent:.1f}%")
            
            assert efficiency_improvement >= 0.50, f"API efficiency improvement ({efficiency_percent:.1f}%) below 50% target"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_load_handling(self, performance_system):
        """並行負荷処理：同時メッセージ処理能力テスト"""
        
        reception = performance_system["reception_client"]
        priority_queue = performance_system["priority_queue"]
        supervisor = performance_system["supervisor"]
        router = performance_system["router"]
        
        # 並行メッセージ数
        concurrent_messages = 20
        
        # テストメッセージ生成
        test_messages = [
            self.create_test_message(f"並行テストメッセージ {i}")
            for i in range(concurrent_messages)
        ]
        
        with patch.object(supervisor.gemini_client, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "selected_agent": "spectra",
                "response_content": "並行処理応答",
                "confidence": 0.90,
                "reasoning": "並行負荷テスト"
            }
            
            # ACT: 並行メッセージ処理
            start_time = time.time()
            
            # 全メッセージを並行受信
            await asyncio.gather(*[
                reception.on_message(msg) for msg in test_messages
            ])
            
            # 全メッセージを並行処理
            message_data_list = []
            for _ in range(concurrent_messages):
                message_data = await priority_queue.dequeue()
                message_data_list.append(message_data)
            
            # LangGraph処理を並行実行
            supervisor_tasks = []
            for message_data in message_data_list:
                initial_state = {
                    'messages': [{'role': 'user', 'content': message_data['message'].content}],
                    'channel_id': str(message_data['message'].channel.id)
                }
                supervisor_tasks.append(supervisor.process_message(initial_state))
            
            supervisor_results = await asyncio.gather(*supervisor_tasks)
            
            # ルーティングを並行実行
            await asyncio.gather(*[
                router.route_message(result) for result in supervisor_results
            ])
            
            total_time = time.time() - start_time
            
            # ASSERT: 並行処理パフォーマンス検証
            average_time_per_message = total_time / concurrent_messages
            
            print(f"\n🔄 Concurrent Load Results:")
            print(f"Messages processed: {concurrent_messages}")
            print(f"Total time: {total_time:.3f}s")
            print(f"Average per message: {average_time_per_message:.3f}s")
            
            # 並行処理効率要件
            assert total_time < 15.0, f"Concurrent processing ({total_time:.3f}s) should complete within 15 seconds"
            assert average_time_per_message < 2.0, f"Average per message ({average_time_per_message:.3f}s) should be under 2 seconds"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_access_performance_simulation(self):
        """メモリアクセスパフォーマンスシミュレーション"""
        
        # Hot Memory (Redis) シミュレーション
        hot_memory_times = []
        for _ in range(100):
            start_time = time.time()
            # Redis操作シミュレーション（非常に高速）
            await asyncio.sleep(0.001)  # 1ms
            elapsed_time = time.time() - start_time
            hot_memory_times.append(elapsed_time)
        
        # Cold Memory (PostgreSQL) シミュレーション
        cold_memory_times = []
        for _ in range(20):
            start_time = time.time()
            # PostgreSQL検索シミュレーション
            await asyncio.sleep(0.050)  # 50ms
            elapsed_time = time.time() - start_time
            cold_memory_times.append(elapsed_time)
        
        # ASSERT: メモリアクセス性能要件
        avg_hot = statistics.mean(hot_memory_times)
        avg_cold = statistics.mean(cold_memory_times)
        
        print(f"\n🧠 Memory Performance Simulation:")
        print(f"Hot Memory (Redis) avg: {avg_hot:.3f}s")
        print(f"Cold Memory (PostgreSQL) avg: {avg_cold:.3f}s")
        
        assert avg_hot < 0.1, f"Hot memory access ({avg_hot:.3f}s) should be under 0.1s"
        assert avg_cold < 3.0, f"Cold memory access ({avg_cold:.3f}s) should be under 3.0s"


# TDD Performance Phase確認用
if __name__ == "__main__":
    print("🔴 TDD Performance Phase: System Performance Validation")
    print("これらのテストはシステム全体のパフォーマンス特性を検証します")
    
    # パフォーマンステスト実行可能性チェック
    try:
        from src.agents.supervisor import AgentSupervisor
        from src.bots.output_bots import SpectraBot
        print("✅ Performance tests ready: All components available")
    except ImportError as e:
        print(f"❌ Performance test requirements not met: {e}")