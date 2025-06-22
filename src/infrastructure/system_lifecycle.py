#!/usr/bin/env python3
"""
System Lifecycle Manager - Clean Architecture Infrastructure Layer  
システムライフサイクル管理とリソース制御
"""

import signal
import asyncio
import sys
from typing import Optional, Callable, Any
from datetime import datetime

# Clean Architecture imports
from ..config.settings import get_settings
from ..utils.logger import get_logger, log_component_status, log_system_shutdown
from ..application.discord_app_service import DiscordAppService
from ..container.system_container import SystemContainer


class SystemLifecycle:
    """
    System Lifecycle Manager - Clean Architecture Infrastructure Layer
    
    責務:
    - システム全体のライフサイクル管理
    - 優雅なシャットダウン処理
    - シグナルハンドリング (SIGINT, SIGTERM)
    - リソースクリーンアップの順序制御
    - エラー復旧とロールバック
    """
    
    def __init__(self, app_service: DiscordAppService, logger: Optional[Any] = None):
        """System Lifecycle Manager 初期化"""
        self.app_service = app_service
        self.container = app_service.container
        self.settings = get_settings()
        self.logger = logger or get_logger(__name__)
        
        # Lifecycle state
        self.is_running = False
        self.shutdown_requested = False
        self.shutdown_complete = False
        
        # Signal handling
        self.original_sigint_handler = None
        self.original_sigterm_handler = None
        self.signal_handlers_setup = False
        
        log_component_status("system_lifecycle", "ready")
        self.logger.info("🔄 System Lifecycle Manager initialized")
    
    def setup_signal_handlers(self) -> None:
        """システムシグナルハンドラー設定"""
        if self.signal_handlers_setup:
            return
        
        try:
            # Save original handlers for cleanup
            self.original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)
            self.original_sigterm_handler = signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.signal_handlers_setup = True
            log_component_status("signal_handlers", "ready")
            self.logger.info("📡 Signal handlers configured (SIGINT, SIGTERM)")
            
        except Exception as e:
            log_component_status("signal_handlers", "error", str(e))
            self.logger.error(f"❌ Failed to setup signal handlers: {e}")
            raise
    
    def _signal_handler(self, signum: int, frame) -> None:
        """シグナル受信時のハンドラー"""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"📡 Received signal {signal_name} ({signum})")
        
        if not self.shutdown_requested:
            self.shutdown_requested = True
            log_component_status("system_lifecycle", "stopping", f"signal {signal_name}")
            
            # Request graceful shutdown
            self._request_graceful_shutdown()
        else:
            self.logger.warning(f"⚠️ Multiple shutdown signals received, forcing exit...")
            sys.exit(1)
    
    def _request_graceful_shutdown(self) -> None:
        """優雅なシャットダウン要求"""
        try:
            # Stop application service (non-blocking)
            if hasattr(self.app_service, 'running'):
                self.app_service.running = False
            
            # Stop workflow systems immediately
            self._stop_workflow_systems_immediately()
            
            self.logger.info("🛑 Graceful shutdown requested")
            
        except Exception as e:
            self.logger.error(f"❌ Error requesting graceful shutdown: {e}")
    
    def _stop_workflow_systems_immediately(self) -> None:
        """ワークフローシステムの即座停止"""
        try:
            # Set stop flags for workflow systems
            daily_workflow = self.container.get('daily_workflow')
            if hasattr(daily_workflow, 'is_running'):
                daily_workflow.is_running = False
                
            autonomous_speech = self.container.get('autonomous_speech')
            if hasattr(autonomous_speech, 'is_running'):
                autonomous_speech.is_running = False
                
            self.logger.debug("🔄 Workflow system stop flags set")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping workflow systems immediately: {e}")
    
    async def run(self) -> None:
        """システム全体の実行・監視"""
        self.logger.info("🚀 Starting system lifecycle management")
        
        startup_time = datetime.now()
        
        try:
            # Phase 1: System startup
            await self._startup_phase()
            
            # Phase 2: Runtime monitoring  
            await self._runtime_phase()
            
        except KeyboardInterrupt:
            self.logger.info("⌨️ Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"❌ System runtime error: {e}")
            log_component_status("system_lifecycle", "error", str(e))
        finally:
            # Phase 3: Graceful shutdown
            await self._shutdown_phase()
            
            # Calculate uptime
            uptime = datetime.now() - startup_time
            self.logger.info(f"📊 System uptime: {uptime}")
    
    async def _startup_phase(self) -> None:
        """システム起動フェーズ"""
        self.logger.info("🔄 Entering startup phase...")
        log_component_status("system_lifecycle", "starting")
        
        try:
            # Start application service
            await self.app_service.start_application()
            
            self.is_running = True
            log_component_status("system_lifecycle", "ready", "startup complete")
            self.logger.info("✅ System startup phase completed")
            
        except Exception as e:
            log_component_status("system_lifecycle", "error", str(e))
            self.logger.error(f"❌ Startup phase failed: {e}")
            raise
    
    async def _runtime_phase(self) -> None:
        """システム実行時フェーズ"""
        self.logger.info("▶️ Entering runtime phase...")
        
        # Runtime monitoring loop
        while self.is_running and not self.shutdown_requested:
            try:
                # Health check interval
                await asyncio.sleep(1)
                
                # Check application service status
                if not self.app_service.running:
                    self.logger.info("📝 Application service stopped, initiating shutdown...")
                    break
                    
            except asyncio.CancelledError:
                self.logger.info("📝 Runtime monitoring cancelled")
                break
            except Exception as e:
                self.logger.error(f"❌ Runtime monitoring error: {e}")
                await asyncio.sleep(5)  # Brief delay before retry
        
        self.logger.info("⏹️ Runtime phase completed")
    
    async def _shutdown_phase(self) -> None:
        """システムシャットダウンフェーズ"""
        if self.shutdown_complete:
            return
            
        self.logger.info("🛑 Entering shutdown phase...")
        log_component_status("system_lifecycle", "stopping")
        log_system_shutdown()
        
        try:
            # Step 1: Stop application service
            await self._shutdown_application_service()
            
            # Step 2: Cleanup system container
            await self._cleanup_system_container()
            
            # Step 3: Restore signal handlers
            self._restore_signal_handlers()
            
            self.shutdown_complete = True
            log_component_status("system_lifecycle", "ready", "shutdown complete")
            self.logger.info("✅ System shutdown phase completed")
            
        except Exception as e:
            log_component_status("system_lifecycle", "error", str(e))
            self.logger.error(f"❌ Shutdown phase error: {e}")
    
    async def _shutdown_application_service(self) -> None:
        """アプリケーションサービス停止"""
        try:
            self.logger.info("🛑 Stopping application service...")
            await self.app_service.stop_application()
            log_component_status("discord_app_service", "ready", "stopped")
            self.logger.info("✅ Application service stopped successfully")
            
        except Exception as e:
            log_component_status("discord_app_service", "error", str(e))
            self.logger.error(f"❌ Error stopping application service: {e}")
    
    async def _cleanup_system_container(self) -> None:
        """システムコンテナクリーンアップ"""
        try:
            self.logger.info("🧹 Cleaning up system container...")
            await self.container.cleanup()
            log_component_status("system_container", "ready", "cleanup complete")
            self.logger.info("✅ System container cleanup completed")
            
        except Exception as e:
            log_component_status("system_container", "error", str(e))
            self.logger.error(f"❌ Error cleaning up system container: {e}")
    
    def _restore_signal_handlers(self) -> None:
        """シグナルハンドラー復元"""
        if not self.signal_handlers_setup:
            return
            
        try:
            # Restore original signal handlers
            if self.original_sigint_handler:
                signal.signal(signal.SIGINT, self.original_sigint_handler)
            if self.original_sigterm_handler:
                signal.signal(signal.SIGTERM, self.original_sigterm_handler)
            
            self.signal_handlers_setup = False
            log_component_status("signal_handlers", "ready", "restored")
            self.logger.info("📡 Signal handlers restored")
            
        except Exception as e:
            log_component_status("signal_handlers", "error", str(e))
            self.logger.error(f"❌ Error restoring signal handlers: {e}")
    
    async def force_shutdown(self, timeout: float = 10.0) -> None:
        """強制シャットダウン (タイムアウト付き)"""
        self.logger.warning(f"⚠️ Force shutdown requested (timeout: {timeout}s)")
        
        self.shutdown_requested = True
        self.is_running = False
        
        try:
            # Wait for graceful shutdown with timeout
            await asyncio.wait_for(self._shutdown_phase(), timeout=timeout)
            
        except asyncio.TimeoutError:
            self.logger.error(f"❌ Graceful shutdown timeout after {timeout}s, forcing exit")
            log_component_status("system_lifecycle", "error", "force shutdown timeout")
            
            # Force exit
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"❌ Force shutdown error: {e}")
            sys.exit(1)
    
    def get_status(self) -> dict:
        """システムライフサイクル状態取得"""
        return {
            'is_running': self.is_running,
            'shutdown_requested': self.shutdown_requested,
            'shutdown_complete': self.shutdown_complete,
            'signal_handlers_setup': self.signal_handlers_setup,
            'app_service_running': getattr(self.app_service, 'running', False),
            'container_initialized': getattr(self.container, '_is_initialized', False)
        }


class SystemLifecycleError(Exception):
    """System Lifecycle 関連エラー"""
    pass


# Factory function
def create_system_lifecycle(app_service: DiscordAppService, logger: Optional[Any] = None) -> SystemLifecycle:
    """System Lifecycle Manager ファクトリー"""
    return SystemLifecycle(app_service, logger)


# Graceful shutdown helper
async def graceful_shutdown_with_timeout(lifecycle: SystemLifecycle, timeout: float = 30.0) -> None:
    """タイムアウト付き優雅なシャットダウン"""
    try:
        await asyncio.wait_for(lifecycle._shutdown_phase(), timeout=timeout)
    except asyncio.TimeoutError:
        logger = get_logger(__name__)
        logger.error(f"❌ Graceful shutdown timeout after {timeout}s")
        await lifecycle.force_shutdown(timeout=5.0)