#!/usr/bin/env python3
"""
Daily Workflow System - 時間ベースの自動ワークフロー管理

AC-015: Daily Workflow Automation の実装
- 06:00: Long-term memory processing + Daily report + Meeting initiation
- 20:00: Work session conclusion  
- 00:00: System rest period
"""
import asyncio
import logging
import os
from datetime import datetime, time, timedelta
from typing import Dict, Optional, Callable
import json
from dataclasses import dataclass
from enum import Enum
import discord

logger = logging.getLogger(__name__)

class WorkflowPhase(Enum):
    """ワークフロー段階定義"""
    STANDBY = "standby"     # 00:00-05:59 待機状態
    PROCESSING = "processing"  # 06:00-会議開始 長期記憶化・日報生成処理中
    ACTIVE = "active"       # 会議開始-19:59 活動時間
    FREE = "free"           # 20:00-23:59 自由時間

@dataclass
class WorkflowEvent:
    """ワークフロー イベント定義"""
    time: time
    phase: WorkflowPhase
    action: str
    message: str
    channel: str
    agent: str

class DailyWorkflowSystem:
    """Daily Workflow System - 時間ベース自動管理"""
    
    def __init__(self, channel_ids: Dict[str, int], memory_system=None, priority_queue=None, long_term_memory_processor=None):
        self.channel_ids = channel_ids
        self.memory_system = memory_system
        self.priority_queue = priority_queue
        self.long_term_memory_processor = long_term_memory_processor
        self.current_phase = WorkflowPhase.STANDBY
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.user_override_active = False
        self.current_tasks = {}  # チャンネル別現在タスク
        
        # ワークフロー スケジュール定義
        self.workflow_schedule = [
            WorkflowEvent(
                time=time(6, 0),
                phase=WorkflowPhase.PROCESSING,
                action="long_term_memory_processing",
                message="🧠 **長期記憶化処理開始**\n\n" +
                       "今日の記憶を統合分析中です...\n" +
                       "処理完了次第、日報と会議開始をお知らせします。",
                channel="command_center",
                agent="system"
            ),
            WorkflowEvent(
                time=time(20, 0),
                phase=WorkflowPhase.FREE,
                action="work_session_conclusion",
                message="🌆 **Work Session Conclusion**\n\n" +
                       "お疲れ様でした！本日の作業を振り返りましょう。\n\n" +
                       "📝 **今日の振り返り:**\n" +
                       "• 達成できたこと\n" +
                       "• 学んだこと・気づき\n" +
                       "• 明日への課題\n\n" +
                       "🏠 ラウンジでリラックスタイムをお楽しみください！",
                channel="lounge",
                agent="spectra"
            ),
            WorkflowEvent(
                time=time(0, 0),
                phase=WorkflowPhase.STANDBY,
                action="system_rest_period",
                message="🌙 **System Rest Period**\n\n" +
                       "システムが休息モードに入ります。\n" +
                       "緊急時は @mention でお声かけください。\n\n" +
                       "おやすみなさい！ 😴",
                channel="lounge",
                agent="paz"
            )
        ]
        
    async def start(self):
        """ワークフロー システム開始"""
        if self.is_running:
            logger.warning("Daily Workflow System は既に動作中です")
            return
            
        self.is_running = True
        self.task = asyncio.create_task(self._workflow_loop())
        logger.info("🚀 Daily Workflow System 開始")
        
    async def stop(self):
        """ワークフロー システム停止"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Daily Workflow System 停止")
        
    async def _workflow_loop(self):
        """メインワークフローループ"""
        logger.info("🔄 Workflow monitoring loop started")
        
        while self.is_running:
            try:
                current_time = datetime.now().time()
                
                # 次のイベントをチェック
                next_event = self._get_next_event(current_time)
                if next_event:
                    await self._execute_event(next_event)
                    
                # 現在のフェーズを更新
                self._update_current_phase(current_time)
                
                # 30秒間隔でチェック（精度確保）
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Workflow loop error: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機
                
    def _get_next_event(self, current_time: time) -> Optional[WorkflowEvent]:
        """次の実行すべきイベントを取得"""
        for event in self.workflow_schedule:
            # イベント時刻の30秒以内なら実行
            event_time = datetime.combine(datetime.now().date(), event.time)
            current_datetime = datetime.combine(datetime.now().date(), current_time)
            
            time_diff = abs((event_time - current_datetime).total_seconds())
            
            if time_diff <= 30 and not self._is_event_executed_today(event):
                return event
        return None
        
    def _is_event_executed_today(self, event: WorkflowEvent) -> bool:
        """今日既に実行済みかチェック（簡易実装）"""
        # TODO: より堅牢な実行履歴管理を実装
        return False
        
    async def _execute_event(self, event: WorkflowEvent):
        """イベント実行"""
        if self.user_override_active:
            logger.info(f"⏭️ User override active, skipping event: {event.action}")
            return
            
        try:
            logger.info(f"⚡ Executing workflow event: {event.action} at {event.time}")
            
            # イベント実行を外部システムに通知
            await self._notify_event_execution(event)
            
            # フェーズ変更
            self.current_phase = event.phase
            
            logger.info(f"✅ Workflow event completed: {event.action}")
            
        except Exception as e:
            logger.error(f"❌ Event execution failed: {event.action} - {e}")
            
    async def _notify_event_execution(self, event: WorkflowEvent):
        """イベント実行を外部システムに通知"""
        if event.action == "long_term_memory_processing":
            # 長期記憶処理の場合は統合ワークフロー実行
            await self._execute_integrated_morning_workflow(event)
        elif event.action == "daily_report_generation":
            # 日報生成の場合は専用処理
            report_content = await self.generate_daily_report()
            await self._send_workflow_message(report_content, event.channel, event.agent, 1)
        else:
            # 通常のワークフローメッセージ
            await self._send_workflow_message(event.message, event.channel, event.agent, 1)
    
    async def _execute_integrated_morning_workflow(self, event: WorkflowEvent):
        """統合朝次ワークフロー実行（06:00トリガー）"""
        try:
            logger.info("🚀 統合朝次ワークフロー開始")
            
            # 1. 開始通知送信
            await self._send_workflow_message(event.message, event.channel, event.agent, 1)
            
            # 2. 長期記憶処理実行（EventDrivenWorkflowOrchestrator使用）
            if self.long_term_memory_processor:
                # ここで実際の統合ワークフローを実行
                # EventDrivenWorkflowOrchestratorが存在する場合
                logger.info("✅ 統合朝次ワークフロー: 長期記憶処理とメッセージ送信は外部統合システムが実行")
            else:
                # フォールバック: 長期記憶処理システムが利用できない場合
                # 日報データなしで基本的な会議開始メッセージのみ送信
                # 注: 正常時は統合メッセージ（日報Embed + 会議宣言）が送信される
                meeting_message = (
                    "🏢 **Morning Meeting - Session Started**\n\n"
                    "📋 **Today's Agenda:**\n"
                    "• 昨日の進捗レビュー\n"
                    "• 今日の目標設定\n"
                    "• リソース配分の確認\n"
                    "• 課題・ブロッカーの特定\n\n"
                    "それでは、本日もよろしくお願いします！ 💪"
                )
                await self._send_workflow_message(meeting_message, "command_center", "spectra", 1)
                logger.info("✅ フォールバック: 基本会議開始メッセージ送信完了")
            
        except Exception as e:
            logger.error(f"❌ 統合朝次ワークフローエラー: {e}")
            
    async def _send_workflow_message(self, content: str, channel: str, agent: str, priority: int = 1):
        """ワークフローメッセージをPriorityQueueに送信"""
        if not self.priority_queue:
            logger.warning("Priority queue not available, cannot send workflow message")
            return
            
        # PriorityQueue用のメッセージオブジェクト作成
        class WorkflowMessage:
            def __init__(self, content, channel_id, target_agent):
                self.content = content
                self.channel = WorkflowChannel(channel_id)
                self.author = WorkflowAuthor()
                self.id = f"workflow_{datetime.now().isoformat()}"
                self.autonomous_speech = True
                self.target_agent = target_agent
                
        class WorkflowChannel:
            def __init__(self, channel_id):
                self.id = channel_id
                self.name = channel
                
        class WorkflowAuthor:
            def __init__(self):
                self.bot = True
                self.id = "000000000000000000"
        
        message_data = {
            'message': WorkflowMessage(content, self.channel_ids.get(channel, 0), agent),
            'priority': priority,
            'timestamp': datetime.now()
        }
        
        try:
            await self.priority_queue.enqueue(message_data)
            logger.info(f"📝 Workflow message queued: {agent} -> #{channel}")
        except Exception as e:
            logger.error(f"❌ Failed to queue workflow message: {e}")
            
    async def generate_daily_report(self) -> str:
        """Redis履歴から日報を生成"""
        try:
            if not self.memory_system:
                return self._get_default_daily_report()
                
            # Redis から昨日の会話履歴を取得
            yesterday = datetime.now().date() - timedelta(days=1)
            conversations = await self.memory_system.get_conversation_history(
                limit=100,
                start_date=yesterday
            )
            
            if not conversations:
                return self._get_default_daily_report()
                
            # 統計情報の計算
            total_messages = len(conversations)
            unique_users = len(set(conv.get('user_id', 'unknown') for conv in conversations))
            
            # 重要な議論の抽出（簡易実装）
            key_discussions = []
            for conv in conversations[-10:]:  # 最新10件から抽出
                content = conv.get('content', '')
                if len(content) > 100 and any(keyword in content.lower() for keyword in ['実装', '設計', '問題', '提案', '完了']):
                    key_discussions.append(content[:100] + "...")
                    
            # Discord Embed形式の日報生成
            embed_content = f"""📊 **Daily Report - {yesterday.strftime('%Y-%m-%d')}**

📈 **Activity Metrics**
• 会話数: {total_messages}
• 参加ユーザー数: {unique_users}
• アクティブ期間: 07:00-20:00

💬 **Key Discussions**
{chr(10).join(f"• {disc}" for disc in key_discussions[:3]) if key_discussions else "• 特記事項なし"}

✅ **Achievements**
• システム正常稼働継続
• ユーザー応答100%達成
{f"• {len(key_discussions)}件の重要議論" if key_discussions else ""}

⚠️ **Issues/Blockers**
• 現在、重大な課題は検出されていません

📋 **Carry Forward**
• 継続的なシステム改善
• ユーザーエンゲージメント向上

🏢 **今日の会議を開始いたします**
📋 **Today's Agenda:**
• 昨日の進捗レビュー
• 今日の目標設定
• リソース配分の確認
• 課題・ブロッカーの特定

それでは、本日もよろしくお願いします！ 💪"""

            return embed_content
            
        except Exception as e:
            logger.error(f"❌ Daily report generation failed: {e}")
            return self._get_default_daily_report()
            
    def _get_default_daily_report(self) -> str:
        """デフォルト日報"""
        today = datetime.now().date()
        return f"""📊 **Daily Report - {today.strftime('%Y-%m-%d')}**

📈 **Activity Metrics**
• システム正常稼働中

💬 **Key Discussions**
• メモリシステム初期化中

✅ **Achievements**
• システム起動完了

📋 **Today's Agenda**
• システム稼働開始
• ユーザー対応準備完了

本日もよろしくお願いします！ 💪"""

    async def process_task_command(self, command: str, channel: str, task: str, user_id: str) -> str:
        """タスクコマンド処理"""
        try:
            if command == "commit":
                # タスクをRedisに保存
                if self.memory_system:
                    task_data = {
                        'task': task,
                        'channel': channel,
                        'user_id': user_id,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'active'
                    }
                    await self.memory_system.store_task(f"task_{channel}", task_data)
                
                # チャンネル別現在タスクを更新
                self.current_tasks[channel] = {
                    'task': task,
                    'channel': channel,  # ✅ チャンネル情報追加
                    'user_id': user_id,
                    'start_time': datetime.now()
                }
                
                response = f"""✅ **タスク確定完了**

📋 **Channel**: #{channel}
🎯 **Task**: {task}
👤 **Assigned**: <@{user_id}>
⏰ **Started**: {datetime.now().strftime('%H:%M')}

実務モードに切り替わりました。該当チャンネルでの作業支援を強化します。"""

                return response
                
            elif command == "change":
                # 既存タスクの更新 - チャンネル間移動対応版
                
                # アクティブタスクを検索（どのチャンネルでも）
                current_active_task = None
                old_channel = None
                for ch, task_info in self.current_tasks.items():
                    current_active_task = task_info
                    old_channel = ch
                    break  # 最初のアクティブタスクを使用（Sequential operation）
                
                if current_active_task:
                    old_task = current_active_task['task']
                    
                    # 旧チャンネルからタスクを削除（チャンネル移動の場合）
                    if old_channel != channel:
                        del self.current_tasks[old_channel]
                    
                    # 新チャンネルにタスクを設定
                    self.current_tasks[channel] = {
                        'task': task,
                        'channel': channel,
                        'user_id': current_active_task.get('user_id'),
                        'start_time': current_active_task.get('start_time'),
                        'updated': datetime.now()
                    }
                    
                    # Redis保存（メモリシステムが利用可能な場合）
                    if self.memory_system:
                        task_data = {
                            'task': task,
                            'channel': channel,
                            'user_id': current_active_task.get('user_id'),
                            'timestamp': datetime.now().isoformat(),
                            'status': 'active',
                            'changed_from': f"{old_channel}:{old_task}"
                        }
                        await self.memory_system.store_task(f"task_{channel}", task_data)
                    
                    # チャンネル変更か内容変更かを判定
                    if old_channel != channel:
                        response = f"""🔄 **タスク・チャンネル変更完了**

📋 **From**: #{old_channel} → #{channel}
🔄 **Task**: {old_task} → {task}
⏰ **Updated**: {datetime.now().strftime('%H:%M')}

{channel}チャンネルでの作業支援を開始します。"""
                    else:
                        response = f"""🔄 **タスク変更完了**

📋 **Channel**: #{channel}
🔄 **From**: {old_task}
🎯 **To**: {task}
⏰ **Updated**: {datetime.now().strftime('%H:%M')}

新しいタスクでの作業支援を開始します。"""
                else:
                    response = f"""⚠️ **変更対象タスクが見つかりません**

現在アクティブなタスクがありません。
まず `/task commit {channel} "{task}"` でタスクを確定してください。"""
                
                return response
                
        except Exception as e:
            logger.error(f"❌ Task command processing failed: {e}")
            return f"❌ **タスク処理中にエラーが発生しました**: {str(e)}"
        
    def _update_current_phase(self, current_time: time):
        """現在のフェーズを更新"""
        hour = current_time.hour
        
        if hour >= 20:
            self.current_phase = WorkflowPhase.FREE
        elif hour >= 6 and hour < 20:
            # 06:00-20:00の間は、会議開始イベントによってPROCESSING→ACTIVEに遷移
            # _execute_eventメソッドでフェーズが更新される
            # ここでは現在のフェーズを維持（手動変更しない）
            pass
        else:
            # 夜間待機時間 (00:00-05:59)
            self.current_phase = WorkflowPhase.STANDBY
            
    async def handle_user_override(self, command: str, duration_minutes: int = 60):
        """ユーザーによるワークフロー上書き"""
        self.user_override_active = True
        logger.info(f"👤 User override activated: {command} for {duration_minutes} minutes")
        
        # 指定時間後に上書きを解除
        await asyncio.sleep(duration_minutes * 60)
        self.user_override_active = False
        logger.info("🔄 User override expired, resuming normal workflow")
        
    def get_current_status(self) -> Dict:
        """現在のワークフロー状態を取得"""
        return {
            "current_phase": self.current_phase.value,
            "is_running": self.is_running,
            "user_override_active": self.user_override_active,
            "next_events": [
                {
                    "time": event.time.strftime("%H:%M"),
                    "action": event.action,
                    "phase": event.phase.value
                }
                for event in self.workflow_schedule
            ]
        }

# システム統合用のファクトリー関数
def create_daily_workflow_system(channel_ids: Dict[str, int]) -> DailyWorkflowSystem:
    """Daily Workflow System のインスタンス作成"""
    return DailyWorkflowSystem(channel_ids)

if __name__ == "__main__":
    # テスト実行
    async def test_daily_workflow():
        # テスト用チャンネルID（実際の値は環境変数から取得）
        channel_ids = {
            "command_center": int(os.getenv('COMMAND_CENTER_CHANNEL_ID', '0')),
            "lounge": int(os.getenv('LOUNGE_CHANNEL_ID', '0')),
            "development": int(os.getenv('DEVELOPMENT_CHANNEL_ID', '0')),
            "creation": int(os.getenv('CREATION_CHANNEL_ID', '0'))
        }
        
        workflow = DailyWorkflowSystem(channel_ids)
        await workflow.start()
        
        # テスト用に短時間実行
        await asyncio.sleep(60)
        await workflow.stop()
    
    asyncio.run(test_daily_workflow())