#!/usr/bin/env python3
"""
Autonomous Speech System Channel Frequency Tests  
TDD Implementation - Phase 3: 失敗するテストケース
"""

import unittest
from unittest.mock import patch, MagicMock
from collections import Counter
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.autonomous_speech import SimplifiedAutonomousSpeechSystem


class TestAutonomousSpeechChannelFrequency(unittest.TestCase):
    """自発発言システムのチャンネル頻度制御テスト"""
    
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
    
    def test_lynq_development_frequency(self):
        """LynQがdevelopmentチャンネルで50%の頻度を持つ"""
        # 1000回のエージェント選択をシミュレート
        selections = []
        
        for _ in range(1000):
            agent = self.speech_system.select_agent_for_channel("development")
            selections.append(agent)
        
        # LynQの選択回数をカウント
        counter = Counter(selections)
        lynq_count = counter.get("lynq", 0)
        
        # 50% ± 5% の範囲内であることを確認（統計的誤差を考慮）
        self.assertGreaterEqual(lynq_count, 450, "LynQがdevelopmentで45%以上選択されるべき")
        self.assertLessEqual(lynq_count, 550, "LynQがdevelopmentで55%以下選択されるべき")
        
        # developmentでのLynQ頻度が他のチャンネルより高いことを確認
        other_channel_lynq_count = 0
        for channel in ["command_center", "creation"]:
            for _ in range(1000):
                agent = self.speech_system.select_agent_for_channel(channel)
                if agent == "lynq":
                    other_channel_lynq_count += 1
        
        # 他のチャンネルでのLynQ頻度は25%程度（1000回×2チャンネル×25%=500回程度）
        self.assertLess(other_channel_lynq_count, lynq_count, 
                       "developmentでのLynQ頻度が他チャンネルより高いべき")
    
    def test_paz_creation_frequency(self):
        """Pazがcreationチャンネルで50%の頻度を持つ"""
        # 1000回のエージェント選択をシミュレート
        selections = []
        
        for _ in range(1000):
            agent = self.speech_system.select_agent_for_channel("creation")
            selections.append(agent)
        
        # Pazの選択回数をカウント
        counter = Counter(selections)
        paz_count = counter.get("paz", 0)
        
        # 50% ± 5% の範囲内であることを確認
        self.assertGreaterEqual(paz_count, 450, "Pazがcreationで45%以上選択されるべき")
        self.assertLessEqual(paz_count, 550, "Pazがcreationで55%以下選択されるべき")
    
    def test_spectra_equal_distribution(self):
        """Spectraが全チャンネルで均等な頻度を持つ"""
        channel_spectra_counts = {}
        
        # 各チャンネルでのSpectra選択回数を測定
        for channel in self.test_channels.keys():
            selections = []
            for _ in range(1000):
                agent = self.speech_system.select_agent_for_channel(channel)
                selections.append(agent)
            
            counter = Counter(selections)
            channel_spectra_counts[channel] = counter.get("spectra", 0)
        
        # 全チャンネルでのSpectra頻度が均等（±10%）であることを確認
        spectra_counts = list(channel_spectra_counts.values())
        average = sum(spectra_counts) / len(spectra_counts)
        
        for channel, count in channel_spectra_counts.items():
            self.assertGreaterEqual(count, average * 0.9, 
                                   f"{channel}でのSpectra頻度が平均の90%以上であるべき")
            self.assertLessEqual(count, average * 1.1, 
                                f"{channel}でのSpectra頻度が平均の110%以下であるべき")
    
    def test_frequency_configuration(self):
        """頻度設定が正しく定義されている"""
        frequency_config = self.speech_system.get_frequency_configuration()
        
        # LynQ development優先設定
        self.assertEqual(frequency_config["lynq"]["development"], 0.5)
        self.assertEqual(frequency_config["lynq"]["others"], 0.25)
        
        # Paz creation優先設定  
        self.assertEqual(frequency_config["paz"]["creation"], 0.5)
        self.assertEqual(frequency_config["paz"]["others"], 0.25)
        
        # Spectra均等設定
        self.assertEqual(frequency_config["spectra"]["all"], 1.0/3)  # 約0.33
    
    def test_channel_agent_selection_distribution(self):
        """チャンネル別エージェント選択の分散テスト"""
        # 全チャンネル・全エージェントの組み合わせを検証
        test_results = {}
        
        for channel in self.test_channels.keys():
            selections = []
            for _ in range(300):  # 統計的に十分なサンプル数
                agent = self.speech_system.select_agent_for_channel(channel)
                selections.append(agent)
            
            counter = Counter(selections)
            test_results[channel] = counter
        
        # development: LynQ優位
        self.assertGreater(test_results["development"]["lynq"], 
                          test_results["development"]["spectra"],
                          "developmentではLynQがSpectraより多く選択されるべき")
        
        # creation: Paz優位
        self.assertGreater(test_results["creation"]["paz"], 
                          test_results["creation"]["spectra"],
                          "creationではPazがSpectraより多く選択されるべき")
        
        # command_center: 比較的均等（Spectraがやや優位でも可）
        command_center_counts = test_results["command_center"]
        # 各エージェントが最低20%は選択される
        total = sum(command_center_counts.values())
        for agent, count in command_center_counts.items():
            self.assertGreater(count, total * 0.2, 
                              f"command_centerで{agent}が20%以上選択されるべき")


if __name__ == '__main__':
    unittest.main()