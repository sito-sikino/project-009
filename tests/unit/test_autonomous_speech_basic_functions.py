#!/usr/bin/env python3
"""
Autonomous Speech System Basic Functions Tests
TDD Implementation - Phase 3: 失敗するテストケース
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timedelta
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.autonomous_speech import SimplifiedAutonomousSpeechSystem, Environment


class TestAutonomousSpeechBasicFunctions(unittest.TestCase):
    """自発発言システムの基本機能テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.test_channels = {
            "command_center": 1383963657137946664,
            "lounge": 1383966355962990653,
            "development": 1383968516033478727,
            "creation": 1383981653046726728
        }
        
        # SimplifiedAutonomousSpeechSystem（まだ存在しない）のインスタンス化を試行
        self.speech_system = SimplifiedAutonomousSpeechSystem(
            channel_ids=self.test_channels,
            environment="test"
        )
    
    def test_ten_second_rule_blocking(self):
        """10秒ルール：前回投稿から10秒未満は新規投稿をブロック"""
        # 最後の自発発言が5秒前の状況をモック
        mock_queue_data = [
            {
                "id": "autonomous_test_recent",
                "event_type": "autonomous_speech",
                "timestamp": (datetime.now() - timedelta(seconds=5)).isoformat(),
                "target_agent": "spectra"
            }
        ]
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_queue_data))):
            with patch('json.load', return_value=mock_queue_data):
                result = self.speech_system.can_post_autonomous_message()
                self.assertFalse(result, "10秒未満では新規投稿がブロックされるべき")
    
    def test_ten_second_rule_allowing(self):
        """10秒ルール：前回投稿から10秒以上経過時は新規投稿を許可"""
        # 最後の自発発言が15秒前の状況をモック
        mock_queue_data = [
            {
                "id": "autonomous_test_old",
                "event_type": "autonomous_speech", 
                "timestamp": (datetime.now() - timedelta(seconds=15)).isoformat(),
                "target_agent": "lynq"
            }
        ]
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_queue_data))):
            with patch('json.load', return_value=mock_queue_data):
                result = self.speech_system.can_post_autonomous_message()
                self.assertTrue(result, "10秒以上経過時は新規投稿が許可されるべき")
    
    def test_environment_probability_test(self):
        """テスト環境では100%の確率"""
        test_system = SimplifiedAutonomousSpeechSystem(
            channel_ids=self.test_channels,
            environment="test"
        )
        
        probability = test_system.get_speech_probability()
        self.assertEqual(probability, 1.0, "テスト環境では100%の確率であるべき")
    
    def test_environment_probability_production(self):
        """本番環境では33%の確率"""
        prod_system = SimplifiedAutonomousSpeechSystem(
            channel_ids=self.test_channels,
            environment="production"
        )
        
        probability = prod_system.get_speech_probability()
        self.assertEqual(probability, 0.33, "本番環境では33%の確率であるべき")
    
    def test_conversation_interruption_avoidance(self):
        """会話中断回避：アクティブな会話中のチャンネルは除外"""
        with patch.object(self.speech_system, 'conversation_detector') as mock_detector:
            # developmentチャンネルが会話中
            def is_active(channel_id):
                return str(channel_id) == str(self.test_channels["development"])
            
            mock_detector.is_conversation_active.side_effect = is_active
            
            available_channels = self.speech_system.get_available_channels()
            self.assertNotIn("development", available_channels, 
                           "会話中のdevelopmentチャンネルは除外されるべき")
            self.assertIn("command_center", available_channels)
            self.assertIn("creation", available_channels)
    
    def test_message_queue_integration(self):
        """メッセージキューへの統合テスト"""
        mock_queue_data = []
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=mock_queue_data):
                with patch('json.dump') as mock_dump:
                    # 自発メッセージをキューに追加
                    result = self.speech_system.queue_autonomous_message(
                        channel="development",
                        agent="lynq", 
                        message="テストメッセージ"
                    )
                    
                    # ファイルが開かれたことを確認
                    mock_file.assert_called()
                    
                    # json.dumpが呼ばれたことを確認
                    mock_dump.assert_called_once()
                    
                    # 追加されたデータの構造を検証
                    call_args = mock_dump.call_args[0][0]  # 最初の引数（データ）
                    self.assertEqual(len(call_args), 1, "1つのメッセージが追加されるべき")
                    
                    message_data = call_args[0]
                    self.assertEqual(message_data["channel_name"], "development")
                    self.assertEqual(message_data["target_agent"], "lynq")
                    self.assertEqual(message_data["content"], "テストメッセージ")
                    self.assertEqual(message_data["event_type"], "autonomous_speech")
    
    def test_personality_message_generation(self):
        """パーソナリティメッセージ生成テスト"""
        # 各エージェントの個性的メッセージ生成
        spectra_message = self.speech_system.generate_personality_message("spectra")
        lynq_message = self.speech_system.generate_personality_message("lynq")
        paz_message = self.speech_system.generate_personality_message("paz")
        
        # メッセージが生成される
        self.assertIsInstance(spectra_message, str)
        self.assertIsInstance(lynq_message, str)
        self.assertIsInstance(paz_message, str)
        
        # メッセージが空でない
        self.assertGreater(len(spectra_message), 0)
        self.assertGreater(len(lynq_message), 0)
        self.assertGreater(len(paz_message), 0)
    
    def test_tick_interval_configuration(self):
        """ティック間隔設定テスト"""
        # テスト環境：10秒間隔
        test_system = SimplifiedAutonomousSpeechSystem(
            channel_ids=self.test_channels,
            environment="test"
        )
        self.assertEqual(test_system.get_tick_interval(), 10)
        
        # 本番環境：300秒（5分）間隔
        prod_system = SimplifiedAutonomousSpeechSystem(
            channel_ids=self.test_channels,
            environment="production"
        )
        self.assertEqual(prod_system.get_tick_interval(), 300)
    
    def test_system_status_reporting(self):
        """システム状態レポート機能テスト"""
        status = self.speech_system.get_system_status()
        
        # 必要なキーが含まれている
        required_keys = [
            "is_running", "environment", "speech_probability", 
            "tick_interval_seconds", "current_phase"
        ]
        
        for key in required_keys:
            self.assertIn(key, status, f"システム状態に{key}が含まれるべき")
        
        # 環境設定が正しく反映されている
        self.assertEqual(status["environment"], "test")
        self.assertEqual(status["speech_probability"], 1.0)


if __name__ == '__main__':
    unittest.main()