#!/usr/bin/env python3
"""
Discord Live Test Script
本番環境でのDiscord動作確認用スクリプト

テスト設定:
- 自発発言: 10秒間隔、100%確率
- 日報生成: 現時刻+2分後 (13:52)
- 本物のAPI・トークン使用
"""

import os
import asyncio
import logging
from datetime import datetime, time, timedelta
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをPythonパスに追加
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 環境変数読み込み
load_dotenv()

# テスト用環境変数設定
os.environ['ENVIRONMENT'] = 'test'  # テスト環境（10秒間隔、100%確率）
os.environ['LOG_LEVEL'] = 'INFO'

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Discord Live Test実行"""
    logger.info("🚀 Discord Live Test開始")
    logger.info(f"⏰ 現在時刻: {datetime.now().strftime('%H:%M:%S')}")
    logger.info("📋 テスト設定:")
    logger.info("  - 環境: test (自発発言10秒間隔、100%確率)")
    logger.info("  - 日報生成: 13:52 (現時刻+2分)")
    logger.info("  - API: 本物のGemini API使用")
    logger.info("  - Discord: 本物のトークン使用")
    
    try:
        # システムコンポーネントのインポート
        from src.container.system_container import create_system_container
        from src.application.discord_app_service import DiscordAppService
        
        # 日報生成時刻を現時刻+2分に設定
        target_time = datetime.now() + timedelta(minutes=2)
        logger.info(f"🎯 日報生成予定時刻: {target_time.strftime('%H:%M:%S')}")
        
        # システムコンテナ初期化
        logger.info("🔧 System Container初期化中...")
        container = create_system_container()
        await container.initialize()
        logger.info("✅ System Container初期化完了")
        
        # 日報時刻の動的変更
        daily_workflow = container.get('daily_workflow')
        
        # 既存の06:00イベントを現時刻+2分に変更
        for event in daily_workflow.workflow_schedule:
            if event.action == "long_term_memory_processing":
                # 時刻を現時刻+2分に変更
                event.time = time(target_time.hour, target_time.minute)
                logger.info(f"📅 日報イベント時刻変更: {event.time}")
                break
        
        # Discord Application Service作成
        discord_service = DiscordAppService(container)
        
        logger.info("🔌 Discord接続開始...")
        logger.info("📊 自発発言監視開始 (10秒間隔、100%確率)")
        
        # システム開始
        await discord_service.start()
        
        # テスト実行時間 (10分間)
        test_duration = 10 * 60  # 10分
        logger.info(f"⏱️ テスト実行時間: {test_duration//60}分")
        
        # テスト実行
        await asyncio.sleep(test_duration)
        
    except KeyboardInterrupt:
        logger.info("⏹️ ユーザーによる中断")
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {e}")
        raise
    finally:
        logger.info("🏁 Discord Live Test終了")

if __name__ == "__main__":
    asyncio.run(main())