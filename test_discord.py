#!/usr/bin/env python3
"""
簡単なDiscord接続テスト
"""
import os
import asyncio
import logging
import discord
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        super().__init__(intents=intents)
        
        # 監視チャンネルID
        self.monitored_channels = [
            1383963657137946664,  # COMMAND_CENTER
            1383981653046726728,  # CREATION
            1383968516033478727,  # DEVELOPMENT
            1383966355962990653   # LOUNGE
        ]
    
    async def on_ready(self):
        logger.info(f'✅ {self.user} としてログインしました')
        logger.info(f'サーバー数: {len(self.guilds)}')
        for guild in self.guilds:
            logger.info(f'  - {guild.name} (ID: {guild.id})')
            for channel in guild.text_channels:
                logger.info(f'    📺 {channel.name} (ID: {channel.id})')
        logger.info(f'監視チャンネル: {self.monitored_channels}')
    
    async def on_message(self, message):
        # 自分のメッセージは無視
        if message.author == self.user:
            return
            
        # ボットメッセージは無視
        if message.author.bot:
            return
        
        logger.info(f'📨 メッセージ受信: #{message.channel.name} ({message.channel.id}) - {message.author} -> {message.content[:50]}...')
        
        # 監視チャンネルかチェック
        if message.channel.id not in self.monitored_channels:
            logger.info(f'⚠️ 非監視チャンネル: {message.channel.id}')
            return
        
        logger.info(f'✅ 監視チャンネルでのメッセージ処理中...')
        
        # 簡単な応答テスト
        if message.content.lower().startswith('test'):
            await message.channel.send('🤖 テスト応答: システム正常動作中！')
        elif '@' in message.content:
            await message.channel.send(f'📢 メンション検知: {message.content}')

async def main():
    """メイン関数"""
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    if not token:
        logger.error('DISCORD_RECEPTION_TOKENが設定されていません')
        return
    
    bot = TestBot()
    
    try:
        logger.info('Discord接続テスト開始...')
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info('テスト終了')
        await bot.close()
    except Exception as e:
        logger.error(f'エラー: {e}')
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())