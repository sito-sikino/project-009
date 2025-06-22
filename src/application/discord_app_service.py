#!/usr/bin/env python3
"""
Discord Application Service - Clean Architecture Application Layer
Discordアプリケーションサービスによる高レベル業務処理
"""

import asyncio
import time
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# Clean Architecture imports
from ..config.settings import get_settings
from ..utils.logger import get_logger, log_performance, log_component_status
from ..container.system_container import SystemContainer

# Import performance monitoring (with fallback)
try:
    from ..utils.monitoring import performance_monitor
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    
# Import health monitoring (with fallback)
try:
    from ..utils.health import setup_health_monitoring
    HEALTH_AVAILABLE = True
except ImportError:
    HEALTH_AVAILABLE = False


class DiscordAppService:
    """
    Discord Application Service - Clean Architecture Application Layer
    
    責務:
    - システム全体のオーケストレーション
    - メッセージ処理フローの管理
    - Discord クライアント接続管理
    - 高レベル業務ロジックの実行
    """
    
    def __init__(self, container: SystemContainer):
        """アプリケーションサービス初期化"""
        self.container = container
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.running = False
        self.health_server = None
        self.connected_clients: List[Tuple[str, Any, Any]] = []
        
        # コンテナからコンポーネント取得
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """コンテナからコンポーネントを取得・初期化"""
        try:
            self.priority_queue = self.container.get('priority_queue')
            self.reception_client = self.container.get('reception_client')
            self.agent_supervisor = self.container.get('agent_supervisor')
            self.message_router = self.container.get('message_router')
            self.memory_system = self.container.get('memory_system')
            self.daily_workflow = self.container.get('daily_workflow')
            self.autonomous_speech = self.container.get('autonomous_speech')
            
            # Discord Bots
            self.spectra_bot = self.container.get('spectra_bot')
            self.lynq_bot = self.container.get('lynq_bot')
            self.paz_bot = self.container.get('paz_bot')
            
            log_component_status("discord_app_service", "ready", "All components initialized")
            self.logger.info("✅ Discord Application Service components initialized")
            
        except Exception as e:
            log_component_status("discord_app_service", "error", str(e))
            self.logger.error(f"❌ Failed to initialize components: {e}")
            raise
    
    async def start_application(self) -> None:
        """アプリケーション開始"""
        self.logger.info("🚀 Starting Discord Multi-Agent Application")
        self.logger.info("Architecture: 統合受信・個別送信型 (Clean Architecture)")
        
        try:
            # Phase 1: Memory System initialization
            await self._initialize_memory_system()
            
            # Phase 2: Health monitoring setup
            await self._setup_health_monitoring()
            
            # Phase 3: Workflow systems startup
            await self._start_workflow_systems()
            
            # Phase 4: Application main loop
            self.running = True
            await self._run_main_application_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Application startup failed: {e}")
            await self.stop_application()
            raise
    
    async def _initialize_memory_system(self) -> None:
        """メモリシステム初期化"""
        self.logger.info("🧠 Initializing Memory System connections...")
        
        try:
            memory_ready = await self.memory_system.initialize()
            if memory_ready:
                log_component_status("memory_system", "ready")
                self.logger.info("✅ Memory System initialized successfully")
            else:
                log_component_status("memory_system", "error", "initialization failed")
                self.logger.warning("⚠️ Memory System initialization failed - continuing without memory")
        except Exception as e:
            log_component_status("memory_system", "error", str(e))
            self.logger.warning(f"⚠️ Memory System initialization error: {e}")
    
    async def _setup_health_monitoring(self) -> None:
        """ヘルスモニタリング設定"""
        if not HEALTH_AVAILABLE:
            self.logger.info("ℹ️ Health monitoring not available - skipping")
            return
        
        try:
            health_port = self.settings.system.health_check_port
            discord_clients = [
                self.reception_client,
                self.spectra_bot,
                self.lynq_bot,
                self.paz_bot
            ]
            
            self.health_server = await setup_health_monitoring(
                self.memory_system,
                discord_clients,
                health_port
            )
            
            log_component_status("health_monitoring", "ready", f"port {health_port}")
            self.logger.info(f"✅ Health monitoring started on port {health_port}")
            
        except Exception as e:
            log_component_status("health_monitoring", "error", str(e))
            self.logger.warning(f"⚠️ Health monitoring setup failed: {e}")
    
    async def _start_workflow_systems(self) -> None:
        """ワークフローシステム開始"""
        try:
            # Daily Workflow System startup
            await self.daily_workflow.start()
            log_component_status("daily_workflow", "ready")
            self.logger.info("✅ Daily Workflow System started")
            
            # Autonomous Speech System startup
            await self.autonomous_speech.start()
            log_component_status("autonomous_speech", "ready")
            self.logger.info("✅ Autonomous Speech System started")
            
        except Exception as e:
            log_component_status("workflow_systems", "error", str(e))
            self.logger.error(f"❌ Workflow systems startup failed: {e}")
            raise
    
    async def _run_main_application_loop(self) -> None:
        """メインアプリケーションループ実行"""
        try:
            # 並行実行: Discord clients + Message processing
            await asyncio.gather(
                self._start_discord_clients(),
                self._message_processing_loop()
            )
        except KeyboardInterrupt:
            self.logger.info("📝 Received shutdown signal")
        except Exception as e:
            self.logger.error(f"❌ Application loop error: {e}")
            raise
    
    async def _start_discord_clients(self) -> None:
        """Discord クライアント順次接続"""
        self.logger.info("🔌 Starting Discord clients...")
        
        # Sequential connection approach to prevent event loop conflicts
        connection_order = [
            ("Reception Client", self.reception_client, self.settings.discord.reception_token),
            ("Spectra Bot", self.spectra_bot, self.settings.discord.spectra_token),
            ("LynQ Bot", self.lynq_bot, self.settings.discord.lynq_token),
            ("Paz Bot", self.paz_bot, self.settings.discord.paz_token)
        ]
        
        connected_clients = []
        
        for name, client, token in connection_order:
            try:
                self.logger.info(f"🔌 Connecting {name}...")
                
                # Create background task for client connection
                connection_task = asyncio.create_task(client.start(token))
                
                # Allow brief initialization time
                await asyncio.sleep(2)
                
                # Check connection progress
                if not connection_task.done():
                    self.logger.info(f"✅ {name} connection initiated successfully")
                    connected_clients.append((name, client, connection_task))
                else:
                    # Connection completed immediately or failed
                    try:
                        await connection_task
                        self.logger.info(f"✅ {name} connected successfully")
                        connected_clients.append((name, client, connection_task))
                    except Exception as e:
                        self.logger.error(f"❌ {name} connection failed: {e}")
                        
            except Exception as e:
                self.logger.error(f"❌ Failed to start {name}: {e}")
                continue
        
        self.connected_clients = connected_clients
        log_component_status("discord_clients", "ready", f"{len(connected_clients)}/4 clients")
        self.logger.info(f"🎉 Successfully initiated {len(connected_clients)}/4 Discord clients")
    
    async def _message_processing_loop(self) -> None:
        """メッセージ処理メインループ"""
        self.logger.info("💬 Starting message processing loop...")
        log_component_status("message_processing", "ready")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Priority Queue からメッセージ取得
                message_data = await self.priority_queue.dequeue()
                
                self.logger.info(f"📝 Processing message: {message_data['message'].content[:50]}...")
                
                # メッセージ処理中フラグ設定
                self.autonomous_speech.system_is_currently_speaking = True
                
                try:
                    # メッセージタイプ別処理
                    supervisor_result = await self._process_message_by_type(message_data)
                    
                    # Message Router でメッセージ配信
                    await self._route_message_with_monitoring(supervisor_result)
                    
                    # パフォーマンス記録
                    await self._record_message_performance(supervisor_result, start_time)
                    
                except Exception as processing_error:
                    self.logger.error(f"❌ Message processing error: {processing_error}")
                    await self._handle_message_processing_error(processing_error)
                
                finally:
                    # 処理完了フラグ解除
                    self.autonomous_speech.system_is_currently_speaking = False
                    
            except Exception as e:
                self.logger.error(f"❌ Error in message processing loop: {e}")
                await asyncio.sleep(1)  # エラー時の短い待機
    
    async def _process_message_by_type(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """メッセージタイプ別処理"""
        message = message_data['message']
        
        # Task command processing
        if not message.author.bot and message.content.startswith('/task '):
            return await self._process_task_command(message_data)
        
        # Autonomous speech processing
        if hasattr(message, 'autonomous_speech') and message.autonomous_speech:
            return await self._process_autonomous_speech(message_data)
        
        # Normal user message processing
        return await self._process_user_message(message_data)
    
    async def _process_task_command(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """タスクコマンド処理"""
        message = message_data['message']
        
        try:
            command_response = await self._execute_task_command(message)
            
            if command_response:
                supervisor_result = {
                    'selected_agent': 'spectra',
                    'response_content': command_response,
                    'channel_id': str(self.settings.discord.channel_ids.get('command_center', message.channel.id)),
                    'message_id': str(message.id),
                    'command_response': True
                }
                
                self.logger.info(f"✅ Task command processed: {message.content[:50]}...")
                return supervisor_result
            
        except Exception as e:
            self.logger.error(f"❌ Task command processing failed: {e}")
            raise
    
    async def _process_autonomous_speech(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """自発発言処理"""
        message = message_data['message']
        target_agent = message.target_agent
        
        supervisor_result = {
            'selected_agent': target_agent,
            'response_content': message.content,
            'channel_id': str(message.channel.id),
            'message_id': str(message.id),
            'autonomous_speech': True
        }
        
        self.logger.info(f"🎙️ 自発発言処理: {target_agent} -> #{message.channel.name}")
        return supervisor_result
    
    async def _process_user_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """通常ユーザーメッセージ処理"""
        message = message_data['message']
        
        initial_state = {
            'messages': [{'role': 'user', 'content': message.content}],
            'channel_id': str(message.channel.id),
            'user_id': str(message.author.id),
            'message_id': str(message.id)
        }
        
        # LangGraph Supervisor で処理
        if MONITORING_AVAILABLE:
            return await performance_monitor.record_operation(
                "message_processing",
                "supervisor",
                self.agent_supervisor.process_message,
                initial_state
            )
        else:
            return await self.agent_supervisor.process_message(initial_state)
    
    async def _route_message_with_monitoring(self, supervisor_result: Dict[str, Any]) -> None:
        """監視機能付きメッセージルーティング"""
        if MONITORING_AVAILABLE:
            await performance_monitor.record_operation(
                "message_routing",
                "router",
                self.message_router.route_message,
                supervisor_result
            )
        else:
            await self.message_router.route_message(supervisor_result)
    
    async def _record_message_performance(self, supervisor_result: Dict[str, Any], start_time: float) -> None:
        """メッセージ処理パフォーマンス記録"""
        total_time = time.time() - start_time
        
        if MONITORING_AVAILABLE:
            performance_monitor.metrics.record_discord_message(
                message_type="user_message",
                agent=supervisor_result.get('selected_agent', 'unknown'),
                response_time=total_time
            )
        
        log_performance(
            self.logger,
            f"message_processed_by_{supervisor_result.get('selected_agent', 'unknown')}",
            total_time
        )
        
        self.logger.info(
            f"✅ Message processed successfully by {supervisor_result['selected_agent']} "
            f"in {total_time:.3f}s"
        )
    
    async def _handle_message_processing_error(self, error: Exception) -> None:
        """メッセージ処理エラーハンドリング"""
        if MONITORING_AVAILABLE:
            performance_monitor.metrics.record_system_error(
                error_type=type(error).__name__,
                component="message_loop"
            )
        
        log_component_status("message_processing", "error", str(error))
    
    async def _execute_task_command(self, message) -> Optional[str]:
        """タスクコマンド実行 (Daily Workflow に委譲)"""
        try:
            content = message.content.strip()
            
            # Command parsing: /task commit [channel] "[task]" or /task change [channel] "[task]"
            import re
            pattern = r'/task\s+(commit|change)\s+([a-zA-Z_]+)\s+"([^"]+)"'
            match = re.match(pattern, content)
            
            if not match:
                return "❌ **コマンド形式エラー**\n\n正しい形式: `/task commit [channel] \"[task]\"` または `/task change [channel] \"[task]\"`"
            
            command, channel, task = match.groups()
            user_id = str(message.author.id)
            
            # Channel validation
            valid_channels = ['development', 'creation', 'command_center', 'lounge']
            if channel not in valid_channels:
                return f"❌ **無効なチャンネル**: {channel}\n\n有効なチャンネル: {', '.join(valid_channels)}"
            
            # Delegate to Daily Workflow System
            response = await self.daily_workflow.process_task_command(command, channel, task, user_id)
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Task command execution error: {e}")
            return f"❌ **タスクコマンド処理中にエラーが発生しました**: {str(e)}"
    
    async def stop_application(self) -> None:
        """アプリケーション停止"""
        self.logger.info("🛑 Stopping Discord Application Service...")
        log_component_status("discord_app_service", "stopping")
        
        self.running = False
        
        try:
            # Stop workflow systems
            await self._stop_workflow_systems()
            
            # Stop health monitoring
            await self._stop_health_monitoring()
            
            # Disconnect Discord clients
            await self._disconnect_discord_clients()
            
            log_component_status("discord_app_service", "ready", "shutdown complete")
            self.logger.info("✅ Discord Application Service stopped successfully")
            
        except Exception as e:
            log_component_status("discord_app_service", "error", str(e))
            self.logger.error(f"❌ Error during application shutdown: {e}")
    
    async def _stop_workflow_systems(self) -> None:
        """ワークフローシステム停止"""
        try:
            if hasattr(self, 'daily_workflow'):
                await self.daily_workflow.stop()
                log_component_status("daily_workflow", "stopping")
                self.logger.info("✅ Daily Workflow System stopped")
        except Exception as e:
            self.logger.error(f"❌ Error stopping Daily Workflow System: {e}")
        
        try:
            if hasattr(self, 'autonomous_speech'):
                await self.autonomous_speech.stop()
                log_component_status("autonomous_speech", "stopping")
                self.logger.info("✅ Autonomous Speech System stopped")
        except Exception as e:
            self.logger.error(f"❌ Error stopping Autonomous Speech System: {e}")
    
    async def _stop_health_monitoring(self) -> None:
        """ヘルスモニタリング停止"""
        if self.health_server:
            try:
                self.health_server.stop()
                log_component_status("health_monitoring", "stopping")
                self.logger.info("✅ Health monitoring server stopped")
            except Exception as e:
                self.logger.error(f"❌ Error stopping health server: {e}")
    
    async def _disconnect_discord_clients(self) -> None:
        """Discordクライアント切断"""
        for name, client, task in self.connected_clients:
            try:
                self.logger.info(f"🔌 Disconnecting {name}...")
                
                # Cancel connection task if still running
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
                # Close client if not already closed
                if not client.is_closed():
                    await client.close()
                
                self.logger.info(f"✅ {name} disconnected successfully")
                
            except Exception as e:
                self.logger.error(f"❌ Error disconnecting {name}: {e}")
        
        log_component_status("discord_clients", "stopping")
        self.connected_clients.clear()


# Factory function
def create_discord_app_service(container: SystemContainer) -> DiscordAppService:
    """Discord Application Service ファクトリー"""
    return DiscordAppService(container)