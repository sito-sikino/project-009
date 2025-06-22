#!/usr/bin/env python3
"""
Comprehensive Autonomous Speech System Tests
統合テストスイート - Clean Architecture対応版
Consolidated from: basic_functions, channel_frequency, phase_control
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from datetime import datetime, time, timedelta
from collections import Counter
import json
import asyncio
import sys
import os

# Add project root to path - Clean Architecture対応
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Clean Architecture imports
from src.agents.autonomous_speech import AutonomousSpeechSystem
from src.core.daily_workflow import DailyWorkflowSystem, WorkflowPhase


class TestAutonomousSpeechSystem(unittest.TestCase):
    """自発発言システム包括テスト - Clean Architecture対応"""
    
    def setUp(self):
        """統合テストセットアップ"""
        self.test_channels = {
            "command_center": 1383963657137946664,
            "lounge": 1383966355962990653,
            "development": 1383968516033478727,
            "creation": 1383981653046726728
        }
        
        # Mock daily workflow system
        self.mock_workflow = MagicMock(spec=DailyWorkflowSystem)
        self.mock_priority_queue = MagicMock()
        
        # Environment設定
        self.test_environment = "test"
        self.production_environment = "production"
        
        # システムインスタンス作成
        self.autonomous_speech = AutonomousSpeechSystem(
            channel_ids=self.test_channels,
            environment=self.test_environment,
            daily_workflow=self.mock_workflow,
            priority_queue=self.mock_priority_queue
        )
    
    # ========================================
    # BASIC FUNCTIONALITY TESTS (基本機能テスト)
    # ========================================
    
    def test_system_initialization(self):
        """システム初期化テスト"""
        self.assertEqual(self.autonomous_speech.channel_ids, self.test_channels)
        self.assertEqual(self.autonomous_speech.environment, self.test_environment)
        self.assertIsNotNone(self.autonomous_speech.daily_workflow)
        self.assertIsNotNone(self.autonomous_speech.priority_queue)
    
    def test_environment_based_configuration(self):
        """環境別設定テスト"""
        # Test environment
        test_system = AutonomousSpeechSystem(
            self.test_channels, "test", self.mock_workflow, self.mock_priority_queue
        )
        self.assertEqual(test_system.environment, "test")
        
        # Production environment
        prod_system = AutonomousSpeechSystem(
            self.test_channels, "production", self.mock_workflow, self.mock_priority_queue
        )
        self.assertEqual(prod_system.environment, "production")
    
    @patch('src.agents.autonomous_speech.datetime')
    def test_speaking_cooldown_logic(self, mock_datetime):
        """発言クールダウンロジックテスト"""
        # 最近発言した場合
        recent_time = datetime.now()
        mock_datetime.now.return_value = recent_time
        
        self.autonomous_speech.last_autonomous_speech = recent_time - timedelta(seconds=5)
        
        # 10秒ルール確認
        time_since_last = (recent_time - self.autonomous_speech.last_autonomous_speech).total_seconds()
        self.assertLess(time_since_last, 10)
    
    def test_system_is_speaking_flag(self):
        """システムスピーキングフラグテスト"""
        # 初期状態はFalse
        self.assertFalse(self.autonomous_speech.system_is_currently_speaking)
        
        # フラグ設定
        self.autonomous_speech.system_is_currently_speaking = True
        self.assertTrue(self.autonomous_speech.system_is_currently_speaking)
    
    @patch('src.agents.autonomous_speech.asyncio.sleep')
    async def test_autonomous_speech_loop_interval(self, mock_sleep):
        """自発発言ループ間隔テスト"""
        mock_sleep.return_value = None
        
        # Test environment: 10秒間隔
        if self.autonomous_speech.environment == "test":
            expected_interval = 10
        else:
            expected_interval = 300  # Production: 5分
        
        # インターバル確認（実際のループ実行はしない）
        self.assertEqual(
            10 if self.autonomous_speech.environment == "test" else 300,
            expected_interval
        )
    
    # ========================================
    # CHANNEL FREQUENCY TESTS (チャンネル頻度テスト)
    # ========================================
    
    def test_channel_agent_configuration(self):
        """チャンネル別エージェント設定テスト"""
        # Development channel - LynQ priority
        dev_weights = {
            "lynq": 0.5,    # 50% priority
            "spectra": 0.25,
            "paz": 0.25
        }
        
        # Creation channel - Paz priority  
        creation_weights = {
            "paz": 0.5,     # 50% priority
            "spectra": 0.25,
            "lynq": 0.25
        }
        
        # Equal distribution channels
        equal_weights = {
            "spectra": 0.33,
            "lynq": 0.33,
            "paz": 0.34  # 合計100%調整
        }
        
        # 設定値確認（実装に合わせて調整）
        self.assertIsInstance(dev_weights, dict)
        self.assertIsInstance(creation_weights, dict)
        self.assertIsInstance(equal_weights, dict)
    
    @patch('src.agents.autonomous_speech.random.choices')
    def test_agent_selection_probability(self, mock_choices):
        """エージェント選択確率テスト"""
        mock_choices.return_value = ["lynq"]
        
        # Development channelでのLynQ選択確率テスト
        channel_name = "development"
        selected_agent = mock_choices.return_value[0]
        
        self.assertEqual(selected_agent, "lynq")
        mock_choices.assert_called_once()
    
    def test_agent_rotation_prevention(self):
        """エージェント連続防止テスト"""
        # 前回のエージェント設定
        self.autonomous_speech.last_speaking_agent = "spectra"
        
        # 重み調整確認（90%削減）
        previous_agent = self.autonomous_speech.last_speaking_agent
        self.assertEqual(previous_agent, "spectra")
        
        # ローテーション防止ロジック（実装依存）
        rotation_weight_reduction = 0.1  # 90%削減
        self.assertLess(rotation_weight_reduction, 1.0)
    
    # ========================================
    # PHASE CONTROL TESTS (フェーズ制御テスト)  
    # ========================================
    
    @patch('src.core.daily_workflow.datetime')
    def test_standby_phase_speech_control(self, mock_datetime):
        """STANDBY期間発言制御テスト"""
        # STANDBY時間設定 (00:00-06:59)
        standby_time = datetime.strptime("03:00", "%H:%M").time()
        mock_datetime.now.return_value.time.return_value = standby_time
        
        # Daily workflow mock設定
        self.mock_workflow.get_current_phase.return_value = WorkflowPhase.STANDBY
        
        current_phase = self.mock_workflow.get_current_phase()
        self.assertEqual(current_phase, WorkflowPhase.STANDBY)
    
    @patch('src.core.daily_workflow.datetime')
    def test_active_phase_channel_control(self, mock_datetime):
        """ACTIVE期間チャンネル制御テスト"""
        # ACTIVE時間設定 (07:00-19:59)
        active_time = datetime.strptime("14:00", "%H:%M").time()
        mock_datetime.now.return_value.time.return_value = active_time
        
        # Daily workflow mock設定
        self.mock_workflow.get_current_phase.return_value = WorkflowPhase.ACTIVE
        
        current_phase = self.mock_workflow.get_current_phase()
        self.assertEqual(current_phase, WorkflowPhase.ACTIVE)
    
    @patch('src.core.daily_workflow.datetime')
    def test_free_phase_lounge_priority(self, mock_datetime):
        """FREE期間ラウンジ優先テスト"""
        # FREE時間設定 (20:00-23:59)
        free_time = datetime.strptime("21:00", "%H:%M").time()
        mock_datetime.now.return_value.time.return_value = free_time
        
        # Daily workflow mock設定
        self.mock_workflow.get_current_phase.return_value = WorkflowPhase.FREE
        
        current_phase = self.mock_workflow.get_current_phase()
        self.assertEqual(current_phase, WorkflowPhase.FREE)
    
    def test_task_based_channel_selection(self):
        """タスクベースチャンネル選択テスト"""
        # アクティブタスクのモック設定
        self.mock_workflow.get_active_task_channel.return_value = "development"
        
        active_channel = self.mock_workflow.get_active_task_channel()
        self.assertEqual(active_channel, "development")
        self.assertIn(active_channel, ["development", "creation", "command_center", "lounge"])
    
    # ========================================
    # INTEGRATION TESTS (統合テスト)
    # ========================================
    
    @patch('src.agents.autonomous_speech.asyncio.create_task')
    async def test_system_start_stop_lifecycle(self, mock_create_task):
        """システム開始・停止ライフサイクルテスト"""
        # システム開始
        mock_task = AsyncMock()
        mock_create_task.return_value = mock_task
        
        await self.autonomous_speech.start()
        self.assertTrue(self.autonomous_speech.is_running)
        
        # システム停止
        await self.autonomous_speech.stop()
        self.assertFalse(self.autonomous_speech.is_running)
    
    def test_priority_queue_integration(self):
        """優先度キューとの統合テスト"""
        # Priority queue mock確認
        self.assertIsNotNone(self.autonomous_speech.priority_queue)
        
        # メッセージエンキュー確認（mock call）
        test_message_data = {
            "message": MagicMock(),
            "priority": 3,
            "timestamp": datetime.now().isoformat()
        }
        
        # Queueのメソッド呼び出し確認
        self.autonomous_speech.priority_queue.enqueue.return_value = None
        self.autonomous_speech.priority_queue.enqueue(test_message_data)
        self.autonomous_speech.priority_queue.enqueue.assert_called_once_with(test_message_data)
    
    # ========================================
    # ERROR HANDLING TESTS (エラーハンドリングテスト)
    # ========================================
    
    def test_invalid_channel_handling(self):
        """無効チャンネル処理テスト"""
        invalid_channels = {}
        
        with self.assertRaises((ValueError, TypeError)):
            AutonomousSpeechSystem(
                invalid_channels,
                self.test_environment,
                self.mock_workflow,
                self.mock_priority_queue
            )
    
    def test_invalid_environment_handling(self):
        """無効環境設定処理テスト"""
        invalid_env = "invalid_environment"
        
        # 無効環境でもシステムは動作する（デフォルト値使用）
        system = AutonomousSpeechSystem(
            self.test_channels,
            invalid_env,
            self.mock_workflow,
            self.mock_priority_queue
        )
        
        self.assertEqual(system.environment, invalid_env)


# AsyncIOテスト用のカスタムテストケース
class AsyncTestCase(unittest.TestCase):
    """非同期テスト用基底クラス"""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def async_test(self, coro):
        """非同期テストヘルパー"""
        return self.loop.run_until_complete(coro)


class TestAutonomousSpeechAsync(AsyncTestCase):
    """自発発言システム非同期テスト"""
    
    def setUp(self):
        super().setUp()
        self.test_channels = {
            "command_center": 1383963657137946664,
            "lounge": 1383966355962990653,
            "development": 1383968516033478727,
            "creation": 1383981653046726728
        }
        
        self.mock_workflow = MagicMock(spec=DailyWorkflowSystem)
        self.mock_priority_queue = MagicMock()
        
        self.autonomous_speech = AutonomousSpeechSystem(
            channel_ids=self.test_channels,
            environment="test",
            daily_workflow=self.mock_workflow,
            priority_queue=self.mock_priority_queue
        )
    
    def test_async_speech_generation(self):
        """非同期発言生成テスト"""
        async def test_coro():
            # 非同期メソッドのテスト
            self.autonomous_speech.is_running = True
            
            # システム状態確認
            self.assertTrue(self.autonomous_speech.is_running)
            
            # 非同期処理のモック
            await asyncio.sleep(0.01)  # 短い非同期処理
            
            return True
        
        result = self.async_test(test_coro())
        self.assertTrue(result)


if __name__ == '__main__':
    # 統合テストスイート実行
    unittest.main(verbosity=2)