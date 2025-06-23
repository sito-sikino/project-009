#!/usr/bin/env python3
"""
v0.3.0 End-to-End Integration Verification
v0.3.0統合動作検証スクリプト
"""

import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 環境変数設定（テスト用）
os.environ.setdefault('ENVIRONMENT', 'test')
os.environ.setdefault('LOG_LEVEL', 'INFO')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class V030IntegrationVerifier:
    """v0.3.0統合検証システム"""
    
    def __init__(self):
        self.verification_results: Dict[str, bool] = {}
        self.error_details: Dict[str, str] = {}
    
    async def verify_all(self) -> bool:
        """全体検証実行"""
        logger.info("🚀 v0.3.0統合検証開始")
        
        verification_tasks = [
            ("環境変数", self.verify_environment_variables),
            ("依存関係", self.verify_dependencies),
            ("SystemContainer", self.verify_system_container),
            ("長期記憶システム", self.verify_long_term_memory_system),
            ("日報システム", self.verify_daily_report_system),
            ("統合ワークフロー", self.verify_integrated_workflow),
            ("PostgreSQLスキーマ", self.verify_postgresql_schema),
        ]
        
        for task_name, task_func in verification_tasks:
            try:
                logger.info(f"🔍 {task_name}検証開始")
                result = await task_func()
                self.verification_results[task_name] = result
                
                if result:
                    logger.info(f"✅ {task_name}検証成功")
                else:
                    logger.error(f"❌ {task_name}検証失敗")
                    
            except Exception as e:
                logger.error(f"❌ {task_name}検証エラー: {e}")
                self.verification_results[task_name] = False
                self.error_details[task_name] = str(e)
        
        return self.generate_final_report()
    
    async def verify_environment_variables(self) -> bool:
        """環境変数検証"""
        required_vars = [
            'DISCORD_RECEPTION_TOKEN',
            'DISCORD_SPECTRA_TOKEN', 
            'DISCORD_LYNQ_TOKEN',
            'DISCORD_PAZ_TOKEN',
            'GEMINI_API_KEY',
            'REDIS_URL',
            'POSTGRESQL_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ 必須環境変数が未設定: {missing_vars}")
            logger.info("💡 解決方法:")
            logger.info("1. 'python scripts/setup_environment.py --env-type test' を実行")
            logger.info("2. '.env.test.template' を参考に '.env' ファイルを作成")
            logger.info("3. 適切なテスト用値を設定")
            
            # テスト環境テンプレートファイルの確認
            env_template = Path(__file__).parent.parent / ".env.test.template"
            if env_template.exists():
                logger.info(f"📋 テンプレートファイル利用可能: {env_template}")
            else:
                logger.warning("⚠️ テンプレートファイルがありません。setup_environment.py を実行してください")
            
            return False
        
        return True
    
    async def verify_dependencies(self) -> bool:
        """依存関係検証"""
        try:
            # 重要な依存関係のインポートテスト
            import datasketch
            import redis
            import asyncpg
            import discord
            import langchain_google_genai
            
            logger.info(f"✅ datasketch: {datasketch.__version__}")
            logger.info(f"✅ redis: {redis.__version__}")
            logger.info(f"✅ discord.py: {discord.__version__}")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ 依存関係エラー: {e}")
            return False
    
    async def verify_system_container(self) -> bool:
        """SystemContainer検証"""
        try:
            from src.container.system_container import create_system_container
            
            container = create_system_container()
            
            # v0.3.0新コンポーネントの存在確認
            v030_components = [
                'long_term_memory_processor',
                'daily_report_generator', 
                'integrated_message_system',
                'event_driven_workflow_orchestrator'
            ]
            
            for component in v030_components:
                if component not in container._components:
                    logger.error(f"❌ 未登録コンポーネント: {component}")
                    return False
                logger.info(f"✅ コンポーネント登録確認: {component}")
            
            # 依存関係確認
            daily_workflow_deps = container._components['daily_workflow'].dependencies
            if 'long_term_memory_processor' not in daily_workflow_deps:
                logger.error("❌ daily_workflowにlong_term_memory_processor依存関係がありません")
                return False
            
            logger.info("✅ SystemContainer依存関係確認完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ SystemContainer検証エラー: {e}")
            traceback.print_exc()
            return False
    
    async def verify_long_term_memory_system(self) -> bool:
        """長期記憶システム検証"""
        try:
            from src.infrastructure.long_term_memory import LongTermMemoryProcessor
            from src.infrastructure.deduplication_system import MinHashDeduplicator
            
            # 長期記憶処理システム初期化テスト
            processor = LongTermMemoryProcessor(
                redis_url=os.getenv('REDIS_URL'),
                postgres_url=os.getenv('POSTGRESQL_URL'),
                gemini_api_key=os.getenv('GEMINI_API_KEY')
            )
            
            # 重複検出システム初期化テスト
            deduplicator = MinHashDeduplicator(threshold=0.8)
            
            # API制限チェック機能テスト
            assert processor._check_api_quota(datetime.now()) == True
            
            # 統計取得テスト
            stats = deduplicator.get_statistics()
            assert isinstance(stats, dict)
            
            logger.info("✅ 長期記憶システム基本機能確認完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ 長期記憶システム検証エラー: {e}")
            traceback.print_exc()
            return False
    
    async def verify_daily_report_system(self) -> bool:
        """日報システム検証"""
        try:
            from src.core.daily_report_system import (
                DailyReportGenerator,
                IntegratedMessageSystem,
                EventDrivenWorkflowOrchestrator
            )
            from unittest.mock import MagicMock
            
            # 日報生成システム初期化テスト
            report_generator = DailyReportGenerator()
            
            # 統合メッセージシステム初期化テスト
            mock_bots = {"spectra": MagicMock(), "lynq": MagicMock(), "paz": MagicMock()}
            message_system = IntegratedMessageSystem(mock_bots)
            
            # イベントドリブンワークフロー統括システム初期化テスト
            orchestrator = EventDrivenWorkflowOrchestrator(
                long_term_memory_processor=MagicMock(),
                daily_report_generator=report_generator,
                integrated_message_system=message_system,
                command_center_channel_id=123456789
            )
            
            # 部門設定確認
            assert len(report_generator.departments) == 3
            assert "command_center" in report_generator.departments
            assert "creation" in report_generator.departments
            assert "development" in report_generator.departments
            
            logger.info("✅ 日報システム基本機能確認完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ 日報システム検証エラー: {e}")
            traceback.print_exc()
            return False
    
    async def verify_integrated_workflow(self) -> bool:
        """統合ワークフロー検証"""
        try:
            from src.core.daily_workflow import DailyWorkflowSystem, WorkflowPhase
            from unittest.mock import MagicMock
            
            # v0.3.0対応DailyWorkflowSystem初期化テスト
            workflow = DailyWorkflowSystem(
                channel_ids={"command_center": 123, "development": 456, "creation": 789},
                memory_system=MagicMock(),
                priority_queue=MagicMock(),
                long_term_memory_processor=MagicMock()  # v0.3.0新引数
            )
            
            # 新フェーズ確認
            assert hasattr(WorkflowPhase, 'PROCESSING')
            assert WorkflowPhase.PROCESSING.value == "processing"
            
            # 06:00イベント確認
            morning_events = [
                event for event in workflow.workflow_schedule 
                if event.time.hour == 6 and event.time.minute == 0
            ]
            assert len(morning_events) == 1
            assert morning_events[0].action == "long_term_memory_processing"
            
            logger.info("✅ 統合ワークフロー基本機能確認完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ 統合ワークフロー検証エラー: {e}")
            traceback.print_exc()
            return False
    
    async def verify_postgresql_schema(self) -> bool:
        """PostgreSQLスキーマ検証"""
        try:
            migration_file = project_root / "migrations" / "001_create_unified_memories.sql"
            
            if not migration_file.exists():
                logger.error("❌ マイグレーションファイルが見つかりません")
                return False
            
            # SQLファイル内容確認
            sql_content = migration_file.read_text()
            
            # 重要な要素の存在確認
            required_elements = [
                "unified_memories",
                "vector(768)",
                "embedding",
                "search_unified_memories",
                "daily_entity_progress"
            ]
            
            for element in required_elements:
                if element not in sql_content:
                    logger.error(f"❌ SQLスキーマに必要な要素がありません: {element}")
                    return False
                logger.info(f"✅ SQL要素確認: {element}")
            
            logger.info("✅ PostgreSQLスキーマ設計確認完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ PostgreSQLスキーマ検証エラー: {e}")
            return False
    
    def generate_final_report(self) -> bool:
        """最終レポート生成"""
        logger.info("\n" + "="*60)
        logger.info("📊 v0.3.0統合検証レポート")
        logger.info("="*60)
        
        total_tests = len(self.verification_results)
        passed_tests = sum(self.verification_results.values())
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        for test_name, result in self.verification_results.items():
            status = "✅ 成功" if result else "❌ 失敗"
            logger.info(f"{status}: {test_name}")
            
            if not result and test_name in self.error_details:
                logger.info(f"    エラー詳細: {self.error_details[test_name]}")
        
        logger.info(f"\n📊 検証結果: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate == 100:
            logger.info("🎉 v0.3.0統合検証完全成功！")
            logger.info("🚀 システムは本番デプロイ準備完了です")
            return True
        elif success_rate >= 80:
            logger.info("⚠️ v0.3.0統合検証部分成功")
            logger.info("🔧 一部修正後にデプロイ可能です")
            return False
        else:
            logger.info("❌ v0.3.0統合検証失敗")
            logger.info("🛠️ 重要な問題があります。修正が必要です")
            return False


async def main():
    """メイン検証実行"""
    verifier = V030IntegrationVerifier()
    
    print("🔍 Discord Multi-Agent System v0.3.0")
    print("📋 統合動作検証スクリプト")
    print("="*50)
    
    success = await verifier.verify_all()
    
    if success:
        print("\n🎉 v0.3.0統合検証成功！")
        return 0
    else:
        print("\n❌ v0.3.0統合検証で問題検出")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ 検証中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 予期しないエラー: {e}")
        traceback.print_exc()
        sys.exit(1)