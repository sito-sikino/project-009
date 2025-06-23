"""
Event-driven Daily Report System
イベントドリブン日報生成システム（API不要・テンプレート式）
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import discord

from ..infrastructure.long_term_memory import ProcessedMemory, ProgressDifferential


@dataclass
class DepartmentReport:
    """部門別レポート"""
    name: str
    emoji: str
    themes: List[str]
    details: List[str]
    progress_score: float


@dataclass
class DailyReport:
    """日報データ"""
    date: datetime
    departments: List[DepartmentReport]
    overall_summary: str
    processing_stats: Dict[str, Any]


class DailyReportGenerator:
    """日報生成システム（API不要・エンティティベース抽出）"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 部門定義
        self.departments = {
            "command_center": {
                "name": "Command Center",
                "emoji": "🧭",
                "keywords": ["戦略", "方針", "決定", "課題", "目標", "リソース", "優先度"]
            },
            "creation": {
                "name": "Creation",
                "emoji": "🗃️",
                "keywords": ["制作", "創作", "デザイン", "アイデア", "コンテンツ", "アート"]
            },
            "development": {
                "name": "Development", 
                "emoji": "🗃️",
                "keywords": ["開発", "実装", "技術", "コード", "テスト", "デプロイ", "バグ"]
            }
        }
    
    def generate_daily_report(self, 
                            memories: List[ProcessedMemory], 
                            progress_diff: ProgressDifferential,
                            processing_stats: Dict[str, Any]) -> DailyReport:
        """
        日報生成（API不要・テンプレート式）
        
        Args:
            memories: 処理済み記憶一覧
            progress_diff: 進捗差分
            processing_stats: 処理統計
            
        Returns:
            生成された日報
        """
        self.logger.info("📊 日報生成開始（API不要処理）")
        
        try:
            # 部門別分析
            department_reports = []
            for dept_key, dept_config in self.departments.items():
                report = self._analyze_department(memories, dept_key, dept_config)
                department_reports.append(report)
            
            # 全体サマリー生成
            overall_summary = self._generate_overall_summary(
                department_reports, progress_diff, processing_stats
            )
            
            daily_report = DailyReport(
                date=datetime.now(),
                departments=department_reports,
                overall_summary=overall_summary,
                processing_stats=processing_stats
            )
            
            self.logger.info("✅ 日報生成完了")
            return daily_report
            
        except Exception as e:
            self.logger.error(f"❌ 日報生成エラー: {e}")
            raise
    
    def _analyze_department(self, 
                          memories: List[ProcessedMemory], 
                          dept_key: str, 
                          dept_config: Dict[str, Any]) -> DepartmentReport:
        """部門別分析"""
        
        # 該当記憶フィルタリング
        dept_memories = []
        for memory in memories:
            # チャンネルIDベースフィルタリング（簡略版）
            if self._is_department_relevant(memory, dept_key, dept_config):
                dept_memories.append(memory)
        
        # テーマ抽出
        themes = self._extract_themes(dept_memories, dept_config["keywords"])
        
        # 詳細抽出
        details = self._extract_details(dept_memories)
        
        # 進捗スコア計算
        progress_score = self._calculate_progress_score(dept_memories)
        
        return DepartmentReport(
            name=dept_config["name"],
            emoji=dept_config["emoji"],
            themes=themes,
            details=details,
            progress_score=progress_score
        )
    
    def _is_department_relevant(self, 
                              memory: ProcessedMemory, 
                              dept_key: str, 
                              dept_config: Dict[str, Any]) -> bool:
        """記憶が部門に関連するかチェック"""
        
        # エンティティチェック
        for entity in memory.entities:
            entity_type = entity.get("type", "").lower()
            entity_name = entity.get("name", "").lower()
            
            # 部門キーワードマッチング
            for keyword in dept_config["keywords"]:
                if keyword in entity_name or keyword in memory.structured_content.lower():
                    return True
        
        # メモリタイプチェック
        if dept_key == "development" and memory.memory_type in ["task", "learning"]:
            return True
        elif dept_key == "creation" and memory.memory_type in ["conversation", "progress"]:
            return True
        elif dept_key == "command_center" and memory.memory_type == "decision":
            return True
        
        return False
    
    def _extract_themes(self, memories: List[ProcessedMemory], keywords: List[str]) -> List[str]:
        """テーマ抽出"""
        themes = set()
        
        for memory in memories:
            # エンティティからテーマ抽出
            for entity in memory.entities:
                if entity.get("type") in ["technology", "project", "skill"]:
                    themes.add(entity.get("name", ""))
            
            # 進捗指標からテーマ抽出
            for key, value in memory.progress_indicators.items():
                if value and isinstance(value, str):
                    themes.add(value)
        
        # 重要度でソート
        sorted_themes = sorted(list(themes), key=lambda x: len(x))[:5]
        return [theme for theme in sorted_themes if theme]
    
    def _extract_details(self, memories: List[ProcessedMemory]) -> List[str]:
        """詳細抽出"""
        details = []
        
        # 高重要度記憶から詳細抽出
        high_importance_memories = [
            m for m in memories if m.importance_score >= 0.7
        ]
        
        for memory in high_importance_memories[:3]:  # 最大3件
            detail = memory.structured_content[:100] + "..." if len(memory.structured_content) > 100 else memory.structured_content
            details.append(detail)
        
        return details
    
    def _calculate_progress_score(self, memories: List[ProcessedMemory]) -> float:
        """進捗スコア計算"""
        if not memories:
            return 0.0
        
        # 重要度スコアの平均
        avg_importance = sum(m.importance_score for m in memories) / len(memories)
        
        # アクティビティレベル（記憶数）
        activity_score = min(len(memories) / 10.0, 1.0)  # 10件で満点
        
        # 組み合わせスコア
        return (avg_importance * 0.7 + activity_score * 0.3)
    
    def _generate_overall_summary(self, 
                                department_reports: List[DepartmentReport],
                                progress_diff: ProgressDifferential,
                                processing_stats: Dict[str, Any]) -> str:
        """全体サマリー生成"""
        
        active_departments = [d for d in department_reports if d.themes]
        total_themes = sum(len(d.themes) for d in active_departments)
        avg_progress = sum(d.progress_score for d in active_departments) / len(active_departments) if active_departments else 0.0
        
        summary = f"今日は{len(active_departments)}部門で{total_themes}のテーマが進行中。"
        
        if avg_progress >= 0.7:
            summary += " 全体的に高い進捗を記録。"
        elif avg_progress >= 0.4:
            summary += " 順調な進展が見られます。"
        else:
            summary += " 活動レベルは控えめです。"
        
        return summary


class IntegratedMessageSystem:
    """統合メッセージシステム（日報+会議開始宣言）"""
    
    def __init__(self, output_bots: Dict[str, Any]):
        self.output_bots = output_bots
        self.logger = logging.getLogger(__name__)
    
    async def send_integrated_morning_message(self, 
                                            daily_report: DailyReport,
                                            channel_id: int) -> bool:
        """
        統合朝次メッセージ送信（日報Embed + 会議開始宣言）
        
        Args:
            daily_report: 生成された日報
            channel_id: 送信先チャンネルID
            
        Returns:
            送信成功/失敗
        """
        try:
            self.logger.info("📤 統合朝次メッセージ送信開始")
            
            # 会議開始宣言（通常テキスト）
            meeting_announcement = self._create_meeting_announcement()
            
            # 日報Embed作成
            report_embed = self._create_daily_report_embed(daily_report)
            
            # Spectra Bot経由で送信
            spectra_bot = self.output_bots.get("spectra")
            if not spectra_bot:
                raise RuntimeError("Spectra Bot not available")
            
            channel = spectra_bot.get_channel(channel_id)
            if not channel:
                raise RuntimeError(f"Channel {channel_id} not found")
            
            # 統合メッセージ送信
            await channel.send(content=meeting_announcement, embed=report_embed)
            
            self.logger.info("✅ 統合朝次メッセージ送信完了")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 統合メッセージ送信エラー: {e}")
            return False
    
    def _create_meeting_announcement(self) -> str:
        """会議開始宣言作成"""
        return (
            "🏢 **Morning Meeting - Session Started**\n\n"
            "📋 **Today's Agenda:**\n"
            "• 昨日の進捗レビュー\n"
            "• 今日の目標設定\n"
            "• リソース配分の確認\n"
            "• 課題・ブロッカーの特定\n\n"
            "それでは、本日もよろしくお願いします！ 💪"
        )
    
    def _create_daily_report_embed(self, daily_report: DailyReport) -> discord.Embed:
        """日報Embed作成"""
        embed = discord.Embed(
            title=f"📅 Daily Report - {daily_report.date.strftime('%Y-%m-%d')}",
            description=daily_report.overall_summary,
            color=0x00FF7F,  # 緑色
            timestamp=daily_report.date
        )
        
        # 部門別フィールド追加
        for dept in daily_report.departments:
            if dept.themes:
                # テーマ表示
                themes_text = "、".join(dept.themes[:3])  # 最大3テーマ
                
                # 詳細表示（1つのみ）
                detail_text = dept.details[0] if dept.details else "進行中..."
                
                field_value = f"**[テーマ]**: {themes_text}\n**[詳細]**: {detail_text}"
                
                embed.add_field(
                    name=f"{dept.emoji} {dept.name}",
                    value=field_value,
                    inline=False
                )
        
        # 処理統計フッター
        stats = daily_report.processing_stats
        embed.set_footer(
            text=f"処理時間: {stats.get('processing_time', 0):.1f}秒 | "
                 f"記憶数: {stats.get('memory_count', 0)}件 | "
                 f"API使用: {stats.get('api_usage', 0)}回"
        )
        
        return embed


# イベントドリブン統合システム

class EventDrivenWorkflowOrchestrator:
    """イベントドリブンワークフロー統括システム"""
    
    def __init__(self, 
                 long_term_memory_processor,
                 daily_report_generator: DailyReportGenerator,
                 integrated_message_system: IntegratedMessageSystem,
                 command_center_channel_id: int):
        
        self.long_term_memory_processor = long_term_memory_processor
        self.daily_report_generator = daily_report_generator
        self.integrated_message_system = integrated_message_system
        self.command_center_channel_id = command_center_channel_id
        
        self.logger = logging.getLogger(__name__)
    
    async def execute_morning_workflow(self) -> bool:
        """
        統合朝次ワークフロー実行（06:00トリガー）
        
        Returns:
            ワークフロー成功/失敗
        """
        workflow_start = datetime.now()
        
        try:
            self.logger.info("🚀 統合朝次ワークフロー開始")
            
            # 1. 長期記憶化処理（3-API）
            memories, progress_diff = await self.long_term_memory_processor.daily_memory_consolidation()
            
            # 2. 処理統計収集
            processing_time = (datetime.now() - workflow_start).total_seconds()
            processing_stats = {
                "processing_time": processing_time,
                "memory_count": len(memories),
                "api_usage": 3,
                "deduplication_rate": getattr(self.long_term_memory_processor.deduplicator, 'last_dedup_rate', 0)
            }
            
            # 3. 日報生成（API不要）
            daily_report = self.daily_report_generator.generate_daily_report(
                memories, progress_diff, processing_stats
            )
            
            # 4. 統合メッセージ送信
            success = await self.integrated_message_system.send_integrated_morning_message(
                daily_report, self.command_center_channel_id
            )
            
            if success:
                total_time = (datetime.now() - workflow_start).total_seconds()
                self.logger.info(f"🎉 統合朝次ワークフロー完了: {total_time:.1f}秒")
                return True
            else:
                raise RuntimeError("統合メッセージ送信失敗")
                
        except Exception as e:
            self.logger.error(f"❌ 統合朝次ワークフローエラー: {e}")
            return False