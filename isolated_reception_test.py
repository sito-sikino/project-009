#!/usr/bin/env python3
"""
隔離されたReception Clientテスト - 競合なし
"""
import os
import asyncio
import logging
import discord
from dotenv import load_dotenv

load_dotenv()

# 詳細ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IsolatedReceptionBot(discord.Client):
    def __init__(self):
        # 完全なIntents設定 - 競合回避
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        
        self.message_count = 0
        self.ready_time = None
        
    async def on_connect(self):
        """Gateway接続確立"""
        logger.critical("🔗 Gateway接続確立!")
        
    async def on_ready(self):
        """ボット準備完了 - Discord上でオンライン表示"""
        import datetime
        self.ready_time = datetime.datetime.now()
        
        logger.critical("=" * 60)
        logger.critical("🎉 ISOLATED RECEPTION BOT - 準備完了!")
        logger.critical(f"ボット名: {self.user}")
        logger.critical(f"ボットID: {self.user.id}")
        logger.critical(f"サーバー数: {len(self.guilds)}")
        logger.critical(f"Discord.py: {discord.__version__}")
        
        # ステータス設定
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("🔥 隔離テスト実行中")
        )
        
        # サーバー詳細表示
        for guild in self.guilds:
            logger.critical(f"📍 サーバー: {guild.name} (ID: {guild.id})")
            logger.critical(f"   メンバー数: {guild.member_count}")
            
            # 権限確認
            bot_member = guild.get_member(self.user.id)
            if bot_member:
                logger.critical(f"   ボット権限: {bot_member.guild_permissions}")
            
            # チャンネル権限確認
            for channel in guild.text_channels:
                perms = channel.permissions_for(guild.me)
                status = "✅" if perms.read_messages and perms.send_messages else "❌"
                logger.critical(f"   {status} #{channel.name}: R={perms.read_messages}, W={perms.send_messages}")
        
        logger.critical("=" * 60)
        logger.critical("🧪 テスト手順:")
        logger.critical("1. Discordでボットがオンライン表示されているか確認")
        logger.critical("2. いずれかのチャンネルで 'isolated-test' と送信")
        logger.critical("3. ボットが応答すれば問題解決!")
        logger.critical("=" * 60)
    
    async def on_message(self, message):
        """メッセージ受信イベント - 最重要"""
        # メッセージカウント
        self.message_count += 1
        
        # 詳細ログ出力
        logger.critical("🔥🔥🔥 MESSAGE EVENT RECEIVED! 🔥🔥🔥")
        logger.critical(f"📨 メッセージ #{self.message_count}")
        logger.critical(f"👤 送信者: {message.author} (Bot: {message.author.bot})")
        logger.critical(f"📺 チャンネル: #{message.channel.name} ({message.channel.id})")
        logger.critical(f"💬 内容: '{message.content}'")
        logger.critical(f"🆔 メッセージID: {message.id}")
        logger.critical(f"⏰ 受信時刻: {message.created_at}")
        
        # 自分のメッセージは処理しない
        if message.author == self.user:
            logger.critical("⚠️ 自分のメッセージのため処理スキップ")
            return
        
        # テストメッセージに応答
        if 'isolated-test' in message.content.lower():
            try:
                response = "🎉 **隔離テスト成功！** 🎉\n✅ Reception Clientが正常にメッセージを受信しています！\n🔥 根本問題解決済み!"
                await message.channel.send(response)
                logger.critical("✅ 応答送信成功! - 隔離テスト完了")
                
                # 統計情報送信
                uptime = (message.created_at.replace(tzinfo=None) - self.ready_time).total_seconds()
                stats = f"📊 統計: 受信メッセージ数={self.message_count}, 稼働時間={uptime:.1f}秒"
                await message.channel.send(stats)
                
            except Exception as e:
                logger.critical(f"❌ 応答送信失敗: {e}")
        
        # その他のテストメッセージ
        elif message.content.lower().startswith('test'):
            await message.channel.send("🤖 基本テスト: Reception Client動作確認")
            logger.critical("✅ 基本テスト応答完了")
    
    async def on_disconnect(self):
        """切断イベント"""
        logger.critical("🔌 Gateway切断!")
    
    async def on_error(self, event, *args, **kwargs):
        """エラーイベント"""
        logger.critical(f"🚨 エラー発生 in {event}: {args}")

async def main():
    """メイン実行"""
    # トークン取得
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    if not token:
        logger.critical("❌ DISCORD_RECEPTION_TOKEN が見つかりません!")
        return
    
    # ボット作成
    bot = IsolatedReceptionBot()
    
    try:
        logger.critical("🚀 隔離されたReception Botテスト開始...")
        logger.critical("📌 この実行では他のDiscordクライアントとの競合なし")
        await bot.start(token)
        
    except KeyboardInterrupt:
        logger.critical("🛑 テスト手動停止")
    except Exception as e:
        logger.critical(f"❌ 致命的エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())