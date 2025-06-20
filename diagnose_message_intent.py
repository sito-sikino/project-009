#!/usr/bin/env python3
"""
Message Content Intent 診断スクリプト
"""
import os
import asyncio
import logging
import discord
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiagnosticBot(discord.Client):
    def __init__(self):
        # 明示的なIntents設定
        intents = discord.Intents.default()
        intents.message_content = True  # 重要: Message Content Intent
        intents.guilds = True
        intents.guild_messages = True
        super().__init__(intents=intents)
    
    async def on_ready(self):
        logger.info("=" * 60)
        logger.info("🔍 Discord Message Content Intent 診断結果")
        logger.info("=" * 60)
        logger.info(f"✅ ボット名: {self.user}")
        logger.info(f"✅ 接続成功: {len(self.guilds)} サーバー")
        
        # Intent確認
        logger.info("\n📋 設定されたIntents:")
        logger.info(f"  - message_content: {self.intents.message_content}")
        logger.info(f"  - guilds: {self.intents.guilds}")
        logger.info(f"  - guild_messages: {self.intents.guild_messages}")
        
        # サーバー・チャンネル情報
        for guild in self.guilds:
            logger.info(f"\n🏰 サーバー: {guild.name}")
            for channel in guild.text_channels:
                logger.info(f"  📺 {channel.name} (ID: {channel.id})")
        
        logger.info("\n🧪 テスト指示:")
        logger.info("  1. いずれかのチャンネルで 'intent-test' と送信してください")
        logger.info("  2. ボットが反応すれば Message Content Intent 有効化成功です")
        logger.info("=" * 60)
    
    async def on_message(self, message):
        # 自分は無視
        if message.author == self.user:
            return
        
        # 全メッセージをログ出力（デバッグ用）
        logger.info(f"📨 【メッセージ受信】")
        logger.info(f"  チャンネル: #{message.channel.name} ({message.channel.id})")
        logger.info(f"  ユーザー: {message.author}")
        logger.info(f"  内容: {message.content}")
        
        # 特別テストメッセージに反応
        if 'intent-test' in message.content.lower():
            await message.channel.send("🎉 **Message Content Intent 正常動作確認！**\n✅ ボットがメッセージ内容を読めています")
            logger.info("✅ Message Content Intent テスト成功!")
        
        # 通常の 'test' にも反応
        elif message.content.lower().startswith('test'):
            await message.channel.send("🤖 診断テスト: システム正常!")
            logger.info("✅ 基本テスト成功!")

async def main():
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    if not token:
        logger.error("❌ DISCORD_RECEPTION_TOKEN が設定されていません")
        return
    
    bot = DiagnosticBot()
    
    try:
        logger.info("🚀 Message Content Intent 診断開始...")
        await bot.start(token)
    except Exception as e:
        logger.error(f"❌ エラー: {e}")

if __name__ == '__main__':
    asyncio.run(main())