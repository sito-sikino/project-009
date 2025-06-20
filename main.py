#!/usr/bin/env python3
"""
Discord Multi-Agent System - Main Entry Point
統合受信・個別送信型アーキテクチャ メインアプリケーション
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List
import signal

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.discord_clients import ReceptionClient
from src.message_processor import PriorityQueue
from src.langgraph_supervisor import AgentSupervisor
from src.gemini_client import GeminiClient
from src.output_bots import SpectraBot, LynQBot, PazBot
from src.message_router import MessageRouter


class DiscordMultiAgentSystem:
    """
    Discord Multi-Agent System メインアプリケーション
    
    統合受信・個別送信型アーキテクチャの実装:
    - 1つのReception Client: 全メッセージ受信
    - LangGraph Supervisor: エージェント選択・応答生成
    - 3つのOutput Bots: 個別送信 (Spectra/LynQ/Paz)
    """
    
    def __init__(self):
        """システム初期化"""
        self.setup_logging()
        self.validate_environment()
        self.initialize_components()
        self.running = False
    
    def setup_logging(self):
        """ログシステム設定"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('discord_agent.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging initialized at {log_level} level")
    
    def validate_environment(self):
        """環境変数検証"""
        required_vars = [
            'DISCORD_RECEPTION_TOKEN',
            'DISCORD_SPECTRA_TOKEN',
            'DISCORD_LYNQ_TOKEN', 
            'DISCORD_PAZ_TOKEN',
            'GEMINI_API_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            self.logger.error(f"Missing required environment variables: {missing_vars}")
            raise EnvironmentError(f"Missing environment variables: {missing_vars}")
        
        self.logger.info("Environment validation passed")
    
    def initialize_components(self):
        """システムコンポーネント初期化"""
        self.logger.info("Initializing system components...")
        
        # Priority Queue
        self.priority_queue = PriorityQueue()
        self.logger.info("✅ Priority Queue initialized")
        
        # Reception Client
        self.reception_client = ReceptionClient(
            priority_queue=self.priority_queue
        )
        self.logger.info("✅ Reception Client initialized")
        
        # Gemini Client
        self.gemini_client = GeminiClient(
            api_key=os.getenv('GEMINI_API_KEY')
        )
        self.logger.info("✅ Gemini Client initialized")
        
        # LangGraph Supervisor
        self.supervisor = AgentSupervisor(
            gemini_client=self.gemini_client,
            memory_system=None  # TODO: Redis/PostgreSQL実装時に追加
        )
        self.logger.info("✅ LangGraph Supervisor initialized")
        
        # Output Bots
        self.spectra_bot = SpectraBot(token=os.getenv('DISCORD_SPECTRA_TOKEN'))
        self.lynq_bot = LynQBot(token=os.getenv('DISCORD_LYNQ_TOKEN'))
        self.paz_bot = PazBot(token=os.getenv('DISCORD_PAZ_TOKEN'))
        
        self.bots = {
            "spectra": self.spectra_bot,
            "lynq": self.lynq_bot,
            "paz": self.paz_bot
        }
        self.logger.info("✅ Output Bots initialized")
        
        # Message Router
        self.message_router = MessageRouter(bots=self.bots)
        self.logger.info("✅ Message Router initialized")
        
        self.logger.info("🚀 All components initialized successfully")
    
    async def message_processing_loop(self):
        """メッセージ処理メインループ"""
        self.logger.info("Starting message processing loop...")
        
        while self.running:
            try:
                # Priority Queueからメッセージ取得
                message_data = await self.priority_queue.dequeue()
                
                self.logger.info(f"Processing message: {message_data['message'].content[:50]}...")
                
                # LangGraph Supervisorで処理
                initial_state = {
                    'messages': [{'role': 'user', 'content': message_data['message'].content}],
                    'channel_id': str(message_data['message'].channel.id)
                }
                
                supervisor_result = await self.supervisor.process_message(initial_state)
                
                # Message Routerで配信
                await self.message_router.route_message(supervisor_result)
                
                self.logger.info(f"Message processed successfully by {supervisor_result['selected_agent']}")
                
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(1)  # エラー時の短い待機
    
    async def start_clients(self):
        """全Discordクライアント開始"""
        self.logger.info("Starting Discord clients...")
        
        # 全クライアントを並行実行
        clients = [
            self.reception_client.start(os.getenv('DISCORD_RECEPTION_TOKEN')),
            self.spectra_bot.start(os.getenv('DISCORD_SPECTRA_TOKEN')),
            self.lynq_bot.start(os.getenv('DISCORD_LYNQ_TOKEN')),
            self.paz_bot.start(os.getenv('DISCORD_PAZ_TOKEN'))
        ]
        
        await asyncio.gather(*clients)
    
    async def run(self):
        """システムメイン実行"""
        self.logger.info("🤖 Starting Discord Multi-Agent System")
        self.logger.info("Architecture: 統合受信・個別送信型")
        
        self.running = True
        
        try:
            # 並行実行: Discord clients + Message processing
            await asyncio.gather(
                self.start_clients(),
                self.message_processing_loop()
            )
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"System error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """システム正常終了"""
        self.logger.info("Shutting down Discord Multi-Agent System...")
        
        self.running = False
        
        # Discord clientsを正常終了
        clients = [
            self.reception_client,
            self.spectra_bot,
            self.lynq_bot,
            self.paz_bot
        ]
        
        for client in clients:
            try:
                await client.close()
            except Exception as e:
                self.logger.error(f"Error closing client: {e}")
        
        self.logger.info("✅ System shutdown completed")
    
    def setup_signal_handlers(self):
        """シグナルハンドラー設定"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """メイン実行関数"""
    try:
        system = DiscordMultiAgentSystem()
        system.setup_signal_handlers()
        await system.run()
    except Exception as e:
        logging.error(f"Failed to start system: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Python 3.7+ の asyncio.run() を使用
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Discord Multi-Agent System stopped")
        sys.exit(0)