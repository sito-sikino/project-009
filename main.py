#!/usr/bin/env python3
"""
Discord Multi-Agent System - Main Entry Point
統合受信・個別送信型アーキテクチャ メインアプリケーション
"""

import os
import sys
import asyncio
import logging
import time
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
from src.memory_system_improved import ImprovedDiscordMemorySystem, create_improved_memory_system
from src.monitoring import performance_monitor, monitor_performance
from src.health_api import setup_health_monitoring


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
        self.health_server = None
    
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
        
        # Memory System (Improved Version with Production Features)
        self.memory_system = create_improved_memory_system()
        self.logger.info("✅ Improved Memory System created with production features")
        
        # LangGraph Supervisor (Memory System統合)
        self.supervisor = AgentSupervisor(
            gemini_client=self.gemini_client,
            memory_system=self.memory_system
        )
        self.logger.info("✅ LangGraph Supervisor with Memory System initialized")
        
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
        """メッセージ処理メインループ（監視機能付き）"""
        self.logger.info("Starting message processing loop with performance monitoring...")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Priority Queueからメッセージ取得
                message_data = await self.priority_queue.dequeue()
                
                self.logger.info(f"Processing message: {message_data['message'].content[:50]}...")
                
                # LangGraph Supervisorで処理（監視付き）
                initial_state = {
                    'messages': [{'role': 'user', 'content': message_data['message'].content}],
                    'channel_id': str(message_data['message'].channel.id),
                    'user_id': str(message_data['message'].author.id),
                    'message_id': str(message_data['message'].id)
                }
                
                supervisor_result = await performance_monitor.record_operation(
                    "message_processing", 
                    "supervisor",
                    self.supervisor.process_message,
                    initial_state
                )
                
                # Message Routerで配信（監視付き）
                await performance_monitor.record_operation(
                    "message_routing",
                    "router", 
                    self.message_router.route_message,
                    supervisor_result
                )
                
                # パフォーマンスメトリクス記録
                total_time = time.time() - start_time
                performance_monitor.metrics.record_discord_message(
                    message_type="user_message",
                    agent=supervisor_result.get('selected_agent', 'unknown'),
                    response_time=total_time
                )
                
                self.logger.info(
                    f"Message processed successfully by {supervisor_result['selected_agent']} "
                    f"in {total_time:.3f}s"
                )
                
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
                performance_monitor.metrics.record_system_error(
                    error_type=type(e).__name__,
                    component="message_loop"
                )
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
        
        # Memory System接続確立
        self.logger.info("Initializing Memory System connections...")
        memory_ready = await self.memory_system.initialize()
        if not memory_ready:
            self.logger.warning("⚠️ Memory System initialization failed - continuing without memory")
        
        # ヘルスチェック・監視システム初期化
        try:
            health_port = int(os.getenv('HEALTH_CHECK_PORT', '8000'))
            discord_clients = [self.reception_client, self.spectra_bot, self.lynq_bot, self.paz_bot]
            
            self.health_server = await setup_health_monitoring(
                self.memory_system,
                discord_clients,
                health_port
            )
            self.logger.info(f"✅ Health monitoring started on port {health_port}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Health monitoring setup failed: {e}")
        
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
        
        # ヘルスチェックサーバー停止
        if self.health_server:
            try:
                self.health_server.stop()
                self.logger.info("✅ Health monitoring server stopped")
            except Exception as e:
                self.logger.error(f"Error stopping health server: {e}")
        
        # Memory System正常終了
        try:
            await self.memory_system.cleanup()
            self.logger.info("✅ Memory System closed")
        except Exception as e:
            self.logger.error(f"Error closing Memory System: {e}")
        
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