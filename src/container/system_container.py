#!/usr/bin/env python3
"""
System Container - Clean Architecture DI Container
依存注入コンテナによるシステムコンポーネント管理
"""

from typing import Dict, Any, Optional, Callable, TypeVar, Type
from dataclasses import dataclass
import asyncio

# Clean Architecture imports
from ..config.settings import get_settings, AppSettings
from ..utils.logger import get_logger, log_component_status

# Core layer imports (immediate)
from ..core.message_processor import PriorityQueue

# Lazy imports (loaded when needed) - to avoid Discord dependency at startup
# from ..core.daily_workflow import DailyWorkflowSystem
# from ..agents.supervisor import AgentSupervisor  
# from ..agents.autonomous_speech import AutonomousSpeechSystem
# from ..bots.reception import ReceptionClient
# from ..bots.output_bots import SpectraBot, LynQBot, PazBot
# from ..infrastructure.gemini_client import GeminiClient
# from ..infrastructure.message_router import MessageRouter
# from ..infrastructure.memory_system import create_improved_memory_system

T = TypeVar('T')


@dataclass
class ComponentDefinition:
    """コンポーネント定義"""
    factory: Callable[[], Any]
    dependencies: list[str]
    singleton: bool = True
    initialized: bool = False
    instance: Optional[Any] = None


class SystemContainer:
    """
    System Container - Clean Architecture DI Container
    
    責務:
    - システムコンポーネントのライフサイクル管理
    - 依存関係の解決と注入
    - シングルトンパターンの実装
    - 初期化順序の管理
    """
    
    def __init__(self):
        """コンテナ初期化"""
        self.logger = get_logger(__name__)
        self.settings: Optional[AppSettings] = None
        self._components: Dict[str, ComponentDefinition] = {}
        self._instances: Dict[str, Any] = {}
        self._initialization_order: list[str] = []
        self._is_initialized = False
        
        # コンポーネント定義を登録
        self._register_component_definitions()
    
    def _register_component_definitions(self) -> None:
        """コンポーネント定義の登録"""
        
        # Settings (no dependencies - already initialized)
        self._components['settings'] = ComponentDefinition(
            factory=self._create_settings,
            dependencies=[],
            singleton=True
        )
        
        # Priority Queue (no dependencies)
        self._components['priority_queue'] = ComponentDefinition(
            factory=self._create_priority_queue,
            dependencies=[],
            singleton=True
        )
        
        # Gemini Client (depends on settings)
        self._components['gemini_client'] = ComponentDefinition(
            factory=self._create_gemini_client,
            dependencies=['settings'],
            singleton=True
        )
        
        # Memory System (no direct dependencies)
        self._components['memory_system'] = ComponentDefinition(
            factory=self._create_memory_system,
            dependencies=[],
            singleton=True
        )
        
        # Reception Client (depends on priority_queue)
        self._components['reception_client'] = ComponentDefinition(
            factory=self._create_reception_client,
            dependencies=['priority_queue'],
            singleton=True
        )
        
        # Agent Supervisor (depends on gemini_client, memory_system)
        self._components['agent_supervisor'] = ComponentDefinition(
            factory=self._create_agent_supervisor,
            dependencies=['gemini_client', 'memory_system'],
            singleton=True
        )
        
        # Output Bots (depend on settings)
        self._components['spectra_bot'] = ComponentDefinition(
            factory=self._create_spectra_bot,
            dependencies=['settings'],
            singleton=True
        )
        
        self._components['lynq_bot'] = ComponentDefinition(
            factory=self._create_lynq_bot,
            dependencies=['settings'],
            singleton=True
        )
        
        self._components['paz_bot'] = ComponentDefinition(
            factory=self._create_paz_bot,
            dependencies=['settings'],
            singleton=True
        )
        
        # Message Router (depends on output bots)
        self._components['message_router'] = ComponentDefinition(
            factory=self._create_message_router,
            dependencies=['spectra_bot', 'lynq_bot', 'paz_bot'],
            singleton=True
        )
        
        # v0.3.0 Long-term Memory Processor (depends on settings, memory_system)
        self._components['long_term_memory_processor'] = ComponentDefinition(
            factory=self._create_long_term_memory_processor,
            dependencies=['settings', 'memory_system'],
            singleton=True
        )
        
        # v0.3.0 Daily Report Generator (no dependencies)
        self._components['daily_report_generator'] = ComponentDefinition(
            factory=self._create_daily_report_generator,
            dependencies=[],
            singleton=True
        )
        
        # v0.3.0 Integrated Message System (depends on output bots)
        self._components['integrated_message_system'] = ComponentDefinition(
            factory=self._create_integrated_message_system,
            dependencies=['spectra_bot', 'lynq_bot', 'paz_bot'],
            singleton=True
        )
        
        # v0.3.0 Event-driven Workflow Orchestrator (depends on v0.3.0 components + settings)
        self._components['event_driven_workflow_orchestrator'] = ComponentDefinition(
            factory=self._create_event_driven_workflow_orchestrator,
            dependencies=['long_term_memory_processor', 'daily_report_generator', 'integrated_message_system', 'settings'],
            singleton=True
        )

        # Daily Workflow System (depends on settings, memory_system, priority_queue, long_term_memory_processor)
        self._components['daily_workflow'] = ComponentDefinition(
            factory=self._create_daily_workflow,
            dependencies=['settings', 'memory_system', 'priority_queue', 'long_term_memory_processor', 'event_driven_workflow_orchestrator'],
            singleton=True
        )
        
        # Autonomous Speech System (depends on settings, daily_workflow, priority_queue, gemini_client)
        self._components['autonomous_speech'] = ComponentDefinition(
            factory=self._create_autonomous_speech,
            dependencies=['settings', 'daily_workflow', 'priority_queue', 'gemini_client'],
            singleton=True
        )
    
    async def initialize(self) -> None:
        """コンテナとすべてのコンポーネントの初期化"""
        if self._is_initialized:
            return
        
        self.logger.info("🔧 Initializing System Container...")
        log_component_status("system_container", "starting")
        
        try:
            # 依存関係の順序解決
            self._resolve_initialization_order()
            
            # コンポーネントの順次初期化
            for component_name in self._initialization_order:
                await self._initialize_component(component_name)
            
            self._is_initialized = True
            log_component_status("system_container", "ready", f"{len(self._instances)} components")
            self.logger.info(f"✅ System Container initialized with {len(self._instances)} components")
            
        except Exception as e:
            log_component_status("system_container", "error", str(e))
            self.logger.error(f"❌ System Container initialization failed: {e}")
            raise
    
    def _resolve_initialization_order(self) -> None:
        """依存関係に基づく初期化順序の解決 (トポロジカルソート)"""
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(component_name: str):
            if component_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {component_name}")
            
            if component_name not in visited:
                temp_visited.add(component_name)
                
                # 依存関係を先に訪問
                component_def = self._components[component_name]
                for dependency in component_def.dependencies:
                    visit(dependency)
                
                temp_visited.remove(component_name)
                visited.add(component_name)
                order.append(component_name)
        
        # すべてのコンポーネントを訪問
        for component_name in self._components:
            if component_name not in visited:
                visit(component_name)
        
        self._initialization_order = order
        self.logger.info(f"🔄 Component initialization order: {' → '.join(order)}")
    
    async def _initialize_component(self, component_name: str) -> Any:
        """個別コンポーネントの初期化"""
        if component_name in self._instances:
            return self._instances[component_name]
        
        component_def = self._components[component_name]
        
        if component_def.initialized:
            return component_def.instance
        
        try:
            self.logger.debug(f"🔧 Initializing component: {component_name}")
            
            # 依存関係の解決
            dependencies = {}
            for dep_name in component_def.dependencies:
                dependencies[dep_name] = await self._initialize_component(dep_name)
            
            # ファクトリー実行 (依存関係を渡す)
            instance = component_def.factory(dependencies)
            
            # インスタンス保存
            if component_def.singleton:
                component_def.instance = instance
                component_def.initialized = True
                self._instances[component_name] = instance
            
            log_component_status(component_name, "ready")
            self.logger.info(f"✅ {component_name} initialized")
            
            return instance
            
        except Exception:
            log_component_status(component_name, "error", "Initialization failed")
            raise
    
    def get(self, component_name: str) -> Any:
        """コンポーネントインスタンスの取得"""
        if not self._is_initialized:
            raise RuntimeError("Container not initialized. Call initialize() first.")
        
        if component_name not in self._instances:
            raise ValueError(f"Component '{component_name}' not found in container")
        
        return self._instances[component_name]
    
    def get_typed(self, component_type: Type[T]) -> T:
        """型指定コンポーネント取得"""
        # Type-based lookup (for convenience)
        type_mappings = {
            PriorityQueue: 'priority_queue',
            ReceptionClient: 'reception_client',
            GeminiClient: 'gemini_client',
            AgentSupervisor: 'agent_supervisor',
            MessageRouter: 'message_router',
            DailyWorkflowSystem: 'daily_workflow',
            AutonomousSpeechSystem: 'autonomous_speech'
        }
        
        component_name = type_mappings.get(component_type)
        if not component_name:
            raise ValueError(f"No component mapping found for type {component_type}")
        
        return self.get(component_name)
    
    # ========================================
    # Component Factory Methods
    # ========================================
    
    def _create_settings(self, dependencies: Dict[str, Any] = None) -> AppSettings:
        """設定オブジェクトの作成"""
        if self.settings is None:
            self.settings = get_settings()
        return self.settings
    
    def _create_priority_queue(self, dependencies: Dict[str, Any] = None) -> PriorityQueue:
        """優先度キューの作成"""
        return PriorityQueue()
    
    def _create_gemini_client(self, dependencies: Dict[str, Any] = None):
        """Geminiクライアントの作成"""
        from ..infrastructure.gemini_client import GeminiClient
        settings = dependencies['settings']
        return GeminiClient(api_key=settings.ai.gemini_api_key)
    
    def _create_memory_system(self, dependencies: Dict[str, Any] = None):
        """メモリシステムの作成"""
        from ..infrastructure.memory_system import create_improved_memory_system
        return create_improved_memory_system()
    
    def _create_reception_client(self, dependencies: Dict[str, Any] = None):
        """受信クライアントの作成"""
        from ..bots.reception import ReceptionClient
        priority_queue = dependencies['priority_queue']
        return ReceptionClient(priority_queue=priority_queue)
    
    def _create_agent_supervisor(self, dependencies: Dict[str, Any] = None):
        """エージェントスーパーバイザーの作成"""
        from ..agents.supervisor import AgentSupervisor
        gemini_client = dependencies['gemini_client']
        memory_system = dependencies['memory_system']
        return AgentSupervisor(
            gemini_client=gemini_client,
            memory_system=memory_system
        )
    
    def _create_spectra_bot(self, dependencies: Dict[str, Any] = None):
        """Spectraボットの作成"""
        from ..bots.output_bots import SpectraBot
        settings = dependencies['settings']
        return SpectraBot(token=settings.discord.spectra_token)
    
    def _create_lynq_bot(self, dependencies: Dict[str, Any] = None):
        """LynQボットの作成"""
        from ..bots.output_bots import LynQBot
        settings = dependencies['settings']
        return LynQBot(token=settings.discord.lynq_token)
    
    def _create_paz_bot(self, dependencies: Dict[str, Any] = None):
        """Pazボットの作成"""
        from ..bots.output_bots import PazBot
        settings = dependencies['settings']
        return PazBot(token=settings.discord.paz_token)
    
    def _create_message_router(self, dependencies: Dict[str, Any] = None):
        """メッセージルーターの作成"""
        from ..infrastructure.message_router import MessageRouter
        bots = {
            "spectra": dependencies['spectra_bot'],
            "lynq": dependencies['lynq_bot'],
            "paz": dependencies['paz_bot']
        }
        return MessageRouter(bots=bots)
    
    def _create_daily_workflow(self, dependencies: Dict[str, Any] = None):
        """デイリーワークフローシステムの作成"""
        from ..core.daily_workflow import DailyWorkflowSystem
        settings = dependencies['settings']
        memory_system = dependencies['memory_system']
        priority_queue = dependencies['priority_queue']
        long_term_memory_processor = dependencies['long_term_memory_processor']
        event_driven_workflow_orchestrator = dependencies['event_driven_workflow_orchestrator']
        
        return DailyWorkflowSystem(
            channel_ids=settings.discord.channel_ids,
            memory_system=memory_system,
            priority_queue=priority_queue,
            long_term_memory_processor=long_term_memory_processor,
            event_driven_workflow_orchestrator=event_driven_workflow_orchestrator
        )
    
    def _create_autonomous_speech(self, dependencies: Dict[str, Any] = None):
        """自発発言システムの作成"""
        from ..agents.autonomous_speech import AutonomousSpeechSystem
        settings = dependencies['settings']
        daily_workflow = dependencies['daily_workflow']
        priority_queue = dependencies['priority_queue']
        gemini_client = dependencies['gemini_client']
        
        return AutonomousSpeechSystem(
            channel_ids=settings.discord.channel_ids,
            environment=settings.system.environment.value,
            workflow_system=daily_workflow,
            priority_queue=priority_queue,
            gemini_client=gemini_client,
            system_settings=settings.system
        )
    
    def _create_long_term_memory_processor(self, dependencies: Dict[str, Any] = None):
        """v0.3.0 長期記憶処理システムの作成"""
        from ..infrastructure.long_term_memory import LongTermMemoryProcessor
        settings = dependencies['settings']
        memory_system = dependencies['memory_system']
        
        return LongTermMemoryProcessor(
            redis_url=settings.database.redis_url,
            postgres_url=settings.database.postgresql_url,
            gemini_api_key=settings.ai.gemini_api_key
        )
    
    def _create_daily_report_generator(self, dependencies: Dict[str, Any] = None):
        """v0.3.0 日報生成システムの作成"""
        from ..core.daily_report_system import DailyReportGenerator
        
        return DailyReportGenerator()
    
    def _create_integrated_message_system(self, dependencies: Dict[str, Any] = None):
        """v0.3.0 統合メッセージシステムの作成"""
        from ..core.daily_report_system import IntegratedMessageSystem
        
        output_bots = {
            "spectra": dependencies['spectra_bot'],
            "lynq": dependencies['lynq_bot'],
            "paz": dependencies['paz_bot']
        }
        
        return IntegratedMessageSystem(output_bots=output_bots)
    
    def _create_event_driven_workflow_orchestrator(self, dependencies: Dict[str, Any] = None):
        """v0.3.0 イベントドリブンワークフロー統括システムの作成"""
        from ..core.daily_report_system import EventDrivenWorkflowOrchestrator
        settings = dependencies['settings']
        
        return EventDrivenWorkflowOrchestrator(
            long_term_memory_processor=dependencies['long_term_memory_processor'],
            daily_report_generator=dependencies['daily_report_generator'],
            integrated_message_system=dependencies['integrated_message_system'],
            command_center_channel_id=settings.discord.channel_ids.get('command_center', 0)
        )
    
    async def cleanup(self) -> None:
        """リソースクリーンアップ"""
        self.logger.info("🧹 Cleaning up System Container...")
        
        # 逆順でクリーンアップ
        cleanup_order = list(reversed(self._initialization_order))
        
        for component_name in cleanup_order:
            try:
                instance = self._instances.get(component_name)
                if instance and hasattr(instance, 'cleanup'):
                    if asyncio.iscoroutinefunction(instance.cleanup):
                        await instance.cleanup()
                    else:
                        instance.cleanup()
                    self.logger.debug(f"🧹 Cleaned up {component_name}")
            except Exception as e:
                self.logger.error(f"❌ Error cleaning up {component_name}: {e}")
        
        self._instances.clear()
        self._is_initialized = False
        log_component_status("system_container", "stopping")
        self.logger.info("✅ System Container cleanup completed")
    
    def get_component_status(self) -> Dict[str, bool]:
        """コンポーネント状態の取得"""
        return {
            component_name: component_name in self._instances
            for component_name in self._components
        }


# ファクトリー関数
def create_system_container() -> SystemContainer:
    """システムコンテナファクトリー"""
    return SystemContainer()