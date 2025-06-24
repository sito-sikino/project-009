#!/usr/bin/env python3
"""
Discord Multi-Agent System - Clean Architecture Entry Point
統合受信・個別送信型アーキテクチャ v0.2.2
"""

import asyncio
import sys
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)
print(f"✅ Environment loaded from .env: {os.getenv('ENVIRONMENT', 'not_set')}")

# Clean Architecture imports
from src.config.settings import check_required_env_vars
from src.utils.logger import setup_logging, get_logger, log_system_startup
from src.container.system_container import create_system_container
from src.application.discord_app_service import create_discord_app_service
from src.infrastructure.system_lifecycle import create_system_lifecycle


async def main():
    """Clean Architecture main entry point"""
    logger = None
    
    # Phase 1: Environment & Logging Setup
    check_required_env_vars()
    setup_logging()
    logger = get_logger(__name__)
    log_system_startup()
    logger.info("🚀 Starting Discord Multi-Agent System v0.2.2")
    logger.info("🏗️ Architecture: Clean Architecture + 統合受信・個別送信型")
    
    # Phase 2: Dependency Injection Container
    logger.info("🔧 Initializing System Container...")
    container = create_system_container()
    await container.initialize()
    logger.info("✅ System Container initialized with dependency injection")
    
    # Phase 3: Application Service
    logger.info("🎯 Creating Application Service...")
    app_service = create_discord_app_service(container)
    logger.info("✅ Discord Application Service created")
    
    # Phase 4: System Lifecycle Management
    logger.info("🔄 Setting up System Lifecycle Manager...")
    lifecycle = create_system_lifecycle(app_service, logger)
    lifecycle.setup_signal_handlers()
    logger.info("✅ System Lifecycle Manager ready")
    
    # Phase 5: Run Application
    logger.info("▶️ Starting main application loop...")
    await lifecycle.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Discord Multi-Agent System stopped")
        sys.exit(0)