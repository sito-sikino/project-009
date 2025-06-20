"""
Discord Memory System - Redis Hot Memory + PostgreSQL Cold Memory
統合受信・個別送信型アーキテクチャ対応メモリシステム
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import redis.asyncio as redis
import asyncpg
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dataclasses import dataclass


@dataclass
class MemoryItem:
    """メモリアイテム基本構造"""
    content: str
    timestamp: datetime
    channel_id: str
    user_id: str
    agent: str
    confidence: float
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'channel_id': self.channel_id,
            'user_id': self.user_id,
            'agent': self.agent,
            'confidence': self.confidence,
            'metadata': self.metadata or {}
        }


class DiscordMemorySystem:
    """
    Discord Memory System統合クラス
    
    アーキテクチャ:
    - Hot Memory (Redis): 当日会話履歴20メッセージ管理
    - Cold Memory (PostgreSQL + pgvector): 長期記憶・セマンティック検索
    
    LangGraph Supervisor統合インターフェース:
    - load_hot_memory(channel_id): 当日メモリ読み込み
    - load_cold_memory(query): セマンティック検索
    - update_memory(conversation_data): メモリ更新
    """
    
    def __init__(self, 
                 redis_url: str = None, 
                 postgres_url: str = None,
                 gemini_api_key: str = None):
        """
        Memory System初期化
        
        Args:
            redis_url: Redis接続URL
            postgres_url: PostgreSQL接続URL  
            gemini_api_key: Gemini API Key (text-embedding-004用)
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.postgres_url = postgres_url or os.getenv('POSTGRESQL_URL', 
            'postgresql://discord_agent:discord_agent_password@localhost:5432/discord_agent')
        
        # Google Generative AI Embeddings設定 (text-embedding-004使用)
        self.embeddings_client = GoogleGenerativeAIEmbeddings(
            model="text-embedding-004",
            google_api_key=gemini_api_key or os.getenv('GEMINI_API_KEY'),
            task_type="RETRIEVAL_DOCUMENT"  # 文書検索向け設定
        )
        
        # 接続オブジェクト
        self.redis = None
        self.postgres_pool = None
        
        # 設定
        self.hot_memory_limit = 20  # Redis保持メッセージ数
        self.hot_memory_ttl = 86400  # 1日TTL
        self.embedding_model = "text-embedding-004"  # 768次元 (Google)
        self.similarity_threshold = 0.7
        self.max_cold_results = 10
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Memory System初期化・接続確立"""
        try:
            # Redis接続
            self.redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_timeout=5.0
            )
            
            # Redis接続確認
            await self.redis.ping()
            self.logger.info("✅ Redis Hot Memory connected")
            
            # PostgreSQL接続プール
            self.postgres_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=2,
                max_size=10,
                command_timeout=30,
                server_settings={
                    'jit': 'off',
                    'application_name': 'discord_agent_memory'
                }
            )
            
            # PostgreSQL接続確認
            async with self.postgres_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            
            self.logger.info("✅ PostgreSQL Cold Memory connected")
            
            # pgvector拡張確認
            async with self.postgres_pool.acquire() as conn:
                extensions = await conn.fetch(
                    "SELECT extname FROM pg_extension WHERE extname = 'vector'"
                )
                if not extensions:
                    raise Exception("pgvector extension not found")
            
            self.logger.info("✅ pgvector extension verified")
            
            # Memory System初期化完了
            self.logger.info("🧠 Discord Memory System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Memory System initialization failed: {e}")
            return False
    
    async def load_hot_memory(self, channel_id: str) -> List[Dict[str, Any]]:
        """
        Hot Memory (Redis) 読み込み
        
        Args:
            channel_id: Discord チャンネルID
            
        Returns:
            List[Dict]: 当日会話履歴 (最大20件)
        """
        try:
            if not self.redis:
                await self.initialize()
            
            # Redis キー生成
            redis_key = f"channel:{channel_id}:messages"
            
            # 当日メッセージ取得 (最新20件)
            messages = await self.redis.lrange(redis_key, 0, self.hot_memory_limit - 1)
            
            # JSON デシリアライズ
            hot_memory = []
            for msg_json in messages:
                try:
                    msg_data = json.loads(msg_json)
                    hot_memory.append(msg_data)
                except json.JSONDecodeError:
                    continue
            
            self.logger.debug(f"Hot Memory loaded: {len(hot_memory)} messages from channel {channel_id}")
            return hot_memory
            
        except Exception as e:
            self.logger.error(f"Hot Memory load failed: {e}")
            return []
    
    async def load_cold_memory(self, query: str, channel_id: str = None) -> List[Dict[str, Any]]:
        """
        Cold Memory (PostgreSQL) セマンティック検索
        
        Args:
            query: 検索クエリテキスト
            channel_id: チャンネル指定 (オプション)
            
        Returns:
            List[Dict]: 関連する長期記憶
        """
        try:
            if not self.postgres_pool:
                await self.initialize()
            
            # クエリテキストのembedding生成
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                return []
            
            # セマンティック検索実行
            async with self.postgres_pool.acquire() as conn:
                if channel_id:
                    # チャンネル指定検索
                    results = await conn.fetch("""
                        SELECT * FROM find_similar_memories($1, $2, $3, $4)
                    """, query_embedding, self.similarity_threshold, self.max_cold_results, int(channel_id))
                else:
                    # 全体検索
                    results = await conn.fetch("""
                        SELECT * FROM find_similar_memories($1, $2, $3, NULL)
                    """, query_embedding, self.similarity_threshold, self.max_cold_results)
                
                # 結果を辞書形式に変換
                cold_memory = []
                for row in results:
                    cold_memory.append({
                        'memory_id': str(row['memory_id']),
                        'content': row['content'],
                        'similarity': float(row['similarity']),
                        'created_at': row['created_at'].isoformat(),
                        'selected_agent': row['selected_agent'],
                        'importance_score': float(row['importance_score'])
                    })
            
            self.logger.debug(f"Cold Memory loaded: {len(cold_memory)} memories for query: {query[:50]}...")
            return cold_memory
            
        except Exception as e:
            self.logger.error(f"Cold Memory load failed: {e}")
            return []
    
    async def update_memory(self, conversation_data: Dict[str, Any]) -> bool:
        """
        Memory更新 (Hot + Cold)
        
        Args:
            conversation_data: 会話データ
                - messages: List[Dict] (メッセージ履歴)
                - selected_agent: str (選択エージェント)
                - response_content: str (応答内容)
                - channel_id: str (チャンネルID)
                - confidence: float (信頼度)
        
        Returns:
            bool: 更新成功可否
        """
        try:
            # Hot Memory更新
            await self._update_hot_memory(conversation_data)
            
            # Cold Memory更新
            await self._update_cold_memory(conversation_data)
            
            self.logger.debug(f"Memory updated for channel: {conversation_data.get('channel_id')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Memory update failed: {e}")
            return False
    
    async def _update_hot_memory(self, conversation_data: Dict[str, Any]) -> None:
        """Hot Memory (Redis) 更新"""
        if not self.redis:
            return
        
        channel_id = conversation_data.get('channel_id')
        if not channel_id:
            return
        
        # 新しいメッセージエントリ作成
        memory_entry = {
            'timestamp': datetime.now().isoformat(),
            'messages': conversation_data.get('messages', []),
            'selected_agent': conversation_data.get('selected_agent'),
            'response_content': conversation_data.get('response_content'),
            'confidence': conversation_data.get('confidence', 0.5),
            'channel_id': channel_id
        }
        
        redis_key = f"channel:{channel_id}:messages"
        
        # リストの先頭に追加 (最新が先頭)
        await self.redis.lpush(redis_key, json.dumps(memory_entry))
        
        # リスト長制限 (20件まで)
        await self.redis.ltrim(redis_key, 0, self.hot_memory_limit - 1)
        
        # TTL設定 (1日)
        await self.redis.expire(redis_key, self.hot_memory_ttl)
    
    async def _update_cold_memory(self, conversation_data: Dict[str, Any]) -> None:
        """Cold Memory (PostgreSQL) 更新"""
        if not self.postgres_pool:
            return
        
        messages = conversation_data.get('messages', [])
        if not messages:
            return
        
        # 最新メッセージ取得
        latest_message = messages[-1] if messages else {}
        user_content = latest_message.get('content', '')
        
        if not user_content:
            return
        
        # Embedding生成
        content_embedding = await self.generate_embedding(user_content)
        response_embedding = await self.generate_embedding(
            conversation_data.get('response_content', '')
        )
        
        if not content_embedding or not response_embedding:
            return
        
        # PostgreSQL保存
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO memories (
                    guild_id, channel_id, user_id, message_id,
                    original_content, processed_content,
                    selected_agent, agent_response, confidence,
                    content_embedding, response_embedding,
                    conversation_context, importance_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
                0,  # guild_id (後で実装)
                int(conversation_data.get('channel_id', 0)),
                0,  # user_id (後で実装)  
                0,  # message_id (後で実装)
                user_content,
                user_content,  # processed_content
                conversation_data.get('selected_agent', 'unknown'),
                conversation_data.get('response_content', ''),
                conversation_data.get('confidence', 0.5),
                content_embedding,
                response_embedding,
                json.dumps(conversation_data),
                min(conversation_data.get('confidence', 0.5), 1.0)  # importance_score
            )
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        テキストのEmbedding生成 (Google text-embedding-004)
        
        Args:
            text: 入力テキスト
            
        Returns:
            List[float]: 768次元ベクトル
        """
        try:
            if not text.strip():
                return None
            
            # text-embedding-004のトークン制限 (2,048トークン)
            # 概算として文字数制限適用 (トークン数 ≈ 文字数/4)
            max_chars = 2048 * 4
            truncated_text = text[:max_chars] if len(text) > max_chars else text
            
            # Google Generative AI Embeddingsでembedding生成
            embedding = await asyncio.to_thread(
                self.embeddings_client.embed_query, 
                truncated_text
            )
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            return None
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Memory System統計情報取得"""
        stats = {
            'hot_memory': {'total_channels': 0, 'total_messages': 0},
            'cold_memory': {'total_memories': 0, 'total_summaries': 0},
            'status': 'disconnected'
        }
        
        try:
            # Redis統計
            if self.redis:
                keys = await self.redis.keys("channel:*:messages")
                stats['hot_memory']['total_channels'] = len(keys)
                
                total_messages = 0
                for key in keys:
                    length = await self.redis.llen(key)
                    total_messages += length
                stats['hot_memory']['total_messages'] = total_messages
            
            # PostgreSQL統計
            if self.postgres_pool:
                async with self.postgres_pool.acquire() as conn:
                    result = await conn.fetchval("SELECT COUNT(*) FROM memories")
                    stats['cold_memory']['total_memories'] = result
                    
                    result = await conn.fetchval("SELECT COUNT(*) FROM conversation_summaries")
                    stats['cold_memory']['total_summaries'] = result
            
            stats['status'] = 'connected'
            
        except Exception as e:
            self.logger.error(f"Stats collection failed: {e}")
            stats['error'] = str(e)
        
        return stats
    
    async def cleanup(self) -> None:
        """Memory System正常終了"""
        try:
            if self.redis:
                await self.redis.close()
                self.logger.info("Redis connection closed")
            
            if self.postgres_pool:
                await self.postgres_pool.close()
                self.logger.info("PostgreSQL pool closed")
                
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")


# Memory System Factory
def create_memory_system() -> DiscordMemorySystem:
    """
    Memory System インスタンス生成
    
    Returns:
        DiscordMemorySystem: 設定済みMemory System
    """
    return DiscordMemorySystem(
        redis_url=os.getenv('REDIS_URL'),
        postgres_url=os.getenv('POSTGRESQL_URL'),
        gemini_api_key=os.getenv('GEMINI_API_KEY')
    )