#!/usr/bin/env python3
"""
Daily Workflow System - 時間ベースの自動ワークフロー管理

AC-015: Daily Workflow Automation の実装
- 06:55: Daily report generation
- 07:00: Morning meeting initiation
- 20:00: Work session conclusion  
- 00:00: System rest period
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, Optional, Callable
import json
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class WorkflowPhase(Enum):
    """ワークフロー段階定義"""
    REST = "rest"           # 00:00-06:54 システム休息
    PREPARATION = "prep"    # 06:55-06:59 準備・レポート生成
    MEETING = "meeting"     # 07:00-19:59 会議・作業フェーズ
    CONCLUSION = "conclusion"  # 20:00-23:59 作業終了フェーズ

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
    
    def __init__(self, channel_ids: Dict[str, int]):
        self.channel_ids = channel_ids
        self.current_phase = WorkflowPhase.REST
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.user_override_active = False
        
        # ワークフロー スケジュール定義
        self.workflow_schedule = [
            WorkflowEvent(
                time=time(6, 55),
                phase=WorkflowPhase.PREPARATION,
                action="daily_report_generation",
                message="📊 **Daily Report Generation Started**\n\n🌅 おはようございます！昨日の活動レポートを生成中...",
                channel="command_center",
                agent="spectra"
            ),
            WorkflowEvent(
                time=time(7, 0),
                phase=WorkflowPhase.MEETING,
                action="morning_meeting_initiation",
                message="🏢 **Morning Meeting - Session Started**\n\n" +
                       "📋 **Today's Agenda:**\n" +
                       "• 昨日の進捗レビュー\n" +
                       "• 今日の目標設定\n" +
                       "• リソース配分の確認\n" +
                       "• 課題・ブロッカーの特定\n\n" +
                       "それでは、本日もよろしくお願いします！ 💪",
                channel="command_center",
                agent="spectra"
            ),
            WorkflowEvent(
                time=time(20, 0),
                phase=WorkflowPhase.CONCLUSION,
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
                phase=WorkflowPhase.REST,
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
        # Message Queue に追加して適切なボットが送信
        queue_item = {
            'id': f"workflow_{event.action}_{datetime.now().isoformat()}",
            'content': event.message,
            'author': 'SYSTEM',
            'author_id': '000000000000000000',
            'channel_id': str(self.channel_ids.get(event.channel, 0)),
            'channel_name': event.channel,
            'target_agent': event.agent,
            'timestamp': datetime.now().isoformat(),
            'processed': False,
            'priority': 1,  # Workflow events are high priority
            'event_type': 'workflow',
            'workflow_action': event.action
        }
        
        # キューファイルに追加
        try:
            with open("message_queue.json", "r", encoding='utf-8') as f:
                queue_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            queue_data = []
            
        queue_data.append(queue_item)
        
        with open("message_queue.json", "w", encoding='utf-8') as f:
            json.dump(queue_data, indent=2, ensure_ascii=False)
            
        logger.info(f"📝 Workflow message queued: {event.agent} -> #{event.channel}")
        
    def _update_current_phase(self, current_time: time):
        """現在のフェーズを更新"""
        hour = current_time.hour
        minute = current_time.minute
        
        if hour == 0 and minute == 0:
            self.current_phase = WorkflowPhase.REST
        elif hour == 6 and minute >= 55:
            self.current_phase = WorkflowPhase.PREPARATION
        elif hour >= 7 and hour < 20:
            self.current_phase = WorkflowPhase.MEETING
        elif hour >= 20:
            self.current_phase = WorkflowPhase.CONCLUSION
        else:
            # 夜間休息時間
            self.current_phase = WorkflowPhase.REST
            
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
        channel_ids = {
            "command_center": 1383963657137946664,
            "lounge": 1383966355962990653,
            "development": 1383968516033478727,
            "creation": 1383981653046726728
        }
        
        workflow = DailyWorkflowSystem(channel_ids)
        await workflow.start()
        
        # テスト用に短時間実行
        await asyncio.sleep(60)
        await workflow.stop()
    
    asyncio.run(test_daily_workflow())