"""
LangGraph Supervisor Pattern - 統合エージェント制御
StateGraphによるマルチエージェントワークフロー
"""

import asyncio
from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, add_messages
from langgraph.graph.graph import CompiledGraph

from ..infrastructure.gemini_client import GeminiClient


class AgentState(TypedDict):
    """
    LangGraph AgentState スキーマ
    
    StateGraphで管理される状態データ構造
    """
    messages: Annotated[List[Dict[str, Any]], add_messages]
    channel_id: str
    memory_context: Dict[str, Any]
    selected_agent: str
    response_content: str
    confidence: float


class AgentSupervisor:
    """
    LangGraph StateGraph統合Agent Supervisor
    
    責務:
    - StateGraphワークフロー管理
    - メモリシステム統合
    - エージェント選択・応答生成制御
    """
    
    def __init__(self, gemini_client: GeminiClient, memory_system=None):
        """
        Agent Supervisor初期化
        
        Args:
            gemini_client: Gemini API統合クライアント
            memory_system: メモリシステム（Hot/Cold Memory）
        """
        self.gemini_client = gemini_client
        self.memory_system = memory_system
        self.graph = self._build_graph()
    
    def _build_graph(self) -> CompiledGraph:
        """
        StateGraphワークフロー構築
        
        Returns:
            CompiledGraph: 実行可能なStateGraph
        """
        # StateGraph定義
        workflow = StateGraph(AgentState)
        
        # ノード追加
        workflow.add_node("load_memory", self._load_memory_node)
        workflow.add_node("unified_selection", self._unified_selection_node)
        workflow.add_node("update_memory", self._update_memory_node)
        
        # エッジ定義
        workflow.add_edge("load_memory", "unified_selection")
        workflow.add_edge("unified_selection", "update_memory")
        
        # エントリーポイント設定
        workflow.set_entry_point("load_memory")
        workflow.set_finish_point("update_memory")
        
        return workflow.compile()
    
    async def process_message(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        メッセージ処理メインフロー
        
        Args:
            initial_state: 初期状態（メッセージ・チャンネル情報等）
            
        Returns:
            Dict[str, Any]: 処理結果（エージェント選択・応答内容等）
        """
        # AgentState初期化
        state = AgentState(
            messages=initial_state.get('messages', []),
            channel_id=initial_state.get('channel_id', ''),
            memory_context={},
            selected_agent='',
            response_content='',
            confidence=0.0
        )
        
        # StateGraph実行
        result = await self.graph.ainvoke(state)
        
        return {
            'selected_agent': result['selected_agent'],
            'response_content': result['response_content'],
            'confidence': result['confidence'],
            'channel_id': result['channel_id']
        }
    
    async def _load_memory_node(self, state: AgentState) -> AgentState:
        """
        メモリ読み込みノード
        
        Args:
            state: 現在の状態
            
        Returns:
            AgentState: メモリ情報が追加された状態
        """
        if not self.memory_system:
            raise RuntimeError("Memory system is required but not available")
        
        # Hot Memory読み込み
        hot_memory = await self.memory_system.load_hot_memory(
            channel_id=state['channel_id']
        )
        
        # Cold Memory読み込み
        if state['messages']:
            last_msg = state['messages'][-1]
            if isinstance(last_msg, dict):
                latest_message = last_msg.get('content', '')
            else:
                latest_message = getattr(last_msg, 'content', str(last_msg))
            
            cold_memory = await self.memory_system.load_cold_memory(
                query=latest_message
            )
        else:
            cold_memory = []
        
        memory_context = {
            'hot_memory': hot_memory,
            'cold_memory': cold_memory
        }
        
        # 状態更新
        updated_state = state.copy()
        updated_state['memory_context'] = memory_context
        
        return updated_state
    
    async def _unified_selection_node(self, state: AgentState) -> AgentState:
        """統合エージェント選択ノード（責務分離: API処理委譲）"""
        if not self.gemini_client:
            raise RuntimeError("Gemini client is required but not available")
        
        latest_message = ""
        if state['messages']:
            last_msg = state['messages'][-1]
            if isinstance(last_msg, dict):
                latest_message = last_msg.get('content', '')
            else:
                latest_message = getattr(last_msg, 'content', str(last_msg))
        
        enriched_context = {
            'message': latest_message,
            'hot_memory': state['memory_context'].get('hot_memory', []),
            'cold_memory': state['memory_context'].get('cold_memory', []),
            'channel_id': state['channel_id']
        }
        
        result = await self.gemini_client.unified_agent_selection(enriched_context)
        
        updated_state = state.copy()
        updated_state['selected_agent'] = result['selected_agent']
        updated_state['response_content'] = result['response_content']
        updated_state['confidence'] = result['confidence']
        
        return updated_state
    
    async def _update_memory_node(self, state: AgentState) -> AgentState:
        """
        メモリ更新ノード
        
        Args:
            state: 現在の状態
            
        Returns:
            AgentState: メモリ更新後の状態
        """
        if self.memory_system:
            try:
                # 会話データ構築
                conversation_data = {
                    'messages': state['messages'],
                    'selected_agent': state['selected_agent'],
                    'response_content': state['response_content'],
                    'channel_id': state['channel_id'],
                    'confidence': state['confidence']
                }
                
                # メモリ更新
                await self.memory_system.update_memory_transactional(conversation_data)
                
            except Exception as e:
                # メモリ更新失敗は処理を継続
                print(f"Memory update failed: {e}")
        
        return state