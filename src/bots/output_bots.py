"""
Output Bots - 個別送信Discord Bot実装
統合受信・個別送信型アーキテクチャの送信部分
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class OutputBot(discord.Client):
    """
    Output Bot基本クラス
    
    責務:
    - Discord個別Bot基本機能
    - メッセージ送信インターフェース
    - パーソナリティ管理
    """
    
    def __init__(self, token: str, bot_name: str, personality: str, **kwargs):
        """
        OutputBot初期化
        
        Args:
            token: Discord Bot Token
            bot_name: Bot識別名
            personality: Botパーソナリティ説明
        """
        # Discord Intents設定（送信専用なので最小限）
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(intents=intents, **kwargs)
        
        self.token = token
        self.bot_name = bot_name
        self.personality = personality
        
        # CRITICAL FIX: Add ready event for synchronization
        self.ready_event = asyncio.Event()
    
    async def send_message(self, message_data: Dict[str, Any]) -> None:
        """
        Discord チャンネルへメッセージ送信
        
        Args:
            message_data: 送信データ
                - content: str (送信内容)
                - channel_id: str (送信先チャンネルID)
                - original_user: str (元の発言者)
                - confidence: float (信頼度)
        """
        try:
            channel_id = int(message_data['channel_id'])
            channel = self.get_channel(channel_id)
            
            if channel:
                content = message_data['content']
                await channel.send(content)
            else:
                logger.error(f"Channel {channel_id} not found for {self.bot_name}")
                
        except Exception as e:
            logger.error(f"Failed to send message via {self.bot_name}: {e}")
    
    async def on_ready(self):
        """Bot準備完了イベント"""
        logger.info(f'{self.bot_name.upper()} Bot ({self.user}) is ready!')
        logger.info(f'Personality: {self.personality}')
        
        # CRITICAL FIX: Signal that client is ready
        self.ready_event.set()


class SpectraBot(OutputBot):
    """
    Spectra Bot - メタ進行役
    
    特性:
    - 議論の構造化
    - 全体方針整理
    - 一般対話
    - メタ進行役
    """
    
    def __init__(self, token: str, **kwargs):
        """Spectra Bot初期化"""
        personality = (
            "メタ進行役・議論の構造化・全体方針整理・一般対話を担当。"
            "会話の流れを整理し、参加者の意見を構造化して議論を前進させる。"
        )
        
        super().__init__(
            token=token,
            bot_name="spectra",
            personality=personality,
            **kwargs
        )


class LynQBot(OutputBot):
    """
    LynQ Bot - 論理収束役
    
    特性:
    - 技術的検証
    - 構造化分析
    - 問題解決
    - 論理収束役
    """
    
    def __init__(self, token: str, **kwargs):
        """LynQ Bot初期化"""
        personality = (
            "論理収束役・技術的検証・構造化分析・問題解決を担当。"
            "論理的思考で問題を分析し、技術的観点から解決策を提示する。"
        )
        
        super().__init__(
            token=token,
            bot_name="lynq",
            personality=personality,
            **kwargs
        )


class PazBot(OutputBot):
    """
    Paz Bot - 発散創造役
    
    特性:
    - 革新的アイデア
    - 創造的テーマ
    - ブレインストーミング
    - 発散創造役
    """
    
    def __init__(self, token: str, **kwargs):
        """Paz Bot初期化"""
        personality = (
            "発散創造役・革新的アイデア・創造的テーマ・ブレインストーミングを担当。"
            "既存の枠を超えた創造的なアイデアと新しい視点を提供する。"
        )
        
        super().__init__(
            token=token,
            bot_name="paz",
            personality=personality,
            **kwargs
        )