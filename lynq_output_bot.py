#!/usr/bin/env python3
"""
LynQ専用送信ボット - 技術サポートエージェント（実AI応答版）
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

class LynQOutputBot(discord.Client):
    """LynQ専用送信ボット（実AI応答版）"""
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.agent_name = "lynq"
        
        # AI応答システム初期化
        self.gemini_client = GeminiClient(api_key=os.getenv('GEMINI_API_KEY'))
        self.memory_system = create_improved_memory_system()
        self.supervisor = AgentSupervisor(
            gemini_client=self.gemini_client,
            memory_system=self.memory_system
        )
        
    async def on_ready(self):
        logger.info(f'💻 LynQ Bot起動: {self.user}')
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("💻 技術サポート待機中")
        )
        
        # キュー監視開始
        asyncio.create_task(self.monitor_queue())
        logger.info('🔍 LynQ: キュー監視開始')
        
    async def monitor_queue(self):
        """メッセージキュー監視"""
        while True:
            try:
                await self.process_my_messages()
                await asyncio.sleep(3)  # 3秒ごとにチェック
            except Exception as e:
                logger.error(f'💻 LynQ キュー監視エラー: {e}')
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
                    message_data['processed_by'] = f"lynq_{self.user.id}"
                    message_data['processed_at'] = datetime.now().isoformat()
                
                # 更新されたキューを保存
                async with aiofiles.open(MESSAGE_QUEUE_FILE, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(queue_data, indent=2, ensure_ascii=False))
                    
        except Exception as e:
            logger.error(f'💻 LynQ メッセージ処理エラー: {e}')
            
    async def handle_message(self, message_data):
        """LynQとして応答"""
        try:
            channel = self.get_channel(int(message_data['channel_id']))
            if not channel:
                logger.error(f'💻 LynQ: チャンネル {message_data["channel_id"]} が見つかりません')
                return
                
            # LynQ専用応答
            response = f"""💻 **LynQ - 技術サポートエージェント**

<@{message_data['author_id']}>さん、技術的なサポートを提供します！

**対応可能な技術分野:**
🐍 **Python Development**
• Discord.py ボット開発
• AsyncIO/非同期プログラミング
• データ処理・分析
• API統合・Web開発

🌐 **Web Technologies**
• JavaScript/TypeScript
• React/Node.js
• REST API設計
• データベース設計（SQL/NoSQL）

🔧 **System & DevOps**
• Git/GitHub ワークフロー
• Docker/コンテナ化
• CI/CD パイプライン
• クラウドデプロイメント

**どのような技術的課題をお手伝いしましょうか？**
エラーメッセージ、コード、または具体的な問題をお聞かせください！"""
            
            # 実AI応答に変更
            logger.info(f'💻 LynQ: 実AI応答生成開始 - {message_data["content"][:50]}...')
            
            initial_state = {
                'messages': [{'role': 'user', 'content': message_data['content']}],
                'channel_id': message_data['channel_id'],
                'user_id': message_data['author_id'],
                'message_id': message_data.get('id', 'unknown'),
                'selected_agent': 'lynq',
                'agent_personality': {
                    'name': 'LynQ',
                    'role': '技術サポートエージェント',
                    'traits': [
                        '論理収束役として技術的検証を得意とする',
                        '構造化分析と問題解決のスペシャリスト',
                        'プログラミング・システム設計の専門家',
                        'データ分析・パフォーマンス最適化',
                        '技術文書作成と知識共有'
                    ],
                    'communication_style': '論理的で正確な技術解説、具体的な実装提案',
                    'emoji': '💻'
                }
            }
            
            supervisor_result = await self.supervisor.process_message(initial_state)
            
            if 'response_content' in supervisor_result and supervisor_result['response_content']:
                response = supervisor_result['response_content']
                if not response.startswith('💻'):
                    response = f"💻 **LynQ**\n\n{response}"
                await channel.send(response)
                logger.info(f'💻 LynQ実AI応答完了: {message_data["author"]} in #{channel.name}')
                logger.info(f'💻 Supervisor結果: {supervisor_result["selected_agent"]} (信頼度: {supervisor_result.get("confidence", "不明")})')
            else:
                fallback_response = f"💻 **LynQ**\n\n<@{message_data['author_id']}>さん、技術的な問題が発生しています。しばらくお待ちください。"
                await channel.send(fallback_response)
                logger.warning(f'💻 LynQ フォールバック応答: supervisor結果不正 - {supervisor_result}')
            
        except Exception as e:
            logger.error(f'💻 LynQ実AI応答エラー: {e}')
            try:
                error_response = f"💻 **LynQ**\n\n<@{message_data['author_id']}>さん、システムに技術的な問題が発生しています。"
                await channel.send(error_response)
            except Exception as fallback_error:
                logger.error(f'💻 LynQ フォールバック送信エラー: {fallback_error}')

async def main():
    """LynQ Bot専用実行"""
    token = os.getenv('DISCORD_LYNQ_TOKEN')
    if not token:
        logger.error('❌ DISCORD_LYNQ_TOKEN が見つかりません')
        return
        
    bot = LynQOutputBot()
    
    try:
        logger.info('🚀 LynQ送信ボット開始...')
        await bot.start(token)
    except Exception as e:
        logger.error(f'❌ LynQ Bot エラー: {e}')

if __name__ == '__main__':
    asyncio.run(main())