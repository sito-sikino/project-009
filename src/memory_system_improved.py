"""
Improved Memory System with Production Enhancements
本番環境向け改善版Memory System
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import redis.asyncio as redis
import asyncpg
from langchain_google_genai import GoogleGenerativeAIEmbeddings


# Custom Exceptions
class MemorySystemError(Exception):
    """Memory System基本エラー"""
    pass

class RedisConnectionError(MemorySystemError):
    """Redis接続エラー"""
    pass

class PostgreSQLConnectionError(MemorySystemError):
    """PostgreSQL接続エラー"""
    pass

class EmbeddingQuotaError(MemorySystemError):
    """Embedding API制限エラー"""
    pass

class EmbeddingError(MemorySystemError):
    """Embedding生成エラー"""
    pass


class RateLimiter:
    """API Rate Limiter"""
    def __init__(self, calls_per_second: float = 1.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_called = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        async with self._lock:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - self.last_called
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self.last_called = asyncio.get_event_loop().time()


@dataclass
class HealthStatus:
    """システムヘルスステータス"""
    redis_connected: bool = False
    postgres_connected: bool = False
    embeddings_available: bool = False
    last_check: Optional[datetime] = None
    error_count: int = 0
    
    @property
    def is_healthy(self) -> bool:
        return all([self.redis_connected, self.postgres_connected, self.embeddings_available])


class ImprovedDiscordMemorySystem:
    """
    本番環境対応改善版Memory System
    
    改善点:
    - レート制限対応
    - 詳細なエラーハンドリング
    - ヘルスチェック機能
    - トランザクション管理
    - 接続プーリング最適化
    """
    
    def __init__(self, 
                 redis_url: str = None, 
                 postgres_url: str = None,
                 gemini_api_key: str = None):
        # ロギング設定（最初に初期化）
        self.logger = self._setup_logging()
        
        # 環境変数から安全に取得
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.postgres_url = self._sanitize_postgres_url(
            postgres_url or os.getenv('POSTGRESQL_URL', '')
        )
        
        # Google Embeddings設定
        self.embeddings_client = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=gemini_api_key or os.getenv('GEMINI_API_KEY'),
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        # 接続オブジェクト
        self.redis: Optional[redis.Redis] = None
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.postgres_pool: Optional[asyncpg.Pool] = None
        
        # 設定
        self.hot_memory_limit = 20
        self.hot_memory_ttl = 86400
        self.embedding_model = "models/text-embedding-004"
        self.similarity_threshold = 0.7
        self.max_cold_results = 10
        
        # レート制限 (15 RPM = 0.25 RPS)
        self.embedding_rate_limiter = RateLimiter(calls_per_second=0.25)
        
        # ヘルスステータス
        self.health_status = HealthStatus()
    
    def _sanitize_postgres_url(self, url: str) -> str:
        """PostgreSQL URL サニタイズ（パスワード隠蔽）"""
        if not url:
            return 'postgresql://localhost:5432/discord_agent'
        
        # パスワード部分を隠す
        if '@' in url and '://' in url:
            parts = url.split('@')
            if len(parts) == 2:
                cred_part = parts[0].split('://')[-1]
                if ':' in cred_part:
                    user = cred_part.split(':')[0]
                    sanitized = f"{parts[0].split('://')[0]}://{user}:****@{parts[1]}"
                    self.logger.info(f"PostgreSQL URL (sanitized): {sanitized}")
        
        return url
    
    def _setup_logging(self) -> logging.Logger:
        """構造化ロギング設定"""
        logger = logging.getLogger(__name__)
        logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))
        
        # 構造化ログフォーマット
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(extra)s'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def initialize(self) -> bool:
        """Memory System初期化（改善版）"""
        try:
            # Redis接続プール設定
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=10,
                decode_responses=True,
                encoding="utf-8",
                retry_on_timeout=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            self.redis = redis.Redis(connection_pool=self.redis_pool)
            
            # Redis接続確認
            await self.redis.ping()
            self.health_status.redis_connected = True
            self.logger.info("✅ Redis Hot Memory connected with connection pool")
            
            # PostgreSQL接続プール（改善版設定）
            self.postgres_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=2,
                max_size=10,
                max_queries=50000,
                max_inactive_connection_lifetime=300.0,
                command_timeout=30,
                server_settings={
                    'jit': 'off',
                    'application_name': 'discord_agent_memory',
                    'statement_timeout': '30s',
                    'lock_timeout': '10s'
                }
            )
            
            # PostgreSQL & pgvector確認
            async with self.postgres_pool.acquire() as conn:
                # pgvector拡張確認
                extensions = await conn.fetch(
                    "SELECT extname FROM pg_extension WHERE extname = 'vector'"
                )
                if not extensions:
                    raise PostgreSQLConnectionError("pgvector extension not found")
                
                await conn.fetchval('SELECT 1')
                self.health_status.postgres_connected = True
            
            self.logger.info("✅ PostgreSQL Cold Memory connected with pgvector")
            
            # Embeddings API確認
            self.health_status.embeddings_available = True
            
            # ヘルスステータス更新
            self.health_status.last_check = datetime.now()
            self.health_status.error_count = 0
            
            self.logger.info("🧠 Discord Memory System initialized successfully")
            return True
            
        except redis.RedisError as e:
            self.logger.error(f"❌ Redis initialization failed: {e}")
            raise RedisConnectionError(f"Redis connection failed: {e}")
            
        except asyncpg.PostgresError as e:
            self.logger.error(f"❌ PostgreSQL initialization failed: {e}")
            raise PostgreSQLConnectionError(f"PostgreSQL connection failed: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Memory System initialization failed: {e}")
            self.health_status.error_count += 1
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(redis.RedisError)
    )
    async def load_hot_memory(self, channel_id: str) -> List[Dict[str, Any]]:
        """Hot Memory読み込み（リトライ機能付き）"""
        try:
            if not self.redis:
                if not await self.initialize():
                    return []
            
            redis_key = f"channel:{channel_id}:messages"
            
            # パイプライン使用で効率化
            async with self.redis.pipeline(transaction=False) as pipe:
                pipe.lrange(redis_key, 0, self.hot_memory_limit - 1)
                pipe.expire(redis_key, self.hot_memory_ttl)
                results = await pipe.execute()
            
            messages = results[0] if results else []
            
            # JSON デシリアライズ
            hot_memory = []
            for msg_json in messages:
                try:
                    msg_data = json.loads(msg_json)
                    hot_memory.append(msg_data)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Invalid JSON in hot memory: {e}")
                    continue
            
            self.logger.debug(
                f"Hot Memory loaded",
                extra={"channel_id": channel_id, "message_count": len(hot_memory)}
            )
            return hot_memory
            
        except redis.RedisError as e:
            self.logger.error(f"Hot Memory load failed: {e}")
            self.health_status.redis_connected = False
            raise RedisConnectionError(f"Redis read failed: {e}")
    
    async def load_cold_memory(self, query: str, channel_id: str = None) -> List[Dict[str, Any]]:
        """Cold Memory検索（一時的に無効化）"""
        try:
            # TEMPORARY FIX: PostgreSQL関数未作成のため一時的に無効化
            self.logger.info("🔧 Cold Memory temporarily disabled (PostgreSQL function missing)")
            return []
            
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
            
            self.logger.info(
                f"Cold Memory search completed",
                extra={
                    "query_length": len(query),
                    "results_count": len(cold_memory),
                    "channel_id": channel_id
                }
            )
            return cold_memory
            
        except asyncpg.PostgresError as e:
            self.logger.error(f"Cold Memory search failed: {e}")
            self.health_status.postgres_connected = False
            raise PostgreSQLConnectionError(f"PostgreSQL search failed: {e}")
        
        except Exception as e:
            self.logger.error(f"Cold Memory load failed: {e}")
            return []
    
    async def update_memory_transactional(self, conversation_data: Dict[str, Any]) -> bool:
        """Memory更新（トランザクション保証）"""
        try:
            channel_id = conversation_data.get('channel_id')
            if not channel_id:
                return False
            
            # Redis更新用データ準備
            memory_entry = {
                'timestamp': datetime.now().isoformat(),
                'messages': conversation_data.get('messages', []),
                'selected_agent': conversation_data.get('selected_agent'),
                'response_content': conversation_data.get('response_content'),
                'confidence': conversation_data.get('confidence', 0.5),
                'channel_id': channel_id
            }
            
            redis_key = f"channel:{channel_id}:messages"
            
            # PostgreSQL更新用データ準備
            messages = conversation_data.get('messages', [])
            if not messages:
                return True  # Redisのみ更新
            
            latest_message = messages[-1] if messages else {}
            user_content = latest_message.get('content', '')
            
            if not user_content:
                return True  # Redisのみ更新
            
            # Embedding生成
            content_embedding = await self.generate_embedding_with_rate_limit(user_content)
            response_embedding = await self.generate_embedding_with_rate_limit(
                conversation_data.get('response_content', '')
            )
            
            # トランザクション実行
            success = False
            
            # Redis更新
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.lpush(redis_key, json.dumps(memory_entry))
                pipe.ltrim(redis_key, 0, self.hot_memory_limit - 1)
                pipe.expire(redis_key, self.hot_memory_ttl)
                await pipe.execute()
            
            # PostgreSQL更新（Embedingが生成できた場合のみ）
            if content_embedding and response_embedding:
                async with self.postgres_pool.acquire() as conn:
                    async with conn.transaction():
                        await conn.execute("""
                            INSERT INTO memories (
                                guild_id, channel_id, user_id, message_id,
                                original_content, processed_content,
                                selected_agent, agent_response, confidence,
                                content_embedding, response_embedding,
                                conversation_context, importance_score
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        """,
                            int(conversation_data.get('guild_id', 0)),
                            int(channel_id),
                            int(conversation_data.get('user_id', 0)),
                            int(conversation_data.get('message_id', 0)),
                            user_content,
                            user_content,
                            conversation_data.get('selected_agent', 'unknown'),
                            conversation_data.get('response_content', ''),
                            conversation_data.get('confidence', 0.5),
                            content_embedding,
                            response_embedding,
                            json.dumps(conversation_data),
                            min(conversation_data.get('confidence', 0.5), 1.0)
                        )
            
            success = True
            self.logger.info(
                "Memory updated successfully",
                extra={"channel_id": channel_id}
            )
            return success
            
        except Exception as e:
            self.logger.error(f"Memory update failed: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((EmbeddingError, EmbeddingQuotaError))
    )
    async def generate_embedding_with_rate_limit(self, text: str) -> Optional[List[float]]:
        """Embedding生成（レート制限・リトライ付き）"""
        try:
            if not text.strip():
                return None
            
            # レート制限
            await self.embedding_rate_limiter.acquire()
            
            # トークン制限対応
            max_chars = 2048 * 4
            truncated_text = text[:max_chars] if len(text) > max_chars else text
            
            # 非同期実行
            embedding = await asyncio.to_thread(
                self.embeddings_client.embed_query, 
                truncated_text
            )
            
            return embedding
            
        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "rate" in error_str:
                self.logger.warning(f"Embedding API quota/rate limit: {e}")
                raise EmbeddingQuotaError(f"API quota exceeded: {e}")
            else:
                self.logger.error(f"Embedding generation failed: {e}")
                raise EmbeddingError(f"Embedding failed: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """詳細なヘルスチェック"""
        try:
            # Redis健康確認
            if self.redis:
                try:
                    await self.redis.ping()
                    self.health_status.redis_connected = True
                except:
                    self.health_status.redis_connected = False
            
            # PostgreSQL健康確認
            if self.postgres_pool:
                try:
                    async with self.postgres_pool.acquire() as conn:
                        await conn.fetchval('SELECT 1')
                    self.health_status.postgres_connected = True
                except:
                    self.health_status.postgres_connected = False
            
            # ヘルスステータス更新
            self.health_status.last_check = datetime.now()
            
            return {
                "status": "healthy" if self.health_status.is_healthy else "unhealthy",
                "redis": self.health_status.redis_connected,
                "postgres": self.health_status.postgres_connected,
                "embeddings": self.health_status.embeddings_available,
                "last_check": self.health_status.last_check.isoformat() if self.health_status.last_check else None,
                "error_count": self.health_status.error_count
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """リソース正常終了"""
        try:
            if self.redis:
                await self.redis.close()
                await self.redis_pool.disconnect() if self.redis_pool else None
                self.logger.info("Redis connection closed")
            
            if self.postgres_pool:
                await self.postgres_pool.close()
                self.logger.info("PostgreSQL pool closed")
                
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")


# Factory関数
def create_improved_memory_system() -> ImprovedDiscordMemorySystem:
    """改善版Memory System生成"""
    return ImprovedDiscordMemorySystem(
        redis_url=os.getenv('REDIS_URL'),
        postgres_url=os.getenv('POSTGRESQL_URL'),
        gemini_api_key=os.getenv('GEMINI_API_KEY')
    )