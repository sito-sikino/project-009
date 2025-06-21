#!/usr/bin/env python3
"""
Reception専用ボット - 受信のみ、返信なし
他のボットにメッセージをルーティング
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

MESSAGE_QUEUE_FILE = "message_queue.json"

class ReceptionOnlyBot(discord.Client):
    """受信専用ボット"""
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.processed_messages = set()
        
    async def on_ready(self):
        logger.info(f'📥 Reception Bot専用起動: {self.user}')
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("📥 受信専用 - 返信なし")
        )
        logger.info('=' * 50)
        logger.info('🔵 RECEPTION ONLY MODE')
        logger.info('📥 このボットは受信のみ、返信は他のボットが行います')
        logger.info('🧪 テスト: @Spectra @LynQ @Paz にメンションしてください')
        logger.info('=' * 50)
        
    async def on_message(self, message):
        # 自分・ボットメッセージは無視
        if message.author == self.user or message.author.bot:
            return
            
        # 重複処理防止
        if message.id in self.processed_messages:
            return
        self.processed_messages.add(message.id)
        
        logger.info(f'📥 [RECEPTION] {message.author}: {message.content[:100]}')
        
        # エージェント判定
        target_agent = self.determine_agent(message.content)
        logger.info(f'🎯 [ROUTING] -> {target_agent.upper()}')
        
        # キューに追加
        await self.add_to_queue(message, target_agent)
        
        # ⚠️ 重要: Reception Botは返信しない！
        logger.info('✅ [RECEPTION] メッセージ処理完了（返信なし）')
        
    def determine_agent(self, content):
        """エージェント選択ロジック"""
        content_lower = content.lower()
        
        # メンション検出
        if '<@1364635447225225286>' in content or 'spectra' in content_lower:
            return 'spectra'
        elif '<@1364657009009627237>' in content or 'lynq' in content_lower:
            return 'lynq'  
        elif '<@1383050248280346685>' in content or 'paz' in content_lower:
            return 'paz'
            
        # キーワード検出（修正版）
        if any(word in content_lower for word in ['創作', 'アイデア', '物語', '小説', '詩', '音楽', 'アート', 'デザイン']):
            return 'paz'  # Pazが創作サポート
        elif any(word in content_lower for word in ['技術', 'プログラム', 'コード', '開発']):
            return 'lynq'
        else:
            return 'spectra'  # Spectraが総合サポート（デフォルト）
            
    async def add_to_queue(self, message, target_agent):
        """メッセージキューに追加"""
        queue_item = {
            'id': str(message.id),
            'content': message.content,
            'author': str(message.author),
            'author_id': str(message.author.id),
            'channel_id': str(message.channel.id),
            'guild_id': str(message.guild.id),
            'target_agent': target_agent,
            'timestamp': datetime.now().isoformat(),
            'processed': False
        }
        
        try:
            # 既存キュー読み込み
            try:
                async with aiofiles.open(MESSAGE_QUEUE_FILE, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    queue_data = json.loads(content) if content.strip() else []
            except (FileNotFoundError, json.JSONDecodeError):
                queue_data = []
            
            # 重複チェック
            existing_ids = {item['id'] for item in queue_data}
            if queue_item['id'] not in existing_ids:
                queue_data.append(queue_item)
                
                # キュー保存
                async with aiofiles.open(MESSAGE_QUEUE_FILE, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(queue_data, indent=2, ensure_ascii=False))
                    
                logger.info(f'📝 [QUEUE] メッセージ追加: {target_agent}宛て')
            else:
                logger.info(f'⚠️ [QUEUE] 重複メッセージスキップ: {message.id}')
                
        except Exception as e:
            logger.error(f'❌ [QUEUE] エラー: {e}')

async def main():
    """Reception Bot専用実行"""
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    if not token:
        logger.error('❌ DISCORD_RECEPTION_TOKEN が見つかりません')
        return
        
    bot = ReceptionOnlyBot()
    
    try:
        logger.info('🚀 Reception専用ボット開始...')
        await bot.start(token)
    except Exception as e:
        logger.error(f'❌ Reception Bot エラー: {e}')

if __name__ == '__main__':
    asyncio.run(main())