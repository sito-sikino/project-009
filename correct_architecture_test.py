#!/usr/bin/env python3
"""
正しいアーキテクチャ実装テスト
Reception Bot: 受信のみ（返信なし）
Output Bots: 各自のアイデンティティで個別送信
"""
import os
import asyncio
import logging
import discord
from dotenv import load_dotenv
import aiofiles
import json
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 共有メッセージキュー（ファイルベース簡易実装）
MESSAGE_QUEUE_FILE = "message_queue.json"

class ReceptionOnlyBot(discord.Client):
    """受信専用ボット - 返信は一切しない"""
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        
    async def on_ready(self):
        logger.info(f'🔵 Reception Bot起動: {self.user}')
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("📥 受信専用モード")
        )
        
    async def on_message(self, message):
        if message.author == self.user or message.author.bot:
            return
            
        logger.info(f'📥 Reception: {message.author} -> {message.content[:50]}')
        
        # メッセージ分析とルーティング
        target_bot = self.determine_target_bot(message.content)
        
        # メッセージキューに追加（Output Botが処理）
        await self.add_to_queue(message, target_bot)
        
        logger.info(f'📤 Routing: {target_bot} にメッセージ転送')
        
    def determine_target_bot(self, content):
        """メッセージ内容からターゲットボット決定"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['spectra', '創作', 'アイデア', '物語']):
            return 'spectra'
        elif any(word in content_lower for word in ['lynq', '技術', 'プログラム', 'コード']):
            return 'lynq'
        elif any(word in content_lower for word in ['paz', '手伝', 'サポート', '相談']):
            return 'paz'
        else:
            return 'paz'  # デフォルト
            
    async def add_to_queue(self, message, target_bot):
        """メッセージキューに追加"""
        queue_item = {
            'id': str(message.id),
            'content': message.content,
            'author': str(message.author),
            'channel_id': str(message.channel.id),
            'target_bot': target_bot,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 既存キュー読み込み
            try:
                async with aiofiles.open(MESSAGE_QUEUE_FILE, 'r') as f:
                    queue_data = json.loads(await f.read())
            except FileNotFoundError:
                queue_data = []
            
            # 新しいメッセージ追加
            queue_data.append(queue_item)
            
            # キュー保存
            async with aiofiles.open(MESSAGE_QUEUE_FILE, 'w') as f:
                await f.write(json.dumps(queue_data, indent=2))
                
        except Exception as e:
            logger.error(f'キューエラー: {e}')

class OutputBot(discord.Client):
    """送信専用ボット基底クラス"""
    
    def __init__(self, bot_name, bot_color):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.bot_name = bot_name
        self.bot_color = bot_color
        
    async def on_ready(self):
        logger.info(f'🟢 {self.bot_name} 起動: {self.user}')
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(f"🤖 {self.bot_name} 待機中")
        )
        
        # メッセージキュー監視開始
        asyncio.create_task(self.monitor_queue())
        
    async def monitor_queue(self):
        """メッセージキュー監視"""
        while True:
            try:
                await self.process_queue()
                await asyncio.sleep(2)  # 2秒ごとにチェック
            except Exception as e:
                logger.error(f'{self.bot_name} キュー監視エラー: {e}')
                await asyncio.sleep(5)
                
    async def process_queue(self):
        """自分宛てのメッセージを処理"""
        try:
            async with aiofiles.open(MESSAGE_QUEUE_FILE, 'r') as f:
                queue_data = json.loads(await f.read())
        except FileNotFoundError:
            return
            
        # 自分宛てのメッセージを抽出
        my_messages = [msg for msg in queue_data if msg['target_bot'] == self.bot_name.lower()]
        remaining_messages = [msg for msg in queue_data if msg['target_bot'] != self.bot_name.lower()]
        
        # 処理対象がある場合
        if my_messages:
            for message_data in my_messages:
                await self.handle_message(message_data)
                
            # 処理済みメッセージを削除
            async with aiofiles.open(MESSAGE_QUEUE_FILE, 'w') as f:
                await f.write(json.dumps(remaining_messages, indent=2))
                
    async def handle_message(self, message_data):
        """メッセージ処理（サブクラスで実装）"""
        pass

class SpectraBot(OutputBot):
    """Spectra - 創作支援エージェント"""
    
    def __init__(self):
        super().__init__("Spectra", "🎨")
        
    async def handle_message(self, message_data):
        channel = self.get_channel(int(message_data['channel_id']))
        if not channel:
            return
            
        response = f"""🎨 **Spectra - 創作支援**

{message_data['author']}さん、創作のお手伝いをします！

**今日のクリエイティブ提案:**
• 夢を編む職人の工房
• 色彩が音楽になる世界  
• 時を止める図書館の秘密

どんな創作をお考えですか？ ✨"""
        
        await channel.send(response)
        logger.info(f'🎨 Spectra応答完了: {message_data["author"]}')

class LynQBot(OutputBot):
    """LynQ - 技術サポートエージェント"""
    
    def __init__(self):
        super().__init__("LynQ", "💻")
        
    async def handle_message(self, message_data):
        channel = self.get_channel(int(message_data['channel_id']))
        if not channel:
            return
            
        response = f"""💻 **LynQ - 技術サポート**

{message_data['author']}さん、技術的なサポートを提供します！

**対応分野:**
• Python/JavaScript開発
• Discord Bot構築
• API統合・データベース
• システム設計・デバッグ

具体的な技術課題をお聞かせください 🔧"""
        
        await channel.send(response)
        logger.info(f'💻 LynQ応答完了: {message_data["author"]}')

class PazBot(OutputBot):
    """Paz - 総合サポートエージェント"""
    
    def __init__(self):
        super().__init__("Paz", "🌟")
        
    async def handle_message(self, message_data):
        channel = self.get_channel(int(message_data['channel_id']))
        if not channel:
            return
            
        response = f"""🌟 **Paz - 総合サポート**

{message_data['author']}さん、何でもサポートします！

**サービス範囲:**
• 質問・相談対応
• プロジェクト支援
• 情報整理・まとめ
• コミュニケーション補助

どのようなサポートが必要でしょうか？ 🤝"""
        
        await channel.send(response)
        logger.info(f'🌟 Paz応答完了: {message_data["author"]}')

async def run_reception_bot():
    """Reception Bot実行"""
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    bot = ReceptionOnlyBot()
    await bot.start(token)

async def run_spectra_bot():
    """Spectra Bot実行"""
    token = os.getenv('DISCORD_SPECTRA_TOKEN')
    bot = SpectraBot()
    await bot.start(token)

async def run_lynq_bot():
    """LynQ Bot実行"""
    token = os.getenv('DISCORD_LYNQ_TOKEN')
    bot = LynQBot()
    await bot.start(token)

async def run_paz_bot():
    """Paz Bot実行"""
    token = os.getenv('DISCORD_PAZ_TOKEN')
    bot = PazBot()
    await bot.start(token)

async def main():
    """全ボット並列実行"""
    logger.info('🚀 正しいアーキテクチャ: 統合受信・個別送信システム開始')
    
    # 全ボット並列実行
    await asyncio.gather(
        run_reception_bot(),
        run_spectra_bot(), 
        run_lynq_bot(),
        run_paz_bot()
    )

if __name__ == '__main__':
    asyncio.run(main())