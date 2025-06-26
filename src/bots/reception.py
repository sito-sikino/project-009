"""
Discord Client Layer - 統合受信・個別送信型アーキテクチャ
Reception Client: 全メッセージ受信・優先度判定・キューイング
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import discord

# Discord.py設計制限によるPyNaCl警告無効化（必要な制御コード）
discord.VoiceClient.warn_nacl = False


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
        # FIXED: Maximum intents for debugging - ensure all events are received
        intents = discord.Intents.all()  # Enable ALL intents for comprehensive event reception
        # Critical intents for message reception:
        # intents.message_content = True  # Already included in .all()
        # intents.guild_messages = True   # Already included in .all()
        # intents.guilds = True          # Already included in .all()
        
        super().__init__(intents=intents, **kwargs)
        self.priority_queue = priority_queue
        self.message_count = 0
        self.connection_status = "disconnected"
        
        # CRITICAL FIX: Add ready event for synchronization
        self.ready_event = asyncio.Event()
        
    async def on_connect(self):
        """Gateway connection established"""
        self.connection_status = "connected"
        print(f"🔗 GATEWAY CONNECTION ESTABLISHED")
        print(f"🔗 Connection status: {self.connection_status}")
        
    async def on_disconnect(self):
        """Gateway connection lost"""
        self.connection_status = "disconnected"
        print(f"🔌 GATEWAY CONNECTION LOST")
        print(f"🔌 Connection status: {self.connection_status}")
        
    async def on_ready(self):
        """Bot is ready and online"""
        self.connection_status = "ready"
        print(f"✅ RECEPTION CLIENT READY!")
        print(f"✅ Bot: {self.user} (ID: {self.user.id})")
        print(f"✅ Connection status: {self.connection_status}")
        print(f"✅ Intents value: {self.intents.value}")
        print(f"✅ Connected to {len(self.guilds)} guilds:")
        for guild in self.guilds:
            print(f"   🏰 {guild.name} (ID: {guild.id}, Members: {guild.member_count})")
            # Check channel permissions
            for channel in guild.text_channels[:3]:  # Show first 3 channels
                perms = channel.permissions_for(guild.me)
                print(f"      📺 #{channel.name}: read={perms.read_messages}, send={perms.send_messages}")
        print(f"🎯 Monitoring for messages...")
        
        # CRITICAL FIX: Signal that client is ready for message processing
        self.ready_event.set()
        
    async def on_resumed(self):
        """Connection resumed"""
        print(f"🔄 GATEWAY CONNECTION RESUMED")
        
    async def on_error(self, event, *args, **kwargs):
        """Handle errors"""
        print(f"🚨 ERROR in event '{event}': {args}")
        import traceback
        traceback.print_exc()
        
    async def on_message(self, message: discord.Message) -> None:
        """
        メッセージ受信イベントハンドラ - ENHANCED WITH DEBUGGING
        
        フロー:
        1. Bot自身のメッセージは無視
        2. 優先度判定（メンション検出）
        3. 優先度キューに追加
        
        Args:
            message: 受信したDiscordメッセージ
        """
        self.message_count += 1
        
        # CRITICAL DEBUG: Always log message reception
        print(f"📨 MESSAGE #{self.message_count} RECEIVED!")
        print(f"   📺 Channel: #{message.channel.name} ({message.channel.id})")
        print(f"   👤 Author: {message.author} (Bot: {message.author.bot})")
        print(f"   💬 Content: '{message.content[:100]}{'...' if len(message.content) > 100 else ''}'")
        print(f"   🏰 Guild: {message.guild.name if message.guild else 'DM'}")
        print(f"   🔢 Message ID: {message.id}")
        
        # Bot自身のメッセージは処理しない
        if message.author.bot:
            print(f"   ⚠️  Ignoring bot message")
            return
        
        print(f"   ✅ Processing user message...")
            
        # 優先度判定
        priority = self._determine_priority(message)
        print(f"   🎯 Priority: {priority}")
        
        # メッセージデータ構築
        message_data = {
            'message': message,
            'priority': priority,
            'timestamp': datetime.now()
        }
        
        try:
            # 優先度キューに追加
            await self.priority_queue.enqueue(message_data)
            print(f"   ✅ Message added to priority queue successfully")
        except Exception as e:
            print(f"   ❌ Failed to add message to queue: {e}")
            import traceback
            traceback.print_exc()
    
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