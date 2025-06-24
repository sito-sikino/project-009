#!/usr/bin/env python3
"""
Discord Test Verification - Quick Status Check
"""

import asyncio
from datetime import datetime, timedelta

# Force test environment
import os
os.environ['ENVIRONMENT'] = 'test'

from src.config.settings import get_settings
from src.utils.logger import setup_logging, get_logger

async def main():
    setup_logging()
    logger = get_logger(__name__)
    settings = get_settings()
    
    logger.info("🔍 Discord Test Verification")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Autonomous Speech Interval: {settings.autonomous_speech_test_interval}秒")
    logger.info(f"Speech Probability: {100 if settings.environment == 'test' else 33}%")
    
    # Calculate next test time
    next_test = datetime.now() + timedelta(minutes=2)
    logger.info(f"⏰ Next test可以: {next_test.strftime('%H:%M:%S')}")
    
    # Health check
    try:
        import requests
        health = requests.get("http://localhost:8000/health", timeout=5)
        logger.info(f"🏥 Health Status: {health.json()}")
    except:
        logger.info("🏥 Health endpoint not accessible (system may be stopped)")

if __name__ == "__main__":
    asyncio.run(main())