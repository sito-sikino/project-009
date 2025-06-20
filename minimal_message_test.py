#!/usr/bin/env python3
"""
最小限のメッセージテスト - 問題の根本特定用
"""
import os
import asyncio
import logging
import discord
from dotenv import load_dotenv

load_dotenv()

# 詳細ログ有効化
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Discord.pyのデバッグログも有効化
logging.getLogger('discord').setLevel(logging.DEBUG)
logging.getLogger('discord.gateway').setLevel(logging.DEBUG)
logging.getLogger('discord.client').setLevel(logging.DEBUG)

class MinimalBot(discord.Client):
    def __init__(self):
        # 最大限のIntents設定
        intents = discord.Intents.all()  # 全Intent有効化
        super().__init__(intents=intents)
        self.message_count = 0
        
    async def on_ready(self):
        logger.critical("🔍 MINIMAL MESSAGE TEST 開始")
        logger.critical(f"ボット: {self.user} (ID: {self.user.id})")
        logger.critical(f"Discord.py バージョン: {discord.__version__}")
        logger.critical(f"設定Intents: {self.intents}")
        
        # サーバー詳細確認
        for guild in self.guilds:
            logger.critical(f"サーバー: {guild.name} (ID: {guild.id})")
            logger.critical(f"メンバー数: {guild.member_count}")
            logger.critical(f"ボット権限: {guild.me.guild_permissions}")
            
            # チャンネル権限詳細確認
            for channel in guild.text_channels:
                perms = channel.permissions_for(guild.me)
                logger.critical(f"  📺 {channel.name}: read_messages={perms.read_messages}, send_messages={perms.send_messages}")
        
        logger.critical("=" * 60)
        logger.critical("🧪 テスト: いずれかのチャンネルで 'minimal-test' と送信")
        logger.critical("=" * 60)
    
    async def on_message(self, message):
        """メッセージイベント - 最優先デバッグ"""
        self.message_count += 1
        
        # 必ず実行されるログ
        logger.critical("🚨 MESSAGE EVENT FIRED!")
        logger.critical(f"メッセージ #{self.message_count}")
        logger.critical(f"作者: {message.author} (Bot: {message.author.bot})")
        logger.critical(f"チャンネル: #{message.channel.name} ({message.channel.id})")
        logger.critical(f"内容: '{message.content}'")
        logger.critical(f"メッセージID: {message.id}")
        logger.critical("=" * 40)
        
        # 自分のメッセージでない場合のみ応答
        if message.author != self.user:
            if 'minimal-test' in message.content.lower():
                try:
                    await message.channel.send("🔥 **MINIMAL TEST SUCCESS!** - メッセージイベント正常動作確認")
                    logger.critical("✅ 応答送信成功!")
                except Exception as e:
                    logger.critical(f"❌ 応答送信失敗: {e}")
            elif message.content.lower() == 'debug-info':
                # デバッグ情報送信
                info = f"""```
ボット: {self.user}
受信メッセージ数: {self.message_count}
Discord.py: {discord.__version__}
Python: {os.sys.version}
```"""
                await message.channel.send(info)
    
    async def on_error(self, event, *args, **kwargs):
        logger.critical(f"🚨 ERROR in {event}: {args}, {kwargs}")
    
    async def on_disconnect(self):
        logger.critical("🚨 DISCONNECTED from Discord")
    
    async def on_resumed(self):
        logger.critical("🔄 RESUMED connection to Discord")

async def main():
    # トークン確認
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    if not token:
        logger.critical("❌ DISCORD_RECEPTION_TOKEN not found!")
        return
    
    logger.critical(f"トークン (先頭10文字): {token[:10]}...")
    
    bot = MinimalBot()
    
    try:
        logger.critical("🚀 Discord接続開始...")
        await bot.start(token)
    except Exception as e:
        logger.critical(f"❌ 致命的エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())