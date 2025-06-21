#!/usr/bin/env python3
"""
Autonomous Speech System - Workflow統合型自発発言システム

AC-016: Autonomous Speech System の実装
- Daily Workflow統合：フェーズ別行動制御
- 5-minute tick-based scheduling（フェーズ依存）
- Environment-specific probability (test: 100%, prod: 33%)
- Channel-specific agent selection（フェーズ考慮）
- Conversation interruption avoidance
- Agent personality consistency
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

# ConversationDetector削除: LangGraph Supervisor統合判定に変更
# 文脈ベースの発言判定により、より自然で効率的な処理を実現

class AgentPersonalityGenerator:
    """エージェント個性メッセージ生成"""
    
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
    """Workflow統合型自発発言システム - Daily Workflowと連携"""
    
    def __init__(self, channel_ids: Dict[str, int], environment: str = "production", workflow_system=None, priority_queue=None):
        self.channel_ids = channel_ids
        self.environment = Environment(environment.lower())
        self.workflow_system = workflow_system  # Daily Workflow System参照
        self.priority_queue = priority_queue  # PriorityQueue参照
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        
        # 環境別設定（テスト時は頻度上げる）
        self.speech_probability = self._get_speech_probability()
        self.tick_interval = 10 if self.environment == Environment.TEST else 300  # テスト:10秒, 本番:5分
        
        # グローバルロック（重複防止）
        self.system_is_currently_speaking = False
        
        # 前回発言者追跡（連続発言防止）
        self.last_speaker = None
        
        # システムコンポーネント
        self.personality_generator = AgentPersonalityGenerator()
        
        # チャンネル別エージェント優先度
        self.channel_agent_preferences = {
            ChannelType.COMMAND_CENTER: ["spectra", "lynq", "paz"],  # Spectra優先
            ChannelType.LOUNGE: ["paz", "spectra", "lynq"],         # Paz優先
            ChannelType.DEVELOPMENT: ["lynq", "spectra", "paz"],    # LynQ優先
            ChannelType.CREATION: ["paz", "lynq", "spectra"]        # Paz優先
        }
        
        # ワークフローフェーズ別設定
        self.phase_settings = self._initialize_phase_settings()
        
        logger.info(f"🎙️ Autonomous Speech System initialized for {self.environment.value}")
        logger.info(f"📊 Speech probability: {self.speech_probability * 100:.0f}%")
        if workflow_system:
            logger.info("🔗 Workflow integration enabled")
        
    def _get_speech_probability(self) -> float:
        """環境別発言確率設定"""
        probability_map = {
            Environment.TEST: 1.0,        # 100%
            Environment.DEVELOPMENT: 1.0,  # 100% (開発時はテスト同様)
            Environment.PRODUCTION: 0.33   # 33%
        }
        return probability_map.get(self.environment, 0.33)
        
    def _initialize_phase_settings(self) -> Dict:
        """ワークフローフェーズ別設定初期化（シンプル化）"""
        return {
            WorkflowPhase.STANDBY: {
                "enabled": False,  # 自発的発言無効
                "description": "待機状態 (0:00-6:59) - 自発的発言なし"
            },
            WorkflowPhase.ACTIVE: {
                "enabled": True,   # 自発的発言有効
                "default_channel": "command_center",  # デフォルトは会議チャンネルのみ
                "description": "活動時間 (7:00-19:59) - command-center会議継続（/task commitまで）"
            },
            WorkflowPhase.FREE: {
                "enabled": True,   # 自発的発言有効
                "preferred_channels": ["lounge"],
                "description": "自由時間 (20:00-23:59) - lounge中心"
            }
        }
        
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
        """5分間隔発言ループ"""
        logger.info("🔄 Autonomous speech monitoring loop started")
        
        while self.is_running:
            try:
                # 5分間隔チェック
                await asyncio.sleep(self.tick_interval)
                
                # 確率判定
                if random.random() <= self.speech_probability:
                    await self._execute_autonomous_speech()
                else:
                    logger.debug(f"🎲 Speech probability check failed: {self.speech_probability * 100:.0f}%")
                    
            except Exception as e:
                logger.error(f"❌ Autonomous speech loop error: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機
                
    async def _execute_autonomous_speech(self):
        """ワークフロー統合型自発発言実行 - フェーズ別行動制御"""
        try:
            # 重複防止チェック（グローバルロック）
            if self.system_is_currently_speaking:
                logger.debug("🔒 システム発言中のため今回のTickをスキップ")
                return
            
            # ロック取得
            self.system_is_currently_speaking = True
            
            # ワークフロー統合チェック
            current_phase = self._get_current_workflow_phase()
            phase_settings = self.phase_settings.get(current_phase, self.phase_settings[WorkflowPhase.ACTIVE])
            
            # フェーズ有効性チェック（簡素化）
            if not phase_settings.get("enabled", False):
                logger.debug(f"🚫 現在のフェーズ {current_phase.value} では自発発言無効")
                return
            
            # ワークフローイベント実行中チェック
            if self._is_workflow_event_active():
                logger.debug("⏰ ワークフローイベント実行中のため自発発言をスキップ")
                return
            
            # グローバル最後発言時刻チェック
            if not await self._can_post_autonomous_message():
                logger.debug("🚫 10秒ルール: まだ前回から10秒経過していません")
                return
            
            # フェーズ別時間制限チェック
            if not self._check_phase_hourly_limit(current_phase, phase_settings):
                logger.debug(f"⏱️ フェーズ別時間制限に達しました: {phase_settings['max_autonomous_per_hour']}/hour")
                return
            
            # フェーズ別チャンネル選択
            available_channels = self._get_phase_appropriate_channels(current_phase, phase_settings)
            
            if not available_channels:
                logger.info(f"💬 フェーズ{current_phase.value}に適したチャンネルで会話中のため自発発言をスキップ")
                return
                
            # チャンネル選択（フェーズ優先）
            selected_channel = self._select_phase_appropriate_channel(available_channels, phase_settings)
            
            # フェーズ別エージェント選択
            selected_agent = self._select_phase_appropriate_agent(selected_channel, current_phase, phase_settings)
            
            # パーソナリティメッセージ生成（フェーズ考慮）
            message = self._generate_phase_appropriate_message(selected_agent, current_phase)
            
            # メッセージキューに追加（フェーズ情報含む）
            await self._queue_autonomous_message(selected_channel, selected_agent, message, current_phase)
            
            logger.info(f"🎙️ フェーズ別自発発言実行: {selected_agent} -> #{selected_channel} (phase: {current_phase.value})")
            
        except Exception as e:
            logger.error(f"❌ ワークフロー統合型自発発言実行失敗: {e}")
        finally:
            # ロック解除
            self.system_is_currently_speaking = False
            
    def _get_current_workflow_phase(self) -> WorkflowPhase:
        """現在のワークフローフェーズを取得"""
        if self.workflow_system:
            return self.workflow_system.current_phase
        else:
            # Fallback: 時刻ベースのフェーズ判定
            current_time = datetime.now().time()
            hour = current_time.hour
            minute = current_time.minute
            
            if hour >= 7 and hour < 20:
                return WorkflowPhase.ACTIVE
            elif hour >= 20:
                return WorkflowPhase.FREE
            else:
                return WorkflowPhase.STANDBY
                
    def _is_workflow_event_active(self) -> bool:
        """ワークフローイベント実行中かチェック"""
        if not self.workflow_system:
            return False
            
        # ワークフローイベントの実行時刻周辺（±2分）をチェック
        current_time = datetime.now().time()
        
        # 重要イベント時刻
        critical_times = [
            (6, 55),  # Daily report generation
            (7, 0),   # Morning meeting
            (20, 0),  # Work conclusion
            (0, 0)    # System rest
        ]
        
        for event_hour, event_minute in critical_times:
            event_time = datetime.now().replace(hour=event_hour, minute=event_minute, second=0, microsecond=0)
            current_datetime = datetime.now()
            
            # イベント時刻の前後2分間は自発発言を避ける
            time_diff = abs((event_time - current_datetime).total_seconds())
            if time_diff <= 120:  # 2分間
                return True
                
        return False
        
    def _check_phase_hourly_limit(self, phase: WorkflowPhase, phase_settings: Dict) -> bool:
        """フェーズ別時間制限チェック"""
        max_per_hour = phase_settings.get("max_autonomous_per_hour", 12)
        
        # 過去1時間の自発発言数をカウント
        try:
            with open("message_queue.json", "r", encoding='utf-8') as f:
                queue_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return True
            
        # 1時間前のタイムスタンプ
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        # 過去1時間の自発発言をカウント
        recent_autonomous = [
            item for item in queue_data 
            if (item.get('event_type') == 'autonomous_speech' and
                datetime.fromisoformat(item.get('timestamp', '1970-01-01')) > one_hour_ago and
                item.get('workflow_phase') == phase.value)
        ]
        
        return len(recent_autonomous) < max_per_hour
        
    def _get_phase_appropriate_channels(self, phase: WorkflowPhase, phase_settings: Dict) -> List[str]:
        """フェーズに適したチャンネル取得（シーケンシャル進行対応）- 文脈判定統合"""
        # タスク実行中の場合は指定チャンネルのみ
        active_tasks = self._get_active_tasks()
        if active_tasks:
            # タスクが実行中の場合、そのチャンネルのみで活動
            task_channels = []
            for task_info in active_tasks.values():
                task_channel = task_info.get('channel')
                if task_channel and task_channel in self.channel_ids:
                    task_channels.append(task_channel)
            return task_channels
        
        # デフォルト動作：フェーズ別チャンネル制御
        if phase == WorkflowPhase.ACTIVE:
            # 活動フェーズ：command-centerのみ
            default_channel = phase_settings.get("default_channel", "command_center")
            if default_channel in self.channel_ids:
                return [default_channel]
            return []
            
        elif phase == WorkflowPhase.FREE:
            # 終了フェーズ：loungeのみ
            preferred_channels = phase_settings.get("preferred_channels", ["lounge"])
            available = []
            for channel_name in preferred_channels:
                if channel_name in self.channel_ids:
                    available.append(channel_name)
            return available
            
        return []
        
    def _select_phase_appropriate_channel(self, available_channels: List[str], phase_settings: Dict) -> str:
        """フェーズに適したチャンネル選択（シーケンシャル進行：単一チャンネル制御）"""
        # シーケンシャル進行のため、利用可能な最初のチャンネルを選択
        # available_channelsは既にフェーズとタスク状態に基づいて適切にフィルタ済み
        return available_channels[0] if available_channels else "command_center"
        
    def _select_phase_appropriate_agent(self, channel: str, phase: WorkflowPhase, phase_settings: Dict) -> str:
        """フェーズとチャンネルに適したエージェント選択（連続発言防止）"""
        phase_preferred = phase_settings.get("preferred_agents", ["spectra", "lynq", "paz"])
        
        try:
            channel_type = ChannelType(channel)
            channel_preferred = self.channel_agent_preferences.get(channel_type, ["spectra", "lynq", "paz"])
        except ValueError:
            channel_preferred = ["spectra", "lynq", "paz"]
            
        # フェーズ優先度とチャンネル優先度を組み合わせ
        combined_preferences = []
        for agent in ["spectra", "lynq", "paz"]:
            phase_priority = 1.0 if agent in phase_preferred else 0.3
            channel_priority = 1.0 if agent in channel_preferred else 0.5
            
            # 前回発言者の場合は重みを大幅に下げる（連続発言防止）
            if agent == self.last_speaker:
                diversity_penalty = 0.1  # 90%重み削減
            else:
                diversity_penalty = 1.0
                
            combined_priority = phase_priority * channel_priority * diversity_penalty
            combined_preferences.append((agent, combined_priority))
            
        # 重み付き選択
        agents, weights = zip(*combined_preferences)
        selected_agent = random.choices(agents, weights=weights)[0]
        
        # 選択されたエージェントを記録
        self.last_speaker = selected_agent
        logger.debug(f"🎯 Agent selected: {selected_agent} (last: {self.last_speaker})")
        
        return selected_agent
        
    def _generate_phase_appropriate_message(self, agent: str, phase: WorkflowPhase) -> str:
        """フェーズに適したメッセージ生成（会議モード vs 実務モード）"""
        # 実務モード検知
        active_tasks = self._get_active_tasks()
        
        if active_tasks:
            # 実務モード：タスク関連メッセージを生成
            work_message = self._generate_work_mode_message(agent, active_tasks)
            if work_message:
                logger.debug(f"実務モードメッセージ: {agent}")
                return work_message
        
        # デフォルト：会議モードメッセージ
        if phase == WorkflowPhase.ACTIVE:
            meeting_message = self.personality_generator.get_meeting_message(agent)
            logger.debug(f"会議モードメッセージ: {agent}")
            return meeting_message
        elif phase == WorkflowPhase.FREE:
            # loungeでの自由なメッセージ
            base_message = self.personality_generator.get_random_message(agent)
            logger.debug(f"loungeメッセージ: {agent}")
            return base_message
        else:
            # その他フェーズ
            base_message = self.personality_generator.get_random_message(agent)
            logger.debug(f"標準メッセージ: {agent} - {phase.value}")
            return base_message

    def _get_active_tasks(self) -> Dict:
        """アクティブなタスク情報を取得"""
        try:
            if self.workflow_system and hasattr(self.workflow_system, 'current_tasks'):
                return self.workflow_system.current_tasks
            return {}
        except Exception as e:
            logger.debug(f"Failed to get active tasks: {e}")
            return {}
    
    def _apply_work_mode_channel_preferences(self, preferred_channels: List[str], task_channels: List[str]) -> List[str]:
        """実務モード時のチャンネル優先度調整"""
        # タスクが割り当てられているチャンネルを最優先に
        enhanced_preferences = list(task_channels)
        
        # 既存の優先チャンネルも追加（重複排除）
        for channel in preferred_channels:
            if channel not in enhanced_preferences:
                enhanced_preferences.append(channel)
                
        return enhanced_preferences
    
    def _generate_work_mode_message(self, agent: str, active_tasks: Dict) -> Optional[str]:
        """実務モード専用メッセージ生成"""
        try:
            if not active_tasks:
                return None
            
            # エージェント別の実務モードメッセージテンプレート
            work_messages = {
                "spectra": [
                    "💼 **進捗確認** 現在進行中のタスクの状況はいかがですか？何かサポートが必要でしたらお声かけください。",
                    "📊 **リソース配分チェック** タスクに必要なリソースは十分確保できていますか？",
                    "🎯 **目標達成支援** 設定されたタスクに向けて順調に進んでいますか？調整が必要でしたら一緒に検討しましょう。",
                    "⏰ **スケジュール確認** タスクの進行スケジュールに問題はありませんか？"
                ],
                "lynq": [
                    "🔧 **技術的支援** 実装中の技術課題でお困りのことはありませんか？",
                    "🧪 **品質保証** コードのテストやレビューが必要でしたらお手伝いします。", 
                    "⚙️ **アーキテクチャ検討** 設計や実装方針で検討したい点はありませんか？",
                    "📈 **パフォーマンス最適化** システムの効率化や改善点があれば分析してみましょう。"
                ],
                "paz": [
                    "🎨 **創造的アプローチ** 新しいアイデアや創造的な解決策をお探しですか？",
                    "✨ **インスピレーション** クリエイティブな作業で行き詰まりを感じていませんか？",
                    "🌟 **デザイン検討** UIやUXの改善アイデアがございましたら一緒に考えましょう。",
                    "💡 **革新的発想** 従来とは異なるアプローチで解決できる課題はありませんか？"
                ]
            }
            
            agent_messages = work_messages.get(agent, work_messages["spectra"])
            return random.choice(agent_messages)
            
        except Exception as e:
            logger.error(f"Work mode message generation failed: {e}")
            return None

    def _get_available_channels(self) -> List[str]:
        """会話中でないチャンネル一覧取得（従来版・互換性維持）"""
        available = []
        
        for channel_name, channel_id in self.channel_ids.items():
            if not self.conversation_detector.is_conversation_active(str(channel_id)):
                available.append(channel_name)
                
        return available
        
    def _select_agent_for_channel(self, channel_name: str) -> str:
        """チャンネル別エージェント選択"""
        try:
            channel_type = ChannelType(channel_name)
            preferences = self.channel_agent_preferences.get(channel_type, ["spectra", "lynq", "paz"])
            
            # 重み付きランダム選択（最優先50%, 2番目30%, 3番目20%）
            weights = [0.5, 0.3, 0.2]
            selected_agent = random.choices(preferences, weights=weights)[0]
            
            return selected_agent
            
        except ValueError:
            # 未定義チャンネルの場合はランダム
            return random.choice(["spectra", "lynq", "paz"])
            
    async def _can_post_autonomous_message(self) -> bool:
        """グローバル10秒ルールチェック - 最後の自発発言から10秒経過しているか"""
        try:
            with open("message_queue.json", "r", encoding='utf-8') as f:
                queue_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return True  # キューファイルがない場合は投稿可能
        
        # 最新の自発発言メッセージのタイムスタンプを取得
        autonomous_messages = [
            item for item in queue_data 
            if item.get('event_type') == 'autonomous_speech'
        ]
        
        if not autonomous_messages:
            return True  # 自発発言がない場合は投稿可能
        
        # 最新メッセージのタイムスタンプを取得
        latest_message = max(autonomous_messages, key=lambda x: x.get('timestamp', '1970-01-01'))
        latest_timestamp = datetime.fromisoformat(latest_message.get('timestamp', '1970-01-01'))
        
        # 10秒経過チェック
        time_since_last = datetime.now() - latest_timestamp
        return time_since_last >= timedelta(seconds=10)

    async def _queue_autonomous_message(self, channel: str, agent: str, message: str, phase: WorkflowPhase = None):
        """ワークフロー統合型自発メッセージをPriorityQueueに追加"""
        if not self.priority_queue:
            logger.error("PriorityQueue が設定されていません")
            return
        
        try:
            # 擬似Discordメッセージオブジェクト作成
            from types import SimpleNamespace
            
            # チャンネルオブジェクト
            mock_channel = SimpleNamespace()
            mock_channel.id = self.channel_ids.get(channel, 0)
            mock_channel.name = channel
            
            # 作者オブジェクト (自発発言システム)
            mock_author = SimpleNamespace()
            mock_author.id = 999999999999999999
            mock_author.name = f"AUTONOMOUS_{agent.upper()}"
            mock_author.bot = False  # メッセージ処理ループで処理されるように
            
            # ギルドオブジェクト
            mock_guild = SimpleNamespace()
            mock_guild.name = "SitoVerse"
            mock_guild.id = 1364600225028640920
            
            # 擬似メッセージオブジェクト
            mock_message = SimpleNamespace()
            mock_message.id = int(f"999{datetime.now().strftime('%Y%m%d%H%M%S')}")
            mock_message.content = message
            mock_message.author = mock_author
            mock_message.channel = mock_channel
            mock_message.guild = mock_guild
            mock_message.created_at = datetime.now()
            
            # 自発発言マーカー追加
            mock_message.autonomous_speech = True
            mock_message.target_agent = agent
            mock_message.workflow_phase = phase.value if phase else None
            
            # メッセージデータ構築
            message_data = {
                'message': mock_message,
                'priority': 5,  # 中優先度
                'timestamp': datetime.now(),
                'event_type': 'autonomous_speech',
                'target_agent': agent,
                'workflow_phase': phase.value if phase else None
            }
            
            # PriorityQueueに追加
            await self.priority_queue.enqueue(message_data)
            logger.info(f"🎙️ 統合版自発発言: {agent} -> #{channel} (phase: {phase.value if phase else 'none'})")
            
        except Exception as e:
            logger.error(f"統合版自発メッセージキューイングエラー: {e}")
        
    def notify_user_activity(self, channel_id: str):
        """ユーザー活動通知（外部から呼び出し）"""
        self.conversation_detector.update_user_activity(channel_id, datetime.now())
        logger.debug(f"👤 User activity detected in channel {channel_id}")
        
    def get_system_status(self) -> Dict:
        """システム状態取得"""
        return {
            "is_running": self.is_running,
            "environment": self.environment.value,
            "speech_probability": self.speech_probability,
            "tick_interval_seconds": self.tick_interval,
            "active_conversations": {
                channel_id: self.conversation_detector.is_conversation_active(channel_id)
                for channel_id in map(str, self.channel_ids.values())
            }
        }
    """
    簡素化された自発発言システム - TDD実装版
    
    要件：
    - REST(00:00-06:59): 自発発言無効
    - MEETING(07:00-19:59): lounge以外で自発発言有効
    - CONCLUSION(20:00-23:59): loungeのみで自発発言有効
    - チャンネル頻度優先度: LynQ→development 50%, Paz→creation 50%
    """
    
    def __init__(self, channel_ids: Dict[str, int], environment: str = "production", priority_queue=None):
        self.channel_ids = channel_ids
        self.environment = Environment(environment.lower())
        self.speech_probability = self._get_speech_probability()
        self.tick_interval = 10 if self.environment == Environment.TEST else 300
        self.priority_queue = priority_queue
        
        # 簡素化されたフェーズ設定
        self.phase_settings = {
            WorkflowPhase.REST: {"enabled": False},
            WorkflowPhase.PREPARATION: {"enabled": False},
            WorkflowPhase.MEETING: {
                "enabled": True,
                "excluded_channels": ["lounge"]
            },
            WorkflowPhase.CONCLUSION: {
                "enabled": True,
                "included_channels": ["lounge"]
            }
        }
        
        # チャンネル頻度設定
        self.frequency_config = {
            "lynq": {"development": 0.5, "others": 0.25},
            "paz": {"creation": 0.5, "others": 0.25},
            "spectra": {"all": 1.0/3}
        }
        
        # 会話検知システム（モック対応）
        self.conversation_detector = ConversationDetector()
        
        # 自発発言ループタスク
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
    
    def _get_speech_probability(self) -> float:
        """環境別発言確率設定"""
        probability_map = {
            Environment.TEST: 1.0,
            Environment.DEVELOPMENT: 1.0,
            Environment.PRODUCTION: 0.33
        }
        return probability_map.get(self.environment, 0.33)
    
    def get_current_phase(self) -> WorkflowPhase:
        """現在のワークフローフェーズを取得"""
        current_time = datetime.now().time()
        hour = current_time.hour
        minute = current_time.minute
        
        # PREPARATION期間の判定を最初に行う
        if hour == 6 and minute >= 55:
            return WorkflowPhase.PREPARATION
        elif hour == 0 and minute == 0:
            return WorkflowPhase.REST
        elif hour >= 0 and hour < 7:
            return WorkflowPhase.REST
        elif hour >= 7 and hour < 20:
            return WorkflowPhase.MEETING
        elif hour >= 20:
            return WorkflowPhase.CONCLUSION
        else:
            return WorkflowPhase.REST
    
    def should_speak_autonomously(self) -> bool:
        """現在のフェーズで自発発言が有効かチェック"""
        current_phase = self.get_current_phase()
        return self.phase_settings.get(current_phase, {}).get("enabled", False)
    
    def get_available_channels(self) -> List[str]:
        """現在のフェーズで利用可能なチャンネル一覧を取得"""
        current_phase = self.get_current_phase()
        phase_config = self.phase_settings.get(current_phase, {})
        
        if not phase_config.get("enabled", False):
            return []
        
        all_channels = list(self.channel_ids.keys())
        
        # MEETING期間：lounge以外
        if current_phase == WorkflowPhase.MEETING:
            excluded = phase_config.get("excluded_channels", [])
            available = [ch for ch in all_channels if ch not in excluded]
        # CONCLUSION期間：loungeのみ
        elif current_phase == WorkflowPhase.CONCLUSION:
            included = phase_config.get("included_channels", all_channels)
            available = [ch for ch in all_channels if ch in included]
        else:
            available = all_channels
        
        # 会話中のチャンネルを除外
        final_available = []
        for channel in available:
            channel_id = str(self.channel_ids.get(channel, 0))
            if not self.conversation_detector.is_conversation_active(channel_id):
                final_available.append(channel)
        
        return final_available
    
    def select_agent_for_channel(self, channel: str) -> str:
        """チャンネルに応じたエージェント選択（頻度制御）"""
        import random
        
        # LynQ development優先：50%
        if channel == "development":
            rand = random.random()
            if rand < 0.5:
                return "lynq"
            elif rand < 0.75:
                return "spectra"
            else:
                return "paz"
        
        # Paz creation優先：50%
        elif channel == "creation":
            rand = random.random()
            if rand < 0.5:
                return "paz"
            elif rand < 0.75:
                return "spectra"
            else:
                return "lynq"
        
        # その他のチャンネル：LynQ 25%, Paz 25%, Spectra 50%
        else:
            rand = random.random()
            if rand < 0.25:
                return "lynq"
            elif rand < 0.5:
                return "paz"
            else:
                return "spectra"
    
    def can_post_autonomous_message(self) -> bool:
        """10秒ルールチェック"""
        try:
            with open("message_queue.json", "r", encoding='utf-8') as f:
                queue_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return True
        
        # 最新の自発発言メッセージのタイムスタンプを取得
        autonomous_messages = [
            item for item in queue_data 
            if item.get('event_type') == 'autonomous_speech'
        ]
        
        if not autonomous_messages:
            return True
        
        latest_message = max(autonomous_messages, key=lambda x: x.get('timestamp', '1970-01-01'))
        latest_timestamp = datetime.fromisoformat(latest_message.get('timestamp', '1970-01-01'))
        
        time_since_last = datetime.now() - latest_timestamp
        return time_since_last >= timedelta(seconds=10)
    
    async def queue_autonomous_message(self, channel: str, agent: str, message: str) -> bool:
        """自発メッセージをPriorityQueueに追加"""
        if not self.priority_queue:
            logger.error("PriorityQueue が設定されていません")
            return False
        
        try:
            # 擬似Discordメッセージオブジェクト作成
            from types import SimpleNamespace
            
            # チャンネルオブジェクト
            mock_channel = SimpleNamespace()
            mock_channel.id = self.channel_ids.get(channel, 0)
            mock_channel.name = channel
            
            # 作者オブジェクト (自発発言システム)
            mock_author = SimpleNamespace()
            mock_author.id = 999999999999999999
            mock_author.name = f"AUTONOMOUS_{agent.upper()}"
            mock_author.bot = False  # メッセージ処理ループで処理されるように
            
            # ギルドオブジェクト
            mock_guild = SimpleNamespace()
            mock_guild.name = "SitoVerse"
            mock_guild.id = 1364600225028640920
            
            # 擬似メッセージオブジェクト
            mock_message = SimpleNamespace()
            mock_message.id = int(f"999{datetime.now().strftime('%Y%m%d%H%M%S')}")
            mock_message.content = message
            mock_message.author = mock_author
            mock_message.channel = mock_channel
            mock_message.guild = mock_guild
            mock_message.created_at = datetime.now()
            
            # 自発発言マーカー追加
            mock_message.autonomous_speech = True
            mock_message.target_agent = agent
            
            # メッセージデータ構築
            message_data = {
                'message': mock_message,
                'priority': 5,  # 中優先度
                'timestamp': datetime.now(),
                'event_type': 'autonomous_speech',
                'target_agent': agent
            }
            
            # PriorityQueueに追加
            await self.priority_queue.enqueue(message_data)
            return True
            
        except Exception as e:
            logger.error(f"自発メッセージキューイングエラー: {e}")
            return False
    
    def generate_personality_message(self, agent: str) -> str:
        """エージェント別パーソナリティメッセージ生成"""
        return AgentPersonalityGenerator.get_random_message(agent)
    
    def get_phase_settings(self) -> Dict:
        """フェーズ設定を取得"""
        return self.phase_settings
    
    def get_frequency_configuration(self) -> Dict:
        """頻度設定を取得"""
        return self.frequency_config
    
    def get_speech_probability(self) -> float:
        """発言確率を取得"""
        return self.speech_probability
    
    def get_tick_interval(self) -> int:
        """ティック間隔を取得"""
        return self.tick_interval
    
    def get_system_status(self) -> Dict:
        """システム状態を取得"""
        return {
            "is_running": self.is_running,
            "environment": self.environment.value,
            "speech_probability": self.speech_probability,
            "tick_interval_seconds": self.tick_interval,
            "current_phase": self.get_current_phase().value
        }
    
    async def start(self):
        """簡素化版自発発言システム開始"""
        if self.is_running:
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._speech_loop())
        logger.info("🚀 SimplifiedAutonomousSpeechSystem 開始")
        
    async def stop(self):
        """簡素化版自発発言システム停止"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ SimplifiedAutonomousSpeechSystem 停止")
        
    async def _speech_loop(self):
        """簡素化版自発発言ループ"""
        logger.info("🔄 Simplified autonomous speech loop started")
        
        while self.is_running:
            try:
                # 環境別ティック間隔
                await asyncio.sleep(self.tick_interval)
                
                # 確率判定
                if random.random() <= self.speech_probability:
                    await self._execute_simplified_autonomous_speech()
                else:
                    logger.debug(f"🎲 確率判定失敗: {self.speech_probability * 100:.0f}%")
                    
            except Exception as e:
                logger.error(f"❌ Simplified autonomous speech loop error: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機
                
    async def _execute_simplified_autonomous_speech(self):
        """簡素化版自発発言実行"""
        try:
            # フェーズベース制御
            if not self.should_speak_autonomously():
                current_phase = self.get_current_phase()
                logger.debug(f"🚫 現在のフェーズ {current_phase.value} では自発発言無効")
                return
            
            # 10秒ルールチェック
            if not self.can_post_autonomous_message():
                logger.debug("🚫 10秒ルール: まだ前回から10秒経過していません")
                return
            
            # 利用可能チャンネル取得
            available_channels = self.get_available_channels()
            if not available_channels:
                logger.debug("💬 利用可能なチャンネルがありません")
                return
            
            # チャンネル選択
            channel = random.choice(available_channels)
            
            # エージェント選択（チャンネル頻度考慮）
            agent = self.select_agent_for_channel(channel)
            
            # パーソナリティメッセージ生成
            message = self.generate_personality_message(agent)
            
            # メッセージキューに追加
            success = await self.queue_autonomous_message(channel, agent, message)
            
            if success:
                logger.info(f"🎙️ 簡素化版自発発言: {agent} -> #{channel}")
            else:
                logger.error("❌ メッセージキューへの追加に失敗")
                
        except Exception as e:
            logger.error(f"❌ 簡素化版自発発言実行エラー: {e}")
    
    def can_post_autonomous_message(self) -> bool:
        """10秒ルール：前回の自発発言から10秒経過チェック"""
        try:
            with open("message_queue.json", "r", encoding='utf-8') as f:
                queue_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return True
        
        # 最後の自発発言を検索
        last_autonomous = None
        for item in reversed(queue_data):
            if item.get('event_type') == 'autonomous_speech':
                last_autonomous = item
                break
        
        if not last_autonomous:
            return True
        
        # 10秒経過チェック
        last_time = datetime.fromisoformat(last_autonomous['timestamp'])
        time_diff = (datetime.now() - last_time).total_seconds()
        
        return time_diff >= 10.0
    
    def notify_user_activity(self, channel_id: str):
        """ユーザー活動通知（会話中断回避）"""
        self.conversation_detector.update_user_activity(channel_id, datetime.now())
    
    async def start(self):
        """自発発言システム開始"""
        if self.is_running:
            logger.warning("SimplifiedAutonomousSpeechSystem は既に動作中です")
            return
            
        self.is_running = True
        self.task = asyncio.create_task(self._speech_loop())
        logger.info("🚀 SimplifiedAutonomousSpeechSystem 開始")
        
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
        logger.info("⏹️ SimplifiedAutonomousSpeechSystem 停止")
        
    async def _speech_loop(self):
        """自発発言メインループ"""
        logger.info("🔄 Simplified autonomous speech loop started")
        
        while self.is_running:
            try:
                await asyncio.sleep(self.tick_interval)
                
                # フェーズチェック
                if not self.should_speak_autonomously():
                    logger.debug(f"🚫 現在のフェーズ {self.get_current_phase().value} では自発発言無効")
                    continue
                
                # 確率判定
                import random
                if random.random() > self.speech_probability:
                    logger.debug(f"🎲 確率判定失敗: {self.speech_probability * 100:.0f}%")
                    continue
                
                # 10秒ルールチェック
                if not self.can_post_autonomous_message():
                    logger.debug("🚫 10秒ルール: まだ前回から10秒経過していません")
                    continue
                
                # チャンネル選択
                available_channels = self.get_available_channels()
                if not available_channels:
                    logger.debug("💬 利用可能なチャンネルがありません")
                    continue
                
                selected_channel = random.choice(available_channels)
                selected_agent = self.select_agent_for_channel(selected_channel)
                message = self.generate_personality_message(selected_agent)
                
                # メッセージキューに追加
                success = await self.queue_autonomous_message(selected_channel, selected_agent, message)
                if success:
                    logger.info(f"🎙️ 簡素化版自発発言: {selected_agent} -> #{selected_channel}")
                
            except Exception as e:
                logger.error(f"❌ Simplified autonomous speech loop error: {e}")
                await asyncio.sleep(60)


# システム統合用のファクトリー関数
def create_autonomous_speech_system(
    channel_ids: Dict[str, int], 
    environment: str = None,
    workflow_system = None
) -> AutonomousSpeechSystem:
    """Workflow統合型 Autonomous Speech System のインスタンス作成"""
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'production')
    
    return AutonomousSpeechSystem(channel_ids, environment, workflow_system)

def create_simplified_autonomous_speech_system(
    channel_ids: Dict[str, int], 
    environment: str = None
) -> SimplifiedAutonomousSpeechSystem:
    """簡素化版 Autonomous Speech System のインスタンス作成"""
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'production')
    
    return SimplifiedAutonomousSpeechSystem(channel_ids, environment)

if __name__ == "__main__":
    # テスト実行
    async def test_autonomous_speech():
        channel_ids = {
            "command_center": 1383963657137946664,
            "lounge": 1383966355962990653,
            "development": 1383968516033478727,
            "creation": 1383981653046726728
        }
        
        speech_system = AutonomousSpeechSystem(channel_ids, environment="test")
        await speech_system.start()
        
        # テスト用に短時間実行
        await asyncio.sleep(120)  # 2分間テスト
        await speech_system.stop()
    
    asyncio.run(test_autonomous_speech())