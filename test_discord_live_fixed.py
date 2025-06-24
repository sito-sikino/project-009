#!/usr/bin/env python3
"""
Discord Live Test - Fixed Version
現時刻+2分の日報生成テスト（リアルDiscordトークン/API使用）
"""

import asyncio
import os
import sys
from datetime import datetime, time, timedelta

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Force test environment
os.environ['ENVIRONMENT'] = 'test'

# Clean Architecture imports
from src.config.settings import check_required_env_vars
from src.utils.logger import setup_logging, get_logger
from src.container.system_container import create_system_container
from src.application.discord_app_service import create_discord_app_service
from src.infrastructure.system_lifecycle import create_system_lifecycle

async def main():
    """Fixed Discord Live Test"""
    logger = None
    
    try:
        # Phase 1: Environment & Logging Setup
        check_required_env_vars()
        setup_logging()
        logger = get_logger(__name__)
        logger.info("🚀 Discord Live Test開始 - Fixed Version")
        
        # Phase 2: Calculate test trigger time (current + 2 minutes)
        current_time = datetime.now()
        test_trigger_time = current_time + timedelta(minutes=2)
        logger.info(f"⏰ 日報テスト時刻: {test_trigger_time.strftime('%H:%M:%S')}")
        
        # Phase 3: System Container with timing override
        logger.info("🔧 System Container初期化...")
        container = create_system_container()
        await container.initialize()
        
        # Phase 4: Override daily workflow timing for test
        daily_workflow = container.get('daily_workflow')
        # Update the first workflow event to trigger at test time
        daily_workflow.workflow_schedule[0].time = test_trigger_time.time()
        logger.info(f"📅 日報イベント時刻変更: {test_trigger_time.strftime('%H:%M:%S')}")
        
        # Phase 5: Application Service
        logger.info("🎯 Application Service作成...")
        app_service = create_discord_app_service(container)
        
        # Phase 6: System Lifecycle Management
        logger.info("🔄 System Lifecycle準備...")
        lifecycle = create_system_lifecycle(app_service, logger)
        lifecycle.setup_signal_handlers()
        
        # Phase 7: Start Application (correct method name)
        logger.info("🔌 Discord接続開始...")
        logger.info("📊 自発発言監視開始 (10秒間隔、100%確率)")
        
        # Start the application using correct method
        await app_service.start_application()
        
    except Exception as e:
        if logger:
            logger.error(f"❌ テスト実行エラー: {e}")
        else:
            print(f"❌ テスト実行エラー: {e}")
        sys.exit(1)
    finally:
        if logger:
            logger.info("🏁 Discord Live Test終了")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Discord Live Test stopped")
        sys.exit(0)