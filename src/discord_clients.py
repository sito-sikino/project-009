"""
Discord Client Layer - 統合受信・個別送信型アーキテクチャ
Reception Client: 全メッセージ受信・優先度判定・キューイング
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import discord


class ReceptionClient(discord.Client):
    """
    統合受信専用Discordクライアント
    
    責務:
    - 全メッセージの一元受信
    - 優先度判定（メンション > 通常）
    - 優先度キューへの追加
    """
    
    def __init__(self, priority_queue, **kwargs):
        """
        Reception Client初期化
        
        Args:
            priority_queue: メッセージ優先度キューインスタンス
            **kwargs: discord.Client追加パラメータ
        """
        # 受信に必要な最小限のIntents設定
        intents = discord.Intents.all()
        
        super().__init__(intents=intents, **kwargs)
        self.priority_queue = priority_queue
        
    async def on_message(self, message: discord.Message) -> None:
        """
        メッセージ受信イベントハンドラ
        
        フロー:
        1. Bot自身のメッセージは無視
        2. 優先度判定（メンション検出）
        3. 優先度キューに追加
        
        Args:
            message: 受信したDiscordメッセージ
        """
        # Bot自身のメッセージは処理しない
        if message.author.bot:
            return
            
        # 優先度判定
        priority = self._determine_priority(message)
        
        # メッセージデータ構築
        message_data = {
            'message': message,
            'priority': priority,
            'timestamp': datetime.now()
        }
        
        # 優先度キューに追加
        await self.priority_queue.enqueue(message_data)
    
    def _determine_priority(self, message: discord.Message) -> int:
        """
        メッセージ優先度判定
        
        優先度ルール:
        - 1: 高優先度（メンション付き）
        - 2: 標準優先度（通常メッセージ）
        
        Args:
            message: 判定対象メッセージ
            
        Returns:
            int: 優先度レベル（低い値ほど高優先度）
        """
        # メンション検出
        if message.mentions:
            return 1  # 高優先度（メンション）
        else:
            return 2  # 標準優先度（通常）