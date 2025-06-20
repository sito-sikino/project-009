#!/usr/bin/env python3
"""
Paz専用送信ボット - 創作サポートエージェント（実AI応答版）
Reception Botからのキューを監視してLangGraph Supervisor経由で応答
"""
import os
import asyncio
import logging
import discord
from dotenv import load_dotenv
import aiofiles
import json
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.langgraph_supervisor import AgentSupervisor
from src.gemini_client import GeminiClient
from src.memory_system_improved import create_improved_memory_system

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MESSAGE_QUEUE_FILE = "message_queue.json"

class PazOutputBot(discord.Client):
    """Paz専用送信ボット（実AI応答版）"""
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.agent_name = "paz"
        
        # AI応答システム初期化
        self.gemini_client = GeminiClient(api_key=os.getenv('GEMINI_API_KEY'))
        self.memory_system = create_improved_memory_system()
        self.supervisor = AgentSupervisor(
            gemini_client=self.gemini_client,
            memory_system=self.memory_system
        )
        
    async def on_ready(self):
        logger.info(f'🌟 Paz Bot起動: {self.user}')
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("🌟 創作サポート待機中")
        )
        
        # キュー監視開始
        asyncio.create_task(self.monitor_queue())
        logger.info('🔍 Paz: キュー監視開始')
        
    async def monitor_queue(self):
        """メッセージキュー監視"""
        while True:
            try:
                await self.process_my_messages()
                await asyncio.sleep(3)  # 3秒ごとにチェック
            except Exception as e:
                logger.error(f'🌟 Paz キュー監視エラー: {e}')
                await asyncio.sleep(5)
                
    async def process_my_messages(self):
        """自分宛てのメッセージを処理"""
        try:
            # キュー読み込み
            try:
                async with aiofiles.open(MESSAGE_QUEUE_FILE, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    queue_data = json.loads(content) if content.strip() else []
            except (FileNotFoundError, json.JSONDecodeError):
                return
                
            # 自分宛ての未処理メッセージを抽出
            my_messages = [
                msg for msg in queue_data 
                if msg['target_agent'] == self.agent_name and not msg.get('processed', False)
            ]
            
            if my_messages:
                for message_data in my_messages:
                    await self.handle_message(message_data)
                    
                    # 処理済みマーク
                    message_data['processed'] = True
                    message_data['processed_by'] = f"paz_{self.user.id}"
                    message_data['processed_at'] = datetime.now().isoformat()
                
                # 更新されたキューを保存
                async with aiofiles.open(MESSAGE_QUEUE_FILE, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(queue_data, indent=2, ensure_ascii=False))
                    
        except Exception as e:
            logger.error(f'🌟 Paz メッセージ処理エラー: {e}')
            
    async def handle_message(self, message_data):
        """Pazとして実AI応答"""
        try:
            channel = self.get_channel(int(message_data['channel_id']))
            if not channel:
                logger.error(f'🌟 Paz: チャンネル {message_data["channel_id"]} が見つかりません')
                return
                
            # LangGraph Supervisor で実AI応答生成
            logger.info(f'🌟 Paz: 実AI応答生成開始 - {message_data["content"][:50]}...')
            
            initial_state = {
                'messages': [{'role': 'user', 'content': message_data['content']}],
                'channel_id': message_data['channel_id'],
                'user_id': message_data['author_id'],
                'message_id': message_data.get('id', 'unknown'),
                'selected_agent': 'paz',  # 強制的にPazを選択
                'agent_personality': {
                    'name': 'Paz',
                    'role': '創作サポートエージェント',
                    'traits': [
                        '発散創造役として革新的アイデアを得意とする',
                        '創造的テーマとブレインストーミングのスペシャリスト',
                        'アート・文学・音楽の総合クリエイター',
                        '想像力拡張と革新的チャレンジ',
                        '自由な発想と枠組み超越思考'
                    ],
                    'communication_style': 'インスピレーショナルで創造的な表現、自由な発想促進',
                    'emoji': '🌟'
                }
            }
            
            # Supervisor経由でAI応答生成
            supervisor_result = await self.supervisor.process_message(initial_state)
            
            if 'response_content' in supervisor_result and supervisor_result['response_content']:
                response = supervisor_result['response_content']
                
                # Paz個性の付加（必要に応じて）
                if not response.startswith('🌟'):
                    response = f"🌟 **Paz**\n\n{response}"
                    
                await channel.send(response)
                logger.info(f'🌟 Paz実AI応答完了: {message_data["author"]} in #{channel.name}')
                logger.info(f'🌟 Supervisor結果: {supervisor_result["selected_agent"]} (信頼度: {supervisor_result.get("confidence", "不明")})')
            else:
                # フォールバック応答
                fallback_response = f"🌟 **Paz**\n\n<@{message_data['author_id']}>さん、創造の源泉に一時的にアクセスできません。少々お待ちください。"
                await channel.send(fallback_response)
                logger.warning(f'🌟 Paz フォールバック応答: supervisor結果不正 - {supervisor_result}')
            
        except Exception as e:
            logger.error(f'🌟 Paz実AI応答エラー: {e}')
            
            # エラー時フォールバック
            try:
                error_response = f"🌟 **Paz**\n\n<@{message_data['author_id']}>さん、創造のシステムに一時的な問題が発生しています。再度お試しください。"
                await channel.send(error_response)
            except Exception as fallback_error:
                logger.error(f'🌟 Paz フォールバック送信エラー: {fallback_error}')

async def main():
    """Paz Bot専用実行"""
    token = os.getenv('DISCORD_PAZ_TOKEN')
    if not token:
        logger.error('❌ DISCORD_PAZ_TOKEN が見つかりません')
        return
        
    bot = PazOutputBot()
    
    try:
        logger.info('🚀 Paz送信ボット開始...')
        await bot.start(token)
    except Exception as e:
        logger.error(f'❌ Paz Bot エラー: {e}')

if __name__ == '__main__':
    asyncio.run(main())