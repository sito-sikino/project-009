#!/usr/bin/env python3
"""
Autonomous Speech System Phase Control Tests
TDD Implementation - Phase 3: 失敗するテストケース
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.autonomous_speech import SimplifiedAutonomousSpeechSystem, WorkflowPhase


class TestAutonomousSpeechPhaseControl(unittest.TestCase):
    """自発発言システムのフェーズ制御テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.test_channels = {
            "command_center": 1383963657137946664,
            "lounge": 1383966355962990653,
            "development": 1383968516033478727,
            "creation": 1383981653046726728
        }
        
        # SimplifiedAutonomousSpeechSystem（まだ存在しない）のインスタンス化を試行
        # → 失敗するテスト
        self.speech_system = SimplifiedAutonomousSpeechSystem(
            channel_ids=self.test_channels,
            environment="test"
        )
    
    @patch('src.autonomous_speech.datetime')
    def test_rest_period_speech_disabled(self, mock_datetime):
        """REST期間（00:00-06:59）は自発発言が完全無効"""
        # 03:00にセット（REST期間）
        mock_datetime.now.return_value = datetime(2024, 1, 1, 3, 0, 0)
        
        # REST期間中は自発発言が無効であることを確認
        result = self.speech_system.should_speak_autonomously()
        self.assertFalse(result, "REST期間中は自発発言が無効であるべき")
        
        # フェーズがRESTであることも確認
        phase = self.speech_system.get_current_phase()
        self.assertEqual(phase, WorkflowPhase.REST)
    
    @patch('src.autonomous_speech.datetime')
    def test_meeting_period_excludes_lounge(self, mock_datetime):
        """MEETING期間（07:00-19:59）はlounge以外で自発発言有効"""
        # 14:00にセット（MEETING期間）
        mock_datetime.now.return_value = datetime(2024, 1, 1, 14, 0, 0)
        
        # MEETING期間中は自発発言が有効
        result = self.speech_system.should_speak_autonomously()
        self.assertTrue(result, "MEETING期間中は自発発言が有効であるべき")
        
        # 利用可能チャンネルにloungeが含まれない
        available_channels = self.speech_system.get_available_channels()
        self.assertNotIn("lounge", available_channels, "MEETING期間中はloungeが除外されるべき")
        self.assertIn("command_center", available_channels)
        self.assertIn("development", available_channels)
        self.assertIn("creation", available_channels)
    
    @patch('src.autonomous_speech.datetime')
    def test_conclusion_period_lounge_only(self, mock_datetime):
        """CONCLUSION期間（20:00-23:59）はloungeのみで自発発言有効"""
        # 22:00にセット（CONCLUSION期間）
        mock_datetime.now.return_value = datetime(2024, 1, 1, 22, 0, 0)
        
        # CONCLUSION期間中は自発発言が有効
        result = self.speech_system.should_speak_autonomously()
        self.assertTrue(result, "CONCLUSION期間中は自発発言が有効であるべき")
        
        # 利用可能チャンネルがloungeのみ
        available_channels = self.speech_system.get_available_channels()
        self.assertEqual(available_channels, ["lounge"], "CONCLUSION期間中はloungeのみが利用可能であるべき")
    
    @patch('src.autonomous_speech.datetime')
    def test_preparation_period_speech_disabled(self, mock_datetime):
        """PREPARATION期間（06:55-06:59）は自発発言無効"""
        # 06:57にセット（PREPARATION期間）
        mock_datetime.now.return_value = datetime(2024, 1, 1, 6, 57, 0)
        
        # PREPARATION期間中は自発発言が無効
        result = self.speech_system.should_speak_autonomously()
        self.assertFalse(result, "PREPARATION期間中は自発発言が無効であるべき")
        
        # フェーズがPREPARATIONであることも確認
        phase = self.speech_system.get_current_phase()
        self.assertEqual(phase, WorkflowPhase.PREPARATION)
    
    def test_phase_based_configuration(self):
        """フェーズ別設定が正しく定義されている"""
        # フェーズ設定の構造をテスト
        phase_settings = self.speech_system.get_phase_settings()
        
        # 全フェーズが定義されている
        self.assertIn(WorkflowPhase.REST, phase_settings)
        self.assertIn(WorkflowPhase.PREPARATION, phase_settings)
        self.assertIn(WorkflowPhase.MEETING, phase_settings)
        self.assertIn(WorkflowPhase.CONCLUSION, phase_settings)
        
        # REST と PREPARATION は無効
        self.assertFalse(phase_settings[WorkflowPhase.REST]["enabled"])
        self.assertFalse(phase_settings[WorkflowPhase.PREPARATION]["enabled"])
        
        # MEETING と CONCLUSION は有効
        self.assertTrue(phase_settings[WorkflowPhase.MEETING]["enabled"])
        self.assertTrue(phase_settings[WorkflowPhase.CONCLUSION]["enabled"])
    
    def test_conversation_detector_integration(self):
        """会話検知システムとの統合テスト"""
        # 会話中のチャンネルが除外される
        with patch.object(self.speech_system, 'conversation_detector') as mock_detector:
            mock_detector.is_conversation_active.return_value = True
            
            # 全チャンネルで会話中の場合
            available_channels = self.speech_system.get_available_channels()
            self.assertEqual(len(available_channels), 0, "会話中のチャンネルは除外されるべき")


if __name__ == '__main__':
    unittest.main()