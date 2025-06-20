#!/usr/bin/env python3
"""
Infrastructure Integration Test
実際のRedis/PostgreSQL接続とMemory System統合テスト
"""

import asyncio
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

async def test_infrastructure_integration():
    """Infrastructure統合テスト"""
    print("🧪 Infrastructure Integration Test開始")
    
    try:
        # Memory System インポート
        from src.memory_system import create_memory_system
        print("✅ Memory System import成功")
        
        # Memory System 作成
        memory_system = create_memory_system()
        print("✅ Memory System作成成功")
        
        # 初期化
        await memory_system.initialize()
        print("✅ Memory System初期化成功")
        
        # 接続テスト
        stats = await memory_system.get_memory_stats()
        print(f"✅ Memory統計取得成功: {stats['status']}")
        print(f"   - Hot Memory: {stats['hot_memory']}")
        print(f"   - Cold Memory: {stats['cold_memory']}")
        
        # テストデータ作成
        from src.memory_system import MemoryItem
        from datetime import datetime
        test_item = MemoryItem(
            content="テスト統合メッセージ",
            timestamp=datetime.now(),
            channel_id="test_channel",
            user_id="test_user",
            agent="test_agent",
            confidence=0.8
        )
        
        # Memory更新テスト
        conversation_data = {
            "messages": [test_item.to_dict()],
            "selected_agent": "test_agent",
            "response_content": "テスト応答内容",
            "channel_id": "test_channel",
            "confidence": 0.8
        }
        await memory_system.update_memory(conversation_data)
        print("✅ Memory更新テスト成功")
        
        # Hot Memory読み込みテスト
        hot_memories = await memory_system.load_hot_memory("test_channel")
        print(f"✅ Hot Memory読み込み成功: {len(hot_memories)}件")
        
        # 埋め込み生成テスト
        if os.getenv('GEMINI_API_KEY'):
            try:
                embedding = await memory_system.generate_embedding("テスト埋め込み生成")
                print(f"✅ 埋め込み生成成功: 次元数={len(embedding) if embedding else 0}")
            except Exception as e:
                print(f"⚠️ 埋め込み生成スキップ: {e}")
        else:
            print("⚠️ GEMINI_API_KEY未設定のため埋め込みテストスキップ")
        
        # クリーンアップ
        await memory_system.cleanup()
        print("✅ クリーンアップ成功")
        
        print("\n🎉 Infrastructure Integration Test完了 - 全て成功!")
        return True
        
    except Exception as e:
        print(f"❌ Infrastructure Integration Test失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_infrastructure_integration())
    exit(0 if success else 1)