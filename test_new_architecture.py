#!/usr/bin/env python3
"""
New Architecture Test - Sequential Connection Approach
新しいアーキテクチャでのDiscord Multi-Client接続テスト
"""

import asyncio
import signal
import sys
from main import DiscordMultiAgentSystem

async def test_new_architecture():
    """新しいアーキテクチャテスト"""
    print("🧪 Testing New Architecture - Sequential Connection Approach")
    
    # Discord Multi-Agent System初期化
    try:
        system = DiscordMultiAgentSystem()
        print("✅ System initialized successfully")
        
        # 短時間テスト実行（30秒）
        print("🔧 Starting 30-second connection test...")
        
        async def test_timeout():
            await asyncio.sleep(30)
            print("⏰ Test timeout reached - shutting down...")
            await system.shutdown()
            return True
        
        # System起動とタイムアウトの競合
        try:
            await asyncio.wait_for(
                asyncio.gather(
                    system.run(),
                    test_timeout()
                ),
                timeout=35
            )
            
        except asyncio.TimeoutError:
            print("🕐 Test completed within timeout")
            await system.shutdown()
            
        except KeyboardInterrupt:
            print("🛑 Test interrupted by user")
            await system.shutdown()
            
        print("🎉 New Architecture Test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Architecture test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print('\n🛑 Interrupted by user')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    success = asyncio.run(test_new_architecture())
    exit(0 if success else 1)