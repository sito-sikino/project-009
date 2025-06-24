#!/usr/bin/env python3
"""
Quick Autonomous Speech Test
現時刻+1分の自発発言テスト（フェーズ同期修正版）
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
    """Quick Autonomous Speech Test"""
    logger = None
    
    try:
        # Setup
        check_required_env_vars()
        setup_logging()
        logger = get_logger(__name__)
        logger.info("🚀 Quick Autonomous Speech Test - フェーズ同期修正版")
        
        # Calculate test timing (current + 1 minute)
        test_time = datetime.now() + timedelta(minutes=1)
        logger.info(f"⏰ 日報テスト時刻: {test_time.strftime('%H:%M:%S')}")
        
        # Initialize system
        logger.info("🔧 System initialization...")
        container = create_system_container()
        await container.initialize()
        
        # Override workflow timing
        daily_workflow = container.get('daily_workflow')
        daily_workflow.workflow_schedule[0].time = test_time.time()
        logger.info(f"📅 ワークフロー時刻設定: {test_time.strftime('%H:%M:%S')}")
        
        # Create and start application
        app_service = create_discord_app_service(container)
        logger.info("🔌 Discord接続開始...")
        
        # Start with timeout for focused testing
        start_task = asyncio.create_task(app_service.start_application())
        
        # Wait for test completion (3 minutes total)
        await asyncio.sleep(180)  # 3 minutes
        
        logger.info("⏰ Test timeout reached, stopping...")
        start_task.cancel()
        
        # Cleanup
        if app_service.running:
            await app_service.stop_application()
            
    except Exception as e:
        if logger:
            logger.error(f"❌ Test error: {e}")
        else:
            print(f"❌ Test error: {e}")
    finally:
        if logger:
            logger.info("🏁 Quick Autonomous Speech Test完了")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")