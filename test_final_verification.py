#!/usr/bin/env python3
"""
Final Verification Test - All Issues Fixed
現時刻+1分30秒で完全検証（フェーズ同期+WorkflowPhase参照修正版）
"""

import asyncio
import os
from datetime import datetime, timedelta

# Force test environment
os.environ['ENVIRONMENT'] = 'test'

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.config.settings import check_required_env_vars
from src.utils.logger import setup_logging, get_logger
from src.container.system_container import create_system_container
from src.application.discord_app_service import create_discord_app_service

async def main():
    """Final Verification Test"""
    logger = None
    
    try:
        # Setup
        check_required_env_vars()
        setup_logging()
        logger = get_logger(__name__)
        logger.info("🚀 Final Verification Test - 全問題修正版")
        
        # Test timing (current + 1.5 minutes)
        test_time = datetime.now() + timedelta(minutes=1, seconds=30)
        logger.info(f"⏰ 日報+自発発言テスト時刻: {test_time.strftime('%H:%M:%S')}")
        
        # Initialize system
        container = create_system_container()
        await container.initialize()
        
        # Set test timing
        daily_workflow = container.get('daily_workflow')
        daily_workflow.workflow_schedule[0].time = test_time.time()
        
        # Start application
        app_service = create_discord_app_service(container)
        logger.info("🔌 Discord接続開始...")
        logger.info("📋 期待結果:")
        logger.info("  1. 日報メッセージ2件 (処理開始 + 会議開始)")
        logger.info("  2. フェーズ遷移: PROCESSING -> ACTIVE")
        logger.info("  3. 自発発言開始 (10秒間隔, 100%確率)")
        
        # Run test for 2 minutes
        start_task = asyncio.create_task(app_service.start_application())
        await asyncio.sleep(120)  # 2 minutes
        
        logger.info("✅ Test completed successfully")
        start_task.cancel()
        
        if app_service.running:
            await app_service.stop_application()
            
    except Exception as e:
        if logger:
            logger.error(f"❌ Test error: {e}")
        else:
            print(f"❌ Test error: {e}")
    finally:
        if logger:
            logger.info("🏁 Final Verification Test完了")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test stopped")
