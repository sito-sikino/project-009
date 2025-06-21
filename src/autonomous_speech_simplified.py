#!/usr/bin/env python3
"""
Autonomous Speech System - Workflow統合型自発発言システム（LLM統合版）

AC-016: Autonomous Speech System の実装
- Daily Workflow統合：フェーズ別行動制御
- tick-based scheduling（フェーズ依存）
- LLM統合型エージェント選択・メッセージ生成
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
        
        logger.info(f"🎙️ LLM統合型 Autonomous Speech System initialized for {self.environment.value}")
        logger.info(f"📊 Speech probability: {self.speech_probability * 100:.0f}%")
        logger.info(f"⏱️ Tick interval: {self.tick_interval}秒")
        
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
        """LLM統合型自発発言実行"""
        try:
            # 現在のフェーズ確認
            current_phase = self._get_current_phase()
            
            # フェーズ別の発言可否チェック
            if current_phase == WorkflowPhase.STANDBY:
                logger.debug("🚫 STANDBY期間中のため自発発言をスキップ")
                return
                
            # 利用可能なチャンネル取得
            available_channel = self._get_available_channel(current_phase)
            if not available_channel:
                logger.debug("🚫 利用可能なチャンネルがないため自発発言をスキップ")
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
            
            # 発言情報を記録
            self.last_speech_info = {
                "agent": speech_data["agent"],
                "channel": available_channel,
                "timestamp": datetime.now()
            }
            
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
        """フェーズに応じた利用可能チャンネル取得"""
        # タスク実行中チェック
        if self.workflow_system and hasattr(self.workflow_system, 'current_tasks'):
            active_tasks = self.workflow_system.current_tasks
            if active_tasks:
                # タスクチャンネルを優先
                for task_info in active_tasks.values():
                    return task_info.get('channel')
        
        # フェーズ別デフォルトチャンネル
        if phase == WorkflowPhase.ACTIVE:
            return "command_center"
        elif phase == WorkflowPhase.FREE:
            return "lounge"
        
        return None
        
    async def _generate_llm_integrated_speech(self, channel: str, phase: WorkflowPhase) -> Optional[Dict[str, str]]:
        """LLM統合型メッセージ生成（エージェント選択含む）"""
        # 実際のLLM呼び出しをシミュレート
        # 本実装では、ここでGemini APIを呼び出し、システムプロンプトで全てを制御
        
        # システムプロンプト（例）
        system_prompt = f"""
あなたはDiscordで活動する3つのエージェント（Spectra, LynQ, Paz）の統合システムです。
現在の状況に基づいて、最適なエージェントを選択し、そのエージェントとしてメッセージを生成してください。

現在の状況：
- 時刻: {datetime.now().strftime('%H:%M')}
- フェーズ: {phase.value}
- チャンネル: #{channel}
- 前回発言: {self.last_speech_info['agent'] or 'なし'} ({self._format_time_ago()})
- アクティブタスク: {self._get_active_tasks_summary()}

エージェント特性：
- Spectra: 組織化・進行管理・全体調整（command_center: 40%, その他: 均等）
- LynQ: 技術分析・論理的思考・実装支援（development: 50%, その他: 25%）
- Paz: 創造性・革新的アイデア・デザイン（creation: 50%, その他: 25%）

チャンネル別推奨重み：
- command_center: Spectra 40%, LynQ 30%, Paz 30%
- development: LynQ 50%, Spectra 25%, Paz 25%
- creation: Paz 50%, LynQ 25%, Spectra 25%
- lounge: 全員均等 33.3%

重要な制約：
1. 前回発言者とは異なるエージェントを強く推奨（90%の確率で別のエージェントを選択）
2. チャンネルに適したエージェントを優先
3. 現在のフェーズとタスクに応じた内容を生成

以下の形式で応答してください：
{{
  "agent": "選択したエージェント名",
  "message": "生成したメッセージ"
}}
"""
        
        # 本実装では実際のLLM呼び出しの代わりにシミュレーション
        # 実際にはここでGemini APIを呼び出す
        
        # シミュレーション：適切なエージェントとメッセージを選択
        agents = ["spectra", "lynq", "paz"]
        
        # 前回発言者を除外
        if self.last_speech_info["agent"]:
            agents = [a for a in agents if a != self.last_speech_info["agent"]]
        
        # チャンネル別の重み付け（簡易版）
        if channel == "development" and "lynq" in agents:
            selected_agent = "lynq"
        elif channel == "creation" and "paz" in agents:
            selected_agent = "paz"
        elif channel == "command_center" and "spectra" in agents:
            selected_agent = "spectra"
        else:
            selected_agent = random.choice(agents)
        
        # メッセージ生成（簡易版）
        messages = {
            "spectra": [
                "📊 **進捗確認** 現在の作業状況はいかがですか？何かサポートが必要でしたらお声かけください。",
                "🎯 **目標確認** 今日の目標に向けて順調に進んでいますか？調整が必要な点があれば一緒に検討しましょう。"
            ],
            "lynq": [
                "🔍 **技術レビュー** 実装内容について技術的な観点から確認させていただけますか？",
                "⚙️ **最適化提案** システムのパフォーマンスや設計について改善点があれば議論しましょう。"
            ],
            "paz": [
                "✨ **アイデア共有** 新しいアプローチや創造的な解決策について考えてみませんか？",
                "🎨 **デザイン思考** ユーザー体験を向上させる革新的なアイデアはありませんか？"
            ]
        }
        
        selected_message = random.choice(messages.get(selected_agent, ["🤖 自動メッセージです。"]))
        
        return {
            "agent": selected_agent,
            "message": selected_message
        }
        
    def _format_time_ago(self) -> str:
        """前回発言からの経過時間をフォーマット"""
        if not self.last_speech_info["timestamp"]:
            return "初回"
        
        delta = datetime.now() - self.last_speech_info["timestamp"]
        minutes = int(delta.total_seconds() / 60)
        if minutes < 1:
            return "1分未満前"
        elif minutes < 60:
            return f"{minutes}分前"
        else:
            hours = minutes // 60
            return f"{hours}時間前"
            
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
            'message': AutonomousMessage(message, self.channel_ids.get(channel, 0), agent),
            'priority': 5,  # 自発発言は低優先度
            'timestamp': datetime.now()
        }
        
        await self.priority_queue.enqueue_dict(message_data)
        logger.info(f"📝 Autonomous message queued: {agent} -> #{channel}")