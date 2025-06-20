#!/usr/bin/env python3
"""
Autonomous Speech System - 5分間隔自発発言システム

AC-016: Autonomous Speech System の実装
- 5-minute tick-based scheduling
- Environment-specific probability (test: 100%, prod: 33%)
- Channel-specific agent selection
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

class ConversationDetector:
    """会話検知システム"""
    
    def __init__(self, silence_threshold_minutes: int = 10):
        self.silence_threshold = timedelta(minutes=silence_threshold_minutes)
        self.last_user_activity: Dict[str, datetime] = {}
        
    def update_user_activity(self, channel_id: str, timestamp: datetime):
        """ユーザー活動を記録"""
        self.last_user_activity[channel_id] = timestamp
        
    def is_conversation_active(self, channel_id: str) -> bool:
        """会話がアクティブかチェック"""
        if channel_id not in self.last_user_activity:
            return False
            
        last_activity = self.last_user_activity[channel_id]
        time_since_activity = datetime.now() - last_activity
        
        return time_since_activity < self.silence_threshold

class AgentPersonalityGenerator:
    """エージェント個性メッセージ生成"""
    
    SPECTRA_MESSAGES = [
        "💼 **進捗確認** 皆さん、今日のタスクの調子はいかがですか？何かサポートが必要でしたらお声かけください！",
        "📊 **リソース状況チェック** プロジェクトのリソース配分は適切でしょうか？効率化のご提案があれば喜んでお手伝いします。",
        "🎯 **目標達成サポート** 今週の目標に向けて順調に進んでいますか？調整が必要な点があれば一緒に検討しましょう。",
        "🤝 **チーム連携促進** 各部門間の情報共有はスムーズですか？コミュニケーションの改善点があれば教えてください。",
        "📋 **タスク優先順位** 現在のタスクの優先順位は適切でしょうか？再調整が必要でしたらご相談ください。"
    ],
    
    LYNQ_MESSAGES = [
        "🔍 **技術的検証** 最近のシステム実装で気になる点はありませんか？パフォーマンスやセキュリティの観点から確認しましょう。",
        "⚙️ **アーキテクチャ最適化** 現在の設計で改善できる部分があれば、一緒に分析してみませんか？",
        "🧪 **テスト戦略** 実装したコードのテストカバレッジは十分でしょうか？品質保証の観点から検討してみましょう。",
        "📈 **メトリクス分析** システムのパフォーマンス指標を確認しましょう。ボトルネックや改善点はありませんか？",
        "🔧 **実装効率化** 開発プロセスで自動化できる部分はありませんか？ツールやワークフローの改善を検討しましょう。"
    ],
    
    PAZ_MESSAGES = [
        "✨ **創造的インスピレーション** 新しいアイデアが浮かんでいませんか？どんな小さな閃きでも大歓迎です！",
        "🎨 **アート的発想** 今日は何か美しいものや面白いものに出会いましたか？創造性を刺激する体験を共有しませんか？",
        "💡 **ブレインストーミング** 解決が困難な課題があれば、一緒に発散的思考で新しい角度から考えてみましょう！",
        "🌈 **想像力拡張** 既存の枠組みを超えた斬新なアプローチはありませんか？自由な発想で可能性を探ってみましょう。",
        "🚀 **革新的チャレンジ** 誰もやったことがない新しい試みを考えてみませんか？リスクを恐れず、創造的に挑戦しましょう！"
    ]

    @classmethod
    def get_random_message(cls, agent: str) -> str:
        """エージェント別ランダムメッセージ取得"""
        messages_map = {
            "spectra": cls.SPECTRA_MESSAGES,
            "lynq": cls.LYNQ_MESSAGES,
            "paz": cls.PAZ_MESSAGES
        }
        
        if agent not in messages_map:
            return "🤖 システムからの自動メッセージです。"
            
        return random.choice(messages_map[agent])

class AutonomousSpeechSystem:
    """5分間隔自発発言システム"""
    
    def __init__(self, channel_ids: Dict[str, int], environment: str = "production"):
        self.channel_ids = channel_ids
        self.environment = Environment(environment.lower())
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        
        # 環境別設定（テスト時は頻度上げる）
        self.speech_probability = self._get_speech_probability()
        self.tick_interval = 10 if self.environment == Environment.TEST else 300  # テスト:10秒, 本番:5分
        
        # システムコンポーネント
        self.conversation_detector = ConversationDetector(silence_threshold_minutes=10)
        self.personality_generator = AgentPersonalityGenerator()
        
        # チャンネル別エージェント優先度
        self.channel_agent_preferences = {
            ChannelType.COMMAND_CENTER: ["spectra", "lynq", "paz"],  # Spectra優先
            ChannelType.LOUNGE: ["paz", "spectra", "lynq"],         # Paz優先
            ChannelType.DEVELOPMENT: ["lynq", "spectra", "paz"],    # LynQ優先
            ChannelType.CREATION: ["paz", "lynq", "spectra"]        # Paz優先
        }
        
        logger.info(f"🎙️ Autonomous Speech System initialized for {self.environment.value}")
        logger.info(f"📊 Speech probability: {self.speech_probability * 100:.0f}%")
        
    def _get_speech_probability(self) -> float:
        """環境別発言確率設定"""
        probability_map = {
            Environment.TEST: 1.0,        # 100%
            Environment.DEVELOPMENT: 1.0,  # 100% (開発時はテスト同様)
            Environment.PRODUCTION: 0.33   # 33%
        }
        return probability_map.get(self.environment, 0.33)
        
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
        """自発発言実行 - 真の10秒ルール実装"""
        try:
            # グローバル最後発言時刻チェック
            if not await self._can_post_autonomous_message():
                logger.debug("🚫 10秒ルール: まだ前回から10秒経過していません")
                return
            
            # アクティブでないチャンネルを特定
            available_channels = self._get_available_channels()
            
            if not available_channels:
                logger.info("💬 All channels have active conversations, skipping autonomous speech")
                return
                
            # チャンネル選択（ランダム）
            selected_channel = random.choice(available_channels)
            
            # チャンネル別エージェント選択
            selected_agent = self._select_agent_for_channel(selected_channel)
            
            # パーソナリティメッセージ生成
            message = self.personality_generator.get_random_message(selected_agent)
            
            # メッセージキューに追加（グローバルタイムスタンプ更新含む）
            await self._queue_autonomous_message(selected_channel, selected_agent, message)
            
            logger.info(f"🎙️ Autonomous speech executed: {selected_agent} -> #{selected_channel}")
            
        except Exception as e:
            logger.error(f"❌ Autonomous speech execution failed: {e}")
            
    def _get_available_channels(self) -> List[str]:
        """会話中でないチャンネル一覧取得"""
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

    async def _queue_autonomous_message(self, channel: str, agent: str, message: str):
        """自発メッセージをキューに追加 - 真の10秒ルール対応"""
        # キューファイル読み込み
        try:
            with open("message_queue.json", "r", encoding='utf-8') as f:
                queue_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            queue_data = []
        
        # 古い処理済みメッセージを削除（5分以上前）
        cutoff_time = datetime.now() - timedelta(minutes=5)
        queue_data = [item for item in queue_data 
                     if not (item.get('processed', False) 
                            and item.get('event_type') == 'autonomous_speech'
                            and datetime.fromisoformat(item.get('timestamp', '1970-01-01')) < cutoff_time)]
        
        # キューサイズ制限（最大20件に削減）
        if len(queue_data) >= 20:
            logger.warning(f"⚠️ キューサイズ制限に達しているため、自発メッセージ追加をスキップ: {len(queue_data)}件")
            return
        
        # 未処理の自発発言メッセージがあるかチェック
        unprocessed_autonomous = [
            item for item in queue_data 
            if item.get('event_type') == 'autonomous_speech' 
            and not item.get('processed', False)
        ]
        
        if unprocessed_autonomous:
            logger.info(f"🚫 未処理自発メッセージが{len(unprocessed_autonomous)}件存在するため、新規追加をスキップ")
            return
        
        queue_item = {
            'id': f"autonomous_{agent}_{datetime.now().isoformat()}",
            'content': message,
            'author': 'AUTONOMOUS_SYSTEM',
            'author_id': '999999999999999999',  # システム識別ID
            'channel_id': str(self.channel_ids.get(channel, 0)),
            'channel_name': channel,
            'target_agent': agent,
            'timestamp': datetime.now().isoformat(),
            'processed': False,
            'priority': 5,  # 自発発言は最低優先度
            'event_type': 'autonomous_speech',
            'speech_probability': self.speech_probability,
            'global_timing_enforced': True  # 真の10秒ルール適用済みフラグ
        }
        
        queue_data.append(queue_item)
        
        with open("message_queue.json", "w", encoding='utf-8') as f:
            json.dump(queue_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"📝 Autonomous message queued (10s rule enforced): {agent} -> #{channel}")
        
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

# システム統合用のファクトリー関数
def create_autonomous_speech_system(
    channel_ids: Dict[str, int], 
    environment: str = None
) -> AutonomousSpeechSystem:
    """Autonomous Speech System のインスタンス作成"""
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'production')
    
    return AutonomousSpeechSystem(channel_ids, environment)

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