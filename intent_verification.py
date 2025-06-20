#!/usr/bin/env python3
"""
Intent設定とDiscord Developer Portal設定の完全検証
"""
import os
import asyncio
import logging
import discord
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_token_and_intents():
    """トークンとIntent設定の完全検証"""
    
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    if not token:
        logger.error("❌ トークンが見つかりません")
        return
    
    logger.info("🔍 Discord Developer Portal設定検証開始...")
    logger.info(f"トークン: {token[:25]}...")
    
    # 段階的Intent検証
    intent_tests = [
        ("デフォルト", discord.Intents.default()),
        ("デフォルト+メッセージコンテンツ", discord.Intents.default()),
        ("最小限", discord.Intents.none()),
        ("全て", discord.Intents.all())
    ]
    
    # デフォルト+メッセージコンテンツの設定
    default_with_content = discord.Intents.default()
    default_with_content.message_content = True
    intent_tests[1] = ("デフォルト+メッセージコンテンツ", default_with_content)
    
    # 最小限の設定
    minimal = discord.Intents.none()
    minimal.guilds = True
    minimal.guild_messages = True
    intent_tests[2] = ("最小限", minimal)
    
    for test_name, intents in intent_tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 テスト: {test_name}")
        logger.info(f"Intent値: {intents.value}")
        logger.info(f"message_content: {intents.message_content}")
        logger.info(f"guilds: {intents.guilds}")
        logger.info(f"guild_messages: {intents.guild_messages}")
        
        try:
            client = discord.Client(intents=intents)
            
            @client.event
            async def on_ready():
                logger.info(f"✅ {test_name} - 接続成功!")
                logger.info(f"   ボット: {client.user}")
                logger.info(f"   サーバー数: {len(client.guilds)}")
                
                # 5秒待機してから切断
                await asyncio.sleep(5)
                await client.close()
                logger.info(f"   {test_name} - 切断完了")
            
            @client.event
            async def on_connect():
                logger.info(f"🔗 {test_name} - Gateway接続")
            
            @client.event
            async def on_disconnect():
                logger.info(f"🔌 {test_name} - Gateway切断")
            
            # 10秒でタイムアウト
            await asyncio.wait_for(client.start(token), timeout=10.0)
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ {test_name} - タイムアウト")
        except discord.PrivilegedIntentsRequired as e:
            logger.error(f"❌ {test_name} - Privileged Intent エラー: {e}")
        except discord.LoginFailure as e:
            logger.error(f"❌ {test_name} - ログイン失敗: {e}")
        except Exception as e:
            logger.error(f"❌ {test_name} - その他のエラー: {e}")
        
        # 各テスト間に待機
        await asyncio.sleep(2)
    
    logger.info("\n" + "="*60)
    logger.info("🎯 Discord Developer Portal確認事項:")
    logger.info("1. Applications > RECEIVERボット > Bot セクション")
    logger.info("2. Privileged Gateway Intents:")
    logger.info("   ✅ PRESENCE INTENT")
    logger.info("   ✅ SERVER MEMBERS INTENT") 
    logger.info("   ✅ MESSAGE CONTENT INTENT")
    logger.info("3. 全てONにして Save Changes をクリック")
    logger.info("4. Bot TokenをReset Tokenして新しいトークンに変更")
    logger.info("=" * 60)

if __name__ == '__main__':
    asyncio.run(verify_token_and_intents())