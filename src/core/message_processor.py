"""
Message Processing Layer - 優先度キューとメッセージ処理
PriorityQueue: 非同期優先度キューシステム
"""

import asyncio
import heapq
from typing import Dict, Any, Optional
from datetime import datetime


class PriorityQueue:
    """
    非同期優先度キューシステム
    
    責務:
    - メッセージの優先度付きキューイング
    - 優先度順での取り出し（低い値ほど高優先度）
    - 非同期操作のサポート
    """
    
    def __init__(self):
        """PriorityQueue初期化"""
        self._queue = []
        self._index = 0  # 同じ優先度でのFIFO順序保証用
        self._condition = asyncio.Condition()
        
    async def enqueue(self, message_data: Dict[str, Any]) -> None:
        """
        メッセージをキューに追加
        
        Args:
            message_data: メッセージデータ
                - priority: int (優先度レベル)
                - message: discord.Message
                - timestamp: datetime
        """
        async with self._condition:
            # heapq用のタプル: (priority, index, data)
            # indexで同じ優先度でのFIFO順序を保証
            item = (
                message_data['priority'],
                self._index,
                message_data
            )
            
            heapq.heappush(self._queue, item)
            self._index += 1
            
            # 待機中のdequeue()を通知
            self._condition.notify()
    
    async def dequeue(self) -> Dict[str, Any]:
        """
        最高優先度のメッセージを取り出し
        
        Returns:
            Dict[str, Any]: メッセージデータ
        """
        async with self._condition:
            # キューが空の場合は待機
            while not self._queue:
                await self._condition.wait()
            
            # 最高優先度のアイテムを取り出し
            priority, index, message_data = heapq.heappop(self._queue)
            return message_data
    
    def is_empty(self) -> bool:
        """
        キューが空かどうかチェック
        
        Returns:
            bool: 空の場合True
        """
        return len(self._queue) == 0
    
    def size(self) -> int:
        """
        キューサイズ取得
        
        Returns:
            int: キュー内のアイテム数
        """
        return len(self._queue)