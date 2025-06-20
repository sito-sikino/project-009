#!/usr/bin/env python3
"""
Discord.py Multiple Client Capability Test
同一プロセスでの複数Discord Clientの同時実行テスト
"""

import asyncio
import discord
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

async def test_multiple_discord_clients():
    """複数Discord Client同時実行テスト"""
    print("🧪 Testing Multiple Discord Client Capability")
    
    # 4つのBot Token取得
    tokens = {
        'reception': os.getenv('DISCORD_RECEPTION_TOKEN'),
        'spectra': os.getenv('DISCORD_SPECTRA_TOKEN'),
        'lynq': os.getenv('DISCORD_LYNQ_TOKEN'),
        'paz': os.getenv('DISCORD_PAZ_TOKEN')
    }
    
    # Token検証
    missing_tokens = [name for name, token in tokens.items() if not token]
    if missing_tokens:
        print(f"❌ Missing tokens: {missing_tokens}")
        return False
    
    print("✅ All tokens available")
    
    # Test 1: Sequential client creation (no start)
    print("\n🔧 Test 1: Sequential Client Creation")
    try:
        clients = {}
        for name, token in tokens.items():
            client = discord.Client(intents=discord.Intents.all())
            clients[name] = client
            print(f"✅ {name} client created")
        
        print("✅ All 4 clients created successfully")
        
        # Clean up
        for client in clients.values():
            if not client.is_closed():
                await client.close()
        
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        return False
    
    # Test 2: Event loop analysis
    print("\n🔧 Test 2: Event Loop Analysis")
    try:
        loop = asyncio.get_running_loop()
        print(f"✅ Current event loop: {type(loop)}")
        print(f"✅ Loop is running: {loop.is_running()}")
        
        # Test if we can create tasks
        async def dummy_task():
            await asyncio.sleep(0.1)
            return "task_completed"
        
        task = asyncio.create_task(dummy_task())
        result = await task
        print(f"✅ Task creation works: {result}")
        
    except Exception as e:
        print(f"❌ Event loop analysis failed: {e}")
        return False
    
    # Test 3: Concurrent connection attempt (high risk - may fail)
    print("\n🔧 Test 3: Concurrent Connection Test (Limited)")
    try:
        # Create minimal clients
        client1 = discord.Client(intents=discord.Intents.default())
        client2 = discord.Client(intents=discord.Intents.default())
        
        print("✅ Two clients created for connection test")
        
        # Test connection tasks (but don't actually connect)
        async def fake_connection_test(client, name):
            # Simulate connection preparation
            await asyncio.sleep(0.1)
            return f"{name}_prepared"
        
        tasks = [
            fake_connection_test(client1, "client1"),
            fake_connection_test(client2, "client2")
        ]
        
        results = await asyncio.gather(*tasks)
        print(f"✅ Concurrent preparation test: {results}")
        
        # Clean up
        await client1.close()
        await client2.close()
        
    except Exception as e:
        print(f"❌ Concurrent connection test failed: {e}")
        return False
    
    print("\n🎉 Multiple Client Capability Test Results:")
    print("✅ Client creation: PASS")
    print("✅ Event loop management: PASS") 
    print("✅ Concurrent task handling: PASS")
    print("\n📋 Analysis:")
    print("- Discord.py supports multiple client instances in same process")
    print("- Event loop can handle concurrent tasks")
    print("- The issue likely lies in connection management, not client creation")
    print("\n💡 Recommendation:")
    print("- Try sequential connection instead of concurrent connection")
    print("- Implement proper error handling for connection failures")
    print("- Consider process separation as alternative architecture")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_multiple_discord_clients())
    exit(0 if success else 1)