#!/usr/bin/env python3
"""
最終テスト - PRESENCE INTENT込み
"""
import os
import asyncio
import logging
import discord
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalTestBot(discord.Client):
    def __init__(self):
        # 完全なIntents設定
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.message_count = 0
    
    async def on_ready(self):
        logger.info("🎉 FINAL TEST - ボット起動完了!")
        logger.info(f"ボット: {self.user}")
        logger.info(f"Intent値: {self.intents.value}")
        logger.info(f"presence: {self.intents.presences}")
        logger.info(f"members: {self.intents.members}")  
        logger.info(f"message_content: {self.intents.message_content}")
        
        # ステータス設定
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("🧪 メッセージテスト中")
        )
        
        logger.info("=" * 50)
        logger.info("🚨 重要: Discordでボットがオンライン表示されているか確認!")
        logger.info("📨 テスト: 'final-test' と送信してください")
        logger.info("=" * 50)
    
    async def on_message(self, message):
        if message.author == self.user:
            return
            
        self.message_count += 1
        logger.info(f"🔥 MESSAGE RECEIVED #{self.message_count}")
        logger.info(f"   From: {message.author}")
        logger.info(f"   Channel: #{message.channel.name}")
        logger.info(f"   Content: {message.content}")
        
        if 'final-test' in message.content.lower():
            await message.channel.send("🎉 **成功！** PRESENCE INTENT + MESSAGE CONTENT INTENT 動作確認!")
            logger.info("✅ 最終テスト成功!")

async def main():
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    bot = FinalTestBot()
    
    try:
        logger.info("🚀 最終テスト開始...")
        await bot.start(token)
    except Exception as e:
        logger.error(f"❌ エラー: {e}")

if __name__ == '__main__':
    asyncio.run(main())