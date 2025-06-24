#!/usr/bin/env python3
"""
Test Timing Update Script
日報時刻を現時刻+2分に設定するスクリプト
"""

import re
from datetime import datetime, timedelta

def update_test_timing():
    """日報時刻を現時刻+2分に更新"""
    
    # Calculate target time
    target_time = datetime.now() + timedelta(minutes=2)
    new_hour = target_time.hour
    new_minute = target_time.minute
    
    print(f"🕐 Setting daily report time to: {new_hour:02d}:{new_minute:02d}")
    
    # Read current file
    with open('src/core/daily_workflow.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the time
    pattern = r'time\(\d+, \d+\)'
    replacement = f'time({new_hour}, {new_minute})'
    updated_content = re.sub(pattern, replacement, content, count=1)
    
    # Write back
    with open('src/core/daily_workflow.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✅ Updated daily_workflow.py: time({new_hour}, {new_minute})")
    print(f"📅 Daily report will trigger at: {target_time.strftime('%H:%M:%S')}")

def reset_to_production():
    """日報時刻を本番設定(6:00)に戻す"""
    
    print("🕐 Resetting daily report time to production: 06:00")
    
    # Read current file
    with open('src/core/daily_workflow.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the time to 6:00
    pattern = r'time\(\d+, \d+\)'
    replacement = 'time(6, 0)'
    updated_content = re.sub(pattern, replacement, content, count=1)
    
    # Also update message to remove [TEST]
    test_message_pattern = r'🧠 \*\*\[TEST\] 長期記憶化処理開始\*\*\\n\\n.*?⚠️ \*\*これはテスト実行です\*\*'
    production_message = '🧠 **長期記憶化処理開始**\\n\\n今日の記憶を統合分析中です...\\n処理完了次第、日報と会議開始をお知らせします。'
    updated_content = re.sub(test_message_pattern, production_message, updated_content, flags=re.DOTALL)
    
    # Write back
    with open('src/core/daily_workflow.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Updated daily_workflow.py: time(6, 0)")
    print("📅 Daily report will trigger at: 06:00 (production)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "production":
        reset_to_production()
    else:
        update_test_timing()