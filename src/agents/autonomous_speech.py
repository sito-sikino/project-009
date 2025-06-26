#!/usr/bin/env python3
"""
Autonomous Speech System - Workflow統合型自発発言システム（LLM統合版）

AC-016: Autonomous Speech System の実装
- Daily Workflow統合：フェーズ別行動制御
- tick-based scheduling（フェーズ依存）
- LLM統合型エージェント選択・メッセージ生成
- 環境別確率制御 (test: 100%, prod: 33%)
"""
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
from dataclasses import dataclass
from enum import Enum
import os

# Daily Workflow統合用import
from src.core.daily_workflow import WorkflowPhase

logger = logging.getLogger(__name__)

class Environment(Enum):
    """実行環境"""
    TEST = "test"
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class ChannelType(Enum):
    """チャンネル種別"""
    COMMAND_CENTER = "command_center"
    LOUNGE = "lounge"
    DEVELOPMENT = "development"
    CREATION = "creation"

@dataclass
class SpeechEvent:
    """自発発言イベント"""
    agent: str
    channel: str
    message: str
    timestamp: datetime
    probability_used: float


class AutonomousSpeechSystem:
    """LLM統合型自発発言システム - シンプル化版"""
    
    def __init__(self, channel_ids: Dict[str, int], environment: str = "production", workflow_system=None, priority_queue=None, gemini_client=None, system_settings=None):
        self.channel_ids = channel_ids
        self.environment = Environment(environment.lower())
        self.workflow_system = workflow_system
        self.priority_queue = priority_queue
        self.gemini_client = gemini_client
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        
        # 環境別設定（SystemSettings経由で必須）
        if not system_settings:
            raise RuntimeError("SystemSettings is required for autonomous speech configuration")
        
        # AppSettingsから環境設定を取得
        self.speech_probability = 1.0 if self.environment == Environment.TEST else 0.33
        self.tick_interval = system_settings.autonomous_speech_interval
        
        # 前回発言情報（LLMに渡す文脈として使用）
        self.last_speech_info = {
            "agent": None,
            "channel": None,
            "timestamp": None
        }
        
        # LLM統合メッセージ生成
        
        logger.info(f"🎙️ LLM統合型 Autonomous Speech System initialized for {self.environment.value}")
        logger.info(f"📊 Speech probability: {self.speech_probability * 100:.0f}%")
        logger.info(f"⏱️ Tick interval: {self.tick_interval}秒")
        if workflow_system:
            logger.info("🔗 Workflow integration enabled")
        
        
    async def start(self):
        """自発発言システム開始"""
        if self.is_running:
            logger.warning("Autonomous Speech System は既に動作中です")
            return
            
        self.is_running = True
        self.task = asyncio.create_task(self._speech_loop())
        logger.info("🚀 Autonomous Speech System 開始")
        
    async def stop(self):
        """自発発言システム停止"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Autonomous Speech System 停止")
        
    async def _speech_loop(self):
        """tick間隔発言ループ"""
        logger.info("🔄 Autonomous speech monitoring loop started")
        
        while self.is_running:
            try:
                # tick間隔待機
                logger.info(f"⏱️ Waiting {self.tick_interval} seconds for next autonomous speech check...")
                await asyncio.sleep(self.tick_interval)
                logger.info("⏰ Autonomous speech tick triggered!")
                
                # 確率判定
                if random.random() <= self.speech_probability:
                    logger.info(f"🎲 Speech probability check passed: {self.speech_probability * 100:.0f}%")
                    await self._execute_autonomous_speech()
                else:
                    logger.info(f"🎲 Speech probability check failed: {self.speech_probability * 100:.0f}%")
                    
            except Exception as e:
                logger.error(f"❌ Autonomous speech loop error: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機
                
    async def _execute_autonomous_speech(self):
        """LLM統合型自発発言実行"""
        try:
            # 現在のフェーズ確認
            current_phase = self._get_current_phase()
            
            # フェーズ別の発言可否チェック
            logger.info(f"🔍 Current phase: {current_phase}")
            if current_phase.value == "standby":
                # TEST環境でも本番と同じようにSTANDBY期間は完全にスキップ
                logger.info("🚫 STANDBY期間中のため自発発言をスキップ")
                return
                
            # 利用可能なチャンネル取得
            available_channel = self._get_available_channel(current_phase)
            logger.info(f"🔍 Available channel: {available_channel}")
            if not available_channel:
                logger.info("🚫 利用可能なチャンネルがないため自発発言をスキップ")
                return
                
            # ワークフローイベント実行中チェック
            if self._is_workflow_event_active():
                logger.info("⏰ ワークフローイベント実行中のため自発発言をスキップ")
                return
                
            # LLM統合メッセージ生成（エージェント選択も含む）
            speech_data = await self._generate_llm_integrated_speech(available_channel, current_phase)
            if not speech_data:
                logger.warning("⚠️ LLM統合メッセージ生成に失敗")
                return
                
            # メッセージキューに追加
            await self._queue_autonomous_message(
                channel=available_channel,
                agent=speech_data["agent"],
                message=speech_data["message"]
            )
            
            # 発言完了時刻とチャンネルを記録（agentは既に更新済み）
            self.last_speech_info["channel"] = available_channel
            self.last_speech_info["timestamp"] = datetime.now()
            
            logger.info(f"🎙️ LLM統合自発発言実行: {speech_data['agent']} -> #{available_channel}")
            
        except Exception as e:
            logger.error(f"❌ LLM統合自発発言実行失敗: {e}")
            
    def _get_current_phase(self) -> WorkflowPhase:
        """現在のワークフローフェーズを取得（同期問題修正版）"""
        if self.workflow_system:
            # ワークフローシステムのフェーズを取得
            workflow_phase = self.workflow_system.current_phase
            
            # Workflow system controls phase transitions - no time-based overrides
            
            logger.debug(f"🔍 Workflow phase: {workflow_phase.value}")
            return workflow_phase
        
        # Workflow system is required
        raise RuntimeError("Workflow system is required but not available")
            
    def _get_available_channel(self, phase: WorkflowPhase) -> Optional[str]:
        """フェーズに応じた利用可能チャンネルID取得（詳細診断版）"""
        logger.info(f"🔍 _get_available_channel called with phase: {phase}")
        logger.info(f"🔍 workflow_system: {self.workflow_system}")
        
        # タスク実行中チェック
        if self.workflow_system and hasattr(self.workflow_system, 'current_tasks'):
            active_tasks = self.workflow_system.current_tasks
            logger.info(f"🔍 Active tasks: {active_tasks}")
            if active_tasks:
                # タスクチャンネルを優先
                for task_info in active_tasks.values():
                    channel_name = task_info.get('channel')
                    if channel_name:
                        logger.info(f"🔍 Task channel found: {channel_name}")
                        return self._get_channel_id_by_name(channel_name)
        
        # フェーズ別デフォルトチャンネル（文字列値比較で確実性確保）
        logger.info(f"🔍 Phase-based channel selection: {phase} (value: {phase.value})")
        if phase.value == "active":
            logger.info("🔍 ACTIVE phase -> command_center (meeting/work mode)")
            channel_id = self._get_channel_id_by_name("command_center")
            if channel_id:
                logger.info(f"✅ ACTIVE phase channel confirmed: command_center ({channel_id})")
            return channel_id
        elif phase.value == "free":
            logger.info("🔍 FREE phase -> lounge (social mode)")
            channel_id = self._get_channel_id_by_name("lounge")
            if channel_id:
                logger.info(f"✅ FREE phase channel confirmed: lounge ({channel_id})")
            return channel_id
        elif phase.value == "standby":
            # STANDBY期間は本番・TEST環境問わず自発発言なし
            logger.info("🔍 STANDBY phase -> no autonomous speech")
        elif phase.value == "processing":
            logger.info("🔍 PROCESSING phase -> no autonomous speech (morning workflow in progress)")
        else:
            logger.info(f"🔍 Unknown phase value: {phase} ({phase.value})")
        
        logger.info("🔍 No channel found, returning None")
        return None
    
    def _get_channel_display_name(self, channel_name: str) -> str:
        """チャンネル表示名を取得"""
        display_names = {
            "command_center": "command-center",
            "lounge": "lounge",
            "development": "development", 
            "creation": "creation"
        }
        return display_names.get(channel_name, channel_name)
    
    def _get_channel_id_by_name(self, channel_name: str) -> Optional[str]:
        """チャンネル名からチャンネルIDを取得"""
        logger.info(f"🔍 All available channel_ids: {self.channel_ids}")
        
        channel_id = self.channel_ids.get(channel_name)
        if channel_id and channel_id > 0:
            logger.info(f"✅ Channel mapping: {channel_name} -> {channel_id}")
            return str(channel_id)
        
        logger.error(f"❌ Channel ID not found for '{channel_name}': {self.channel_ids}")
        return None
        
    def _is_workflow_event_active(self) -> bool:
        """ワークフローイベント実行中かチェック"""
        if not self.workflow_system:
            return False
            
        # ワークフローイベントの実行時刻周辺（±1分）をチェック（設定ベース）
        from ..config.settings import get_system_settings
        system_settings = get_system_settings()
        current_time = datetime.now()
        
        # 設定から重要イベント時刻を取得
        critical_times = [
            system_settings.parse_time_setting(system_settings.workflow_morning_workflow_time),  # Morning workflow
            system_settings.parse_time_setting(system_settings.workflow_work_conclusion_time),   # Work conclusion
            system_settings.parse_time_setting(system_settings.workflow_system_rest_time)       # System rest
        ]
        
        for event_hour, event_minute in critical_times:
            event_time = current_time.replace(hour=event_hour, minute=event_minute, second=0, microsecond=0)
            time_diff = abs((event_time - current_time).total_seconds())
            if time_diff <= 60:  # 1分間
                return True
                
        return False
        
    async def _generate_llm_integrated_speech(self, channel: str, phase: WorkflowPhase) -> Optional[Dict[str, str]]:
        """真のLLM統合型メッセージ生成（エージェント選択含む）"""
        try:
            # GeminiClientがDI経由で注入されているかチェック
            if not self.gemini_client:
                raise RuntimeError("GeminiClient is required but not injected via DI")
            
            # アクティブタスクの取得
            active_tasks = self._get_active_tasks_summary()
            work_mode = bool(active_tasks != "なし")
            
            # 自発発言用のコンテキスト生成
            autonomous_context = self._create_autonomous_speech_context(
                channel=channel, 
                phase=phase, 
                work_mode=work_mode, 
                active_tasks=active_tasks
            )
            
            # DI経由で注入されたGeminiClientを使用
            llm_response = await self.gemini_client.unified_agent_selection(autonomous_context)
            
            # 前回発言者との重複チェック
            selected_agent = llm_response.get('selected_agent', 'spectra')
            if selected_agent == self.last_speech_info.get("agent"):
                # 前回と同じエージェントの場合、チャンネル優先度に基づいて別エージェントを選択
                alternative_agent = self._select_alternative_agent(channel, selected_agent)
                selected_agent = alternative_agent
                # メッセージも再生成（簡易版として既存応答を使用）
                message = llm_response.get('response_content', '')
            else:
                message = llm_response.get('response_content', '')
            
            # last_speech_infoを更新
            self.last_speech_info["agent"] = selected_agent
            
            logger.debug(f"🎲 LLM Agent selection: {selected_agent}")
            
            return {
                "agent": selected_agent,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"❌ LLM統合メッセージ生成失敗: {e}")
            return None
    
    def _create_autonomous_speech_context(self, channel: str, phase: WorkflowPhase, work_mode: bool, active_tasks: str) -> Dict[str, Any]:
        """自発発言用コンテキスト生成"""
        # チャンネルIDからチャンネル名を特定
        channel_name = None
        for name, ch_id in self.channel_ids.items():
            if str(ch_id) == channel:
                channel_name = self._get_channel_display_name(name)
                break
        
        if not channel_name:
            channel_name = f"channel-{channel}"
        
        if work_mode:
            context_message = f"現在のタスク「{active_tasks}」に関連して、自発的に有益な発言をしたい。"
        elif phase.value == "active":
            context_message = "会議や議論を促進するために自発的に発言したい。"
        else:
            context_message = "チームとのコミュニケーションのために自発的に発言したい。"
        
        return {
            'message': context_message,
            'mention_override': '',
            'hot_memory': [],  # 必要に応じて履歴を追加
            'cold_memory': [],  # 必要に応じて長期記憶を追加
            'channel_id': channel
        }
    
    def _select_alternative_agent(self, channel: str, current_agent: str) -> str:
        """前回と同じエージェントの場合の代替選択（LLM統合選択を優先使用）"""
        agents = ["spectra", "lynq", "paz"]
        available_agents = [agent for agent in agents if agent != current_agent]
        
        # LLMのシステムプロンプトに確率が指定されているため、シンプルなランダム選択
        # 真のLLM統合選択に任せることで一貫性を保つ
        return random.choice(available_agents)
    
        
    def _get_active_tasks_summary(self) -> str:
        """アクティブタスクの要約を取得"""
        if not self.workflow_system or not hasattr(self.workflow_system, 'current_tasks'):
            return "なし"
            
        tasks = self.workflow_system.current_tasks
        if not tasks:
            return "なし"
            
        summaries = []
        for channel, task_info in tasks.items():
            summaries.append(f"{channel}: {task_info.get('task', 'Unknown')}")
        
        return ", ".join(summaries)
        
    async def _queue_autonomous_message(self, channel: str, agent: str, message: str):
        """自発発言メッセージをキューに追加"""
        if not self.priority_queue:
            logger.warning("Priority queue not available")
            return
            
        # メッセージオブジェクト作成
        class AutonomousMessage:
            def __init__(self, content, channel_id, target_agent):
                self.content = content
                self.channel = AutonomousChannel(channel_id)
                self.author = AutonomousAuthor()
                self.id = f"autonomous_{datetime.now().isoformat()}"
                self.autonomous_speech = True
                self.target_agent = target_agent
                
        class AutonomousChannel:
            def __init__(self, channel_id):
                self.id = channel_id
                self.name = channel
                
        class AutonomousAuthor:
            def __init__(self):
                self.bot = True
                self.id = "000000000000000000"
        
        message_data = {
            'message': AutonomousMessage(message, int(channel), agent),
            'priority': 5,  # 自発発言は低優先度
            'timestamp': datetime.now()
        }
        
        await self.priority_queue.enqueue(message_data)
        logger.info(f"📝 Autonomous message queued: {agent} -> #{channel}")
        
    def get_status(self) -> Dict:
        """システム状態を取得"""
        return {
            "is_running": self.is_running,
            "environment": self.environment.value,
            "speech_probability": self.speech_probability,
            "tick_interval_seconds": self.tick_interval,
            "current_phase": self._get_current_phase().value,
            "last_speech": self.last_speech_info,
            "active_tasks": self._get_active_tasks_summary()
        }