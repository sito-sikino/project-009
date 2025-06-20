"""
Message Router - エージェント別メッセージルーティング
LangGraph Supervisor → 個別Output Bot配信システム
"""

import asyncio
from typing import Dict, Any, List, Optional
from .output_bots import OutputBot


class MessageRouter:
    """
    Message Router - エージェント別ルーティング
    
    責務:
    - LangGraph出力の解析
    - 適切なOutput Botへの配信
    - フォールバック処理
    - 並行メッセージ配信管理
    """
    
    def __init__(self, bots: Dict[str, OutputBot]):
        """
        MessageRouter初期化
        
        Args:
            bots: エージェント名をキーとするOutput Botディクショナリ
                  例: {"spectra": SpectraBot, "lynq": LynQBot, "paz": PazBot}
        """
        self.bots = bots
        self.valid_agents = set(bots.keys())
        self.fallback_agent = "spectra"  # デフォルトフォールバック
    
    async def route_message(self, message_data: Dict[str, Any]) -> None:
        """
        メッセージルーティング・配信
        
        Args:
            message_data: LangGraphからの出力データ
                - selected_agent: str (選択エージェント)
                - response_content: str (応答内容)
                - channel_id: str (送信先チャンネル)
                - confidence: float (信頼度)
                - original_user: str (元発言者、オプション)
        """
        selected_agent = message_data.get('selected_agent', self.fallback_agent)
        
        # エージェント有効性チェック
        if not self.is_bot_available(selected_agent):
            print(f"Warning: Agent '{selected_agent}' not available, falling back to {self.fallback_agent}")
            selected_agent = self.fallback_agent
        
        # 対象Bot取得
        target_bot = self.bots[selected_agent]
        
        # メッセージデータ準備
        routing_data = {
            'content': message_data.get('response_content', ''),
            'channel_id': message_data.get('channel_id', ''),
            'original_user': message_data.get('original_user', ''),
            'confidence': message_data.get('confidence', 0.5),
            'selected_agent': selected_agent
        }
        
        try:
            # Bot経由でメッセージ送信
            await target_bot.send_message(routing_data)
            
            print(f"✅ Routed message to {selected_agent.upper()}: {routing_data['content'][:50]}...")
            
        except Exception as e:
            print(f"❌ Failed to route message to {selected_agent}: {e}")
            
            # フォールバック処理
            if selected_agent != self.fallback_agent:
                print(f"Retrying with fallback agent: {self.fallback_agent}")
                routing_data['selected_agent'] = self.fallback_agent
                await self.bots[self.fallback_agent].send_message(routing_data)
    
    def is_bot_available(self, agent_name: str) -> bool:
        """
        Bot可用性チェック
        
        Args:
            agent_name: エージェント名
            
        Returns:
            bool: 利用可能かどうか
        """
        return agent_name in self.valid_agents
    
    def list_available_bots(self) -> List[str]:
        """
        利用可能Bot一覧取得
        
        Returns:
            List[str]: 利用可能エージェント名リスト
        """
        return list(self.valid_agents)
    
    async def broadcast_message(self, message_data: Dict[str, Any], target_agents: List[str]) -> None:
        """
        複数エージェントへの同時配信
        
        Args:
            message_data: 配信データ
            target_agents: 配信対象エージェントリスト
        """
        tasks = []
        
        for agent in target_agents:
            if self.is_bot_available(agent):
                # 各エージェント用にデータ複製
                agent_data = message_data.copy()
                agent_data['selected_agent'] = agent
                
                # 非同期タスク作成
                task = self.route_message(agent_data)
                tasks.append(task)
            else:
                print(f"Warning: Skipping unavailable agent: {agent}")
        
        # 並行実行
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_bot_stats(self) -> Dict[str, Any]:
        """
        Bot統計情報取得
        
        Returns:
            Dict[str, Any]: Bot統計データ
        """
        return {
            'total_bots': len(self.bots),
            'available_agents': list(self.valid_agents),
            'fallback_agent': self.fallback_agent,
            'bot_personalities': {
                name: bot.personality for name, bot in self.bots.items()
            }
        }