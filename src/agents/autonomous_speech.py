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
from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass
from enum import Enum
import os

# Daily Workflow統合用import
try:
    from .daily_workflow import WorkflowPhase
except ImportError:
    # Fallback for standalone execution
    class WorkflowPhase(Enum):
        STANDBY = "standby"
        ACTIVE = "active"
        FREE = "free"

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

class AgentPersonalityGenerator:
    """エージェント個性メッセージ生成（参考データ）"""
    
    # 会議モード用メッセージ（/task commitトリガーなし）
    SPECTRA_MEETING_MESSAGES = [
        "💼 **会議進行** 本日の議題について話し合いましょう。何かご提案がございますか？",
        "📋 **アジェンダ確認** 今日検討すべき課題や目標はありますか？一緒に整理してみましょう。",
        "🤝 **意見交換** チームの皆さんのお考えやアイデアをお聞かせください。",
        "📊 **状況共有** 現在の状況や進捗について情報を共有しませんか？",
        "🎯 **方針検討** 今後の方向性について一緒に考えてみましょう。何かご意見はありますか？"
    ]
    
    LYNQ_MEETING_MESSAGES = [
        "🔍 **技術的議論** 技術面での課題や検討事項があれば議論しましょう。",
        "⚙️ **アーキテクチャ相談** システム設計について相談したいことはありませんか？",
        "📋 **技術要件整理** 実装に向けた技術要件を整理しませんか？",
        "🧠 **技術知見共有** 最近学んだ技術や手法があれば共有してください。",
        "💡 **解決策検討** 技術的な課題の解決策を一緒に考えてみましょう。"
    ]
    
    PAZ_MEETING_MESSAGES = [
        "✨ **創造的議論** 新しいアイデアやアプローチについて話し合いませんか？",
        "🎨 **デザイン相談** UIやUXについてご相談がありましたらお聞かせください。",
        "💭 **ブレインストーミング** 自由な発想でアイデアを出し合いませんか？",
        "🌟 **創作企画** 何か面白い企画やプロジェクトのアイデアはありませんか？",
        "🎪 **イノベーション** 従来とは違うアプローチを考えてみませんか？"
    ]
    
    # 実務モード用メッセージ（/task commit実行後）
    SPECTRA_WORK_MESSAGES = [
        "💼 **進捗確認** 皆さん、今日のタスクの調子はいかがですか？何かサポートが必要でしたらお声かけください！",
        "📊 **リソース状況チェック** プロジェクトのリソース配分は適切でしょうか？効率化のご提案があれば喜んでお手伝いします。",
        "🎯 **目標達成サポート** 今週の目標に向けて順調に進んでいますか？調整が必要な点があれば一緒に検討しましょう。",
        "🤝 **チーム連携促進** 各部門間の情報共有はスムーズですか？コミュニケーションの改善点があれば教えてください。",
        "📋 **タスク優先順位** 現在のタスクの優先順位は適切でしょうか？再調整が必要でしたらご相談ください。"
    ]
    
    LYNQ_WORK_MESSAGES = [
        "🔍 **技術的検証** 最近のシステム実装で気になる点はありませんか？パフォーマンスやセキュリティの観点から確認しましょう。",
        "⚙️ **アーキテクチャ最適化** 現在の設計で改善できる部分があれば、一緒に分析してみませんか？",
        "🧪 **テスト戦略** 実装したコードのテストカバレッジは十分でしょうか？品質保証の観点から検討してみましょう。",
        "📈 **メトリクス分析** システムのパフォーマンス指標を確認しましょう。ボトルネックや改善点はありませんか？",
        "🔧 **実装効率化** 開発プロセスで自動化できる部分はありませんか？ツールやワークフローの改善を検討しましょう。"
    ]
    
    PAZ_WORK_MESSAGES = [
        "✨ **創造的インスピレーション** 新しいアイデアが浮かんでいませんか？どんな小さな閃きでも大歓迎です！",
        "🎨 **アート的発想** 今日は何か美しいものや面白いものに出会いましたか？創造性を刺激する体験を共有しませんか？",
        "💡 **ブレインストーミング** 解決が困難な課題があれば、一緒に発散的思考で新しい角度から考えてみましょう！",
        "🌈 **想像力拡張** 既存の枠組みを超えた斬新なアプローチはありませんか？自由な発想で可能性を探ってみましょう。",
        "🚀 **革新的チャレンジ** 誰もやったことがない新しい試みを考えてみませんか？リスクを恐れず、創造的に挑戦しましょう！"
    ]

    @classmethod
    def get_random_message(cls, agent: str) -> str:
        """エージェント別ランダムメッセージ取得（従来互換性のため実務モード）"""
        return cls.get_work_mode_message(agent)
    
    @classmethod
    def get_meeting_message(cls, agent: str) -> str:
        """会議モード専用メッセージ取得"""
        messages_map = {
            "spectra": cls.SPECTRA_MEETING_MESSAGES,
            "lynq": cls.LYNQ_MEETING_MESSAGES,
            "paz": cls.PAZ_MEETING_MESSAGES
        }
        
        if agent not in messages_map:
            return "🤖 **会議進行** 皆さんのご意見をお聞かせください。"
            
        return random.choice(messages_map[agent])
    
    @classmethod
    def get_work_mode_message(cls, agent: str) -> str:
        """実務モード専用メッセージ取得"""
        messages_map = {
            "spectra": cls.SPECTRA_WORK_MESSAGES,
            "lynq": cls.LYNQ_WORK_MESSAGES,
            "paz": cls.PAZ_WORK_MESSAGES
        }
        
        if agent not in messages_map:
            return "🤖 システムからの自動メッセージです。"
            
        return random.choice(messages_map[agent])

class AutonomousSpeechSystem:
    """LLM統合型自発発言システム - シンプル化版"""
    
    def __init__(self, channel_ids: Dict[str, int], environment: str = "production", workflow_system=None, priority_queue=None):
        self.channel_ids = channel_ids
        self.environment = Environment(environment.lower())
        self.workflow_system = workflow_system
        self.priority_queue = priority_queue
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        
        # 環境別設定
        self.speech_probability = self._get_speech_probability()
        self.tick_interval = 10 if self.environment == Environment.TEST else 300  # テスト:10秒, 本番:5分
        
        # 前回発言情報（LLMに渡す文脈として使用）
        self.last_speech_info = {
            "agent": None,
            "channel": None,
            "timestamp": None
        }
        
        # メッセージ生成用参考データ
        self.personality_generator = AgentPersonalityGenerator()
        
        logger.info(f"🎙️ LLM統合型 Autonomous Speech System initialized for {self.environment.value}")
        logger.info(f"📊 Speech probability: {self.speech_probability * 100:.0f}%")
        logger.info(f"⏱️ Tick interval: {self.tick_interval}秒")
        if workflow_system:
            logger.info("🔗 Workflow integration enabled")
        
    def _get_speech_probability(self) -> float:
        """環境別発言確率設定"""
        return 1.0 if self.environment == Environment.TEST else 0.33
        
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
            if current_phase == WorkflowPhase.STANDBY:
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
        """現在のワークフローフェーズを取得"""
        if self.workflow_system:
            return self.workflow_system.current_phase
        
        # Fallback: 時刻ベース判定
        hour = datetime.now().hour
        if 7 <= hour < 20:
            return WorkflowPhase.ACTIVE
        elif hour >= 20:
            return WorkflowPhase.FREE
        else:
            return WorkflowPhase.STANDBY
            
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
            logger.info("🔍 ACTIVE phase -> command_center")
            return self._get_channel_id_by_name("command_center")
        elif phase.value == "free":
            logger.info("🔍 FREE phase -> lounge")
            return self._get_channel_id_by_name("lounge")
        elif phase.value == "standby":
            logger.info("🔍 STANDBY phase -> no autonomous speech")
        else:
            logger.info(f"🔍 Unknown phase value: {phase} ({phase.value})")
        
        logger.info("🔍 No channel found, returning None")
        return None
    
    def _get_channel_id_by_name(self, channel_name: str) -> Optional[str]:
        """チャンネル名からチャンネルIDを取得（フォールバック機能付き）"""
        logger.info(f"🔍 All available channel_ids: {self.channel_ids}")
        
        channel_id = self.channel_ids.get(channel_name)
        if channel_id and channel_id > 0:
            logger.info(f"✅ Channel mapping: {channel_name} -> {channel_id}")
            return str(channel_id)
        
        # フォールバック: loungeが無い場合はcommand_centerを使用
        if channel_name == "lounge":
            logger.warning(f"⚠️ 'lounge' channel not found, falling back to 'command_center'")
            fallback_id = self.channel_ids.get("command_center")
            if fallback_id and fallback_id > 0:
                logger.info(f"✅ Fallback mapping: lounge -> command_center ({fallback_id})")
                return str(fallback_id)
        
        logger.error(f"❌ Channel ID not found for '{channel_name}': {self.channel_ids}")
        return None
        
    def _is_workflow_event_active(self) -> bool:
        """ワークフローイベント実行中かチェック"""
        if not self.workflow_system:
            return False
            
        # ワークフローイベントの実行時刻周辺（±1分）をチェック
        current_time = datetime.now()
        critical_times = [
            (7, 0),   # Morning meeting
            (20, 0),  # Work conclusion
            (0, 0)    # System rest
        ]
        
        for event_hour, event_minute in critical_times:
            event_time = current_time.replace(hour=event_hour, minute=event_minute, second=0, microsecond=0)
            time_diff = abs((event_time - current_time).total_seconds())
            if time_diff <= 60:  # 1分間
                return True
                
        return False
        
    async def _generate_llm_integrated_speech(self, channel: str, phase: WorkflowPhase) -> Optional[Dict[str, str]]:
        """LLM統合型メッセージ生成（エージェント選択含む）"""
        # 本実装では実際のLLM（Gemini）を呼び出す代わりに、
        # システムプロンプトのロジックをコードでシミュレート
        
        # アクティブタスクの取得
        active_tasks = self._get_active_tasks_summary()
        work_mode = bool(active_tasks != "なし")
        
        # エージェントプール
        agents = ["spectra", "lynq", "paz"]
        
        # 前回発言者を優先度下げる（90%削減）
        agent_weights = {}
        for agent in agents:
            if agent == self.last_speech_info.get("agent"):
                agent_weights[agent] = 0.1
            else:
                agent_weights[agent] = 1.0
        
        # チャンネル別の重み付け適用
        channel_preferences = {
            "command_center": {"spectra": 0.4, "lynq": 0.3, "paz": 0.3},
            "development": {"lynq": 0.5, "spectra": 0.25, "paz": 0.25},
            "creation": {"paz": 0.5, "lynq": 0.25, "spectra": 0.25},
            "lounge": {"spectra": 0.333, "lynq": 0.333, "paz": 0.334}
        }
        
        if channel in channel_preferences:
            for agent in agents:
                agent_weights[agent] *= channel_preferences[channel].get(agent, 0.333)
        
        # 重み付き選択
        total_weight = sum(agent_weights.values())
        if total_weight == 0:
            selected_agent = random.choice(agents)
        else:
            normalized_weights = [agent_weights[agent] / total_weight for agent in agents]
            selected_agent = random.choices(agents, weights=normalized_weights)[0]
        
        # 即座にlast_speech_infoを更新（重複防止）
        self.last_speech_info["agent"] = selected_agent
        
        # メッセージ生成
        if work_mode:
            # 実務モード
            message = self.personality_generator.get_work_mode_message(selected_agent)
        elif phase == WorkflowPhase.ACTIVE:
            # 会議モード
            message = self.personality_generator.get_meeting_message(selected_agent)
        else:
            # 自由時間
            message = self.personality_generator.get_random_message(selected_agent)
        
        logger.debug(f"🎲 Agent selection: {selected_agent} (prev: {self.last_speech_info.get('agent')})")
        
        return {
            "agent": selected_agent,
            "message": message
        }
        
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