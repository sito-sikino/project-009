#!/usr/bin/env python3
"""
Spectra専用送信ボット - 総合サポートエージェント（実AI応答版）
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

class SpectraOutputBot(discord.Client):
    """Spectra専用送信ボット（実AI応答版）"""
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.agent_name = "spectra"
        
        # AI応答システム初期化
        self.gemini_client = GeminiClient(api_key=os.getenv('GEMINI_API_KEY'))
        self.memory_system = create_improved_memory_system()
        self.supervisor = AgentSupervisor(
            gemini_client=self.gemini_client,
            memory_system=self.memory_system
        )
        
    async def on_ready(self):
        logger.info(f'🎨 Spectra Bot起動: {self.user}')
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("🎨 総合サポート待機中")
        )
        
        # キュー監視開始
        asyncio.create_task(self.monitor_queue())
        logger.info('🔍 Spectra: キュー監視開始')
        
    async def monitor_queue(self):
        """メッセージキュー監視"""
        while True:
            try:
                await self.process_my_messages()
                await asyncio.sleep(3)  # 3秒ごとにチェック
            except Exception as e:
                logger.error(f'🎨 Spectra キュー監視エラー: {e}')
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
                    message_data['processed_by'] = f"spectra_{self.user.id}"
                    message_data['processed_at'] = datetime.now().isoformat()
                
                # 更新されたキューを保存
                async with aiofiles.open(MESSAGE_QUEUE_FILE, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(queue_data, indent=2, ensure_ascii=False))
                    
        except Exception as e:
            logger.error(f'🎨 Spectra メッセージ処理エラー: {e}')
            
    async def handle_message(self, message_data):
        """Spectraとして実AI応答"""
        try:
            channel = self.get_channel(int(message_data['channel_id']))
            if not channel:
                logger.error(f'🎨 Spectra: チャンネル {message_data["channel_id"]} が見つかりません')
                return
                
            # LangGraph Supervisor で実AI応答生成
            logger.info(f'🎨 Spectra: 実AI応答生成開始 - {message_data["content"][:50]}...')
            
            initial_state = {
                'messages': [{'role': 'user', 'content': message_data['content']}],
                'channel_id': message_data['channel_id'],
                'user_id': message_data['author_id'],
                'message_id': message_data.get('id', 'unknown'),
                'selected_agent': 'spectra',  # 強制的にSpectraを選択
                'agent_personality': {
                    'name': 'Spectra Communicator',
                    'role': '総合サポートエージェント',
                    'traits': [
                        'メタ進行役として議論の構造化を得意とする',
                        '全体的な方針整理と一般対話のファシリテーター',
                        'チーム間のコミュニケーション促進',
                        'プロジェクト管理と意思決定支援',
                        '情報統合とまとめ作業'
                    ],
                    'communication_style': '組織的で整理された応答、全体最適の視点',
                    'emoji': '🎨'
                }
            }
            
            # Supervisor経由でAI応答生成
            supervisor_result = await self.supervisor.process_message(initial_state)
            
            if 'response_content' in supervisor_result and supervisor_result['response_content']:
                response = supervisor_result['response_content']
                
                # Spectra個性の付加（必要に応じて）
                if not response.startswith('🎨'):
                    response = f"🎨 **Spectra Communicator**\n\n{response}"
                    
                await channel.send(response)
                logger.info(f'🎨 Spectra実AI応答完了: {message_data["author"]} in #{channel.name}')
                logger.info(f'🎨 Supervisor結果: {supervisor_result["selected_agent"]} (信頼度: {supervisor_result.get("confidence", "不明")})')
            else:
                # フォールバック応答
                fallback_response = f"🎨 **Spectra Communicator**\n\n<@{message_data['author_id']}>さん、申し訳ございません。現在システムの調整中です。少々お待ちください。"
                await channel.send(fallback_response)
                logger.warning(f'🎨 Spectra フォールバック応答: supervisor結果不正 - {supervisor_result}')
            
        except Exception as e:
            logger.error(f'🎨 Spectra実AI応答エラー: {e}')
            
            # エラー時フォールバック
            try:
                error_response = f"🎨 **Spectra Communicator**\n\n<@{message_data['author_id']}>さん、システムに一時的な問題が発生しています。再度お試しください。"
                await channel.send(error_response)
            except Exception as fallback_error:
                logger.error(f'🎨 Spectra フォールバック送信エラー: {fallback_error}')

async def main():
    """Spectra Bot専用実行"""
    token = os.getenv('DISCORD_SPECTRA_TOKEN')
    if not token:
        logger.error('❌ DISCORD_SPECTRA_TOKEN が見つかりません')
        return
        
    bot = SpectraOutputBot()
    
    try:
        logger.info('🚀 Spectra送信ボット開始...')
        await bot.start(token)
    except Exception as e:
        logger.error(f'❌ Spectra Bot エラー: {e}')

if __name__ == '__main__':
    asyncio.run(main())