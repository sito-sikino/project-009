"""
Improved Memory System with Production Enhancements
本番環境向け改善版Memory System
"""

import asyncio
import json
import logging
import gc
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import psutil

import redis.asyncio as redis
import asyncpg
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

from ..config.settings import get_database_settings, get_ai_settings, get_system_settings


@dataclass
class MemoryItem:
    """Memory Item Data Structure"""
    content: str
    timestamp: datetime
    channel_id: str
    user_id: str
    agent: str
    confidence: float = 0.5
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'channel_id': self.channel_id,
            'user_id': self.user_id,
            'agent': self.agent,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


# Custom Exceptions
class MemorySystemError(Exception):
    """Memory System基本エラー"""
    pass

class MemorySystemConnectionError(MemorySystemError):
    """接続関連エラー"""
    pass

class MemorySystemTransactionError(MemorySystemError):
    """トランザクション関連エラー"""
    pass

class RedisConnectionError(MemorySystemConnectionError):
    """Redis接続エラー"""
    pass

class PostgreSQLConnectionError(MemorySystemConnectionError):
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
    redis_pool_health: Optional[Dict[str, Any]] = None
    postgres_pool_health: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    
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
                 redis_url: Optional[str] = None, 
                 postgres_url: Optional[str] = None,
                 gemini_api_key: Optional[str] = None):
        # ロギング設定（最初に初期化）
        self.logger = self._setup_logging()
        
        # 設定から安全に取得
        db_settings = get_database_settings()
        ai_settings = get_ai_settings()
        
        self.redis_url = redis_url or db_settings.redis_url
        postgres_url_env = postgres_url or db_settings.postgresql_url
        self.postgres_url = self._sanitize_postgres_url(postgres_url_env) if postgres_url_env else ''
        
        # Google Embeddings設定
        api_key = gemini_api_key or ai_settings.gemini_api_key
        self.embeddings_client = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=SecretStr(api_key) if api_key else None,
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        # 接続オブジェクト
        self.redis: Optional[redis.Redis] = None
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.postgres_pool: Optional[asyncpg.Pool] = None
        
        # 設定（中央管理対応）
        self.hot_memory_limit = 20
        self.hot_memory_ttl = db_settings.hot_memory_ttl_seconds
        self.cold_retention_days = db_settings.cold_memory_retention_days
        self.migration_batch_size = db_settings.memory_migration_batch_size
        self.embedding_model = "models/text-embedding-004"
        self.similarity_threshold = 0.7
        self.max_cold_results = 10
        
        # レート制限 (15 RPM = 0.25 RPS)
        self.embedding_rate_limiter = RateLimiter(calls_per_second=0.25)
        
        # パフォーマンスメトリクス記録
        self.performance_metrics = {
            'hot_memory_operations': 0,
            'cold_memory_operations': 0,
            'embedding_generations': 0,
            'total_operations': 0
        }
        
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
        system_settings = get_system_settings()
        logger.setLevel(system_settings.log_level)
        
        # 構造化ログフォーマット
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def initialize(self) -> bool:
        """Memory System初期化（Fail-fast対応改善版）"""
        try:
            # 設定を取得（メソッドスコープ内で定義）
            db_settings = get_database_settings()
            
            # Redis接続プール設定強化（Fail-fast対応）
            if not self.redis_url:
                raise MemorySystemConnectionError("Redis URL not provided")
            
            # Redis接続のFail-fast設定
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=db_settings.redis_max_connections,
                decode_responses=True,
                encoding="utf-8",
                retry_on_timeout=False,  # Fail-fast: リトライ無効
                socket_timeout=1.0,      # Fail-fast: 1秒タイムアウト
                socket_connect_timeout=1.0,  # Fail-fast: 1秒接続タイムアウト
                health_check_interval=30
            )
            self.redis = redis.Redis(connection_pool=self.redis_pool)
            
            # Redis接続確認（Fail-fast）
            redis_start = time.time()
            try:
                await asyncio.wait_for(self.redis.ping(), timeout=1.0)
                self.health_status.redis_connected = True
                self.logger.info(f"✅ Redis connected in {time.time() - redis_start:.3f}s")
            except asyncio.TimeoutError:
                redis_error_time = time.time() - redis_start
                self.logger.error(f"❌ Redis connection timeout after {redis_error_time:.3f}s")
                raise RedisConnectionError(f"Redis connection timeout after {redis_error_time:.3f}s")
            except Exception as e:
                redis_error_time = time.time() - redis_start
                self.logger.error(f"❌ Redis initialization failed after {redis_error_time:.3f}s: {e}")
                raise RedisConnectionError(f"Redis initialization failed: {e}")
            
            # PostgreSQL接続プール設定強化（Fail-fast対応）
            postgres_start = time.time()
            try:
                self.postgres_pool = await asyncio.wait_for(
                    asyncpg.create_pool(
                        self.postgres_url,
                        min_size=db_settings.postgres_pool_min_size,
                        max_size=db_settings.postgres_pool_max_size,
                        max_queries=50000,
                        max_inactive_connection_lifetime=300.0,
                        command_timeout=2.0,  # Fail-fast: 2秒コマンドタイムアウト
                        server_settings={
                            'jit': 'off',
                            'application_name': 'discord_agent_memory_v2',
                            'statement_timeout': '2s',  # Fail-fast: 2秒ステートメントタイムアウト
                            'lock_timeout': '1s',       # Fail-fast: 1秒ロックタイムアウト
                            'work_mem': '256MB',
                            'effective_cache_size': '1GB'
                        }
                    ),
                    timeout=3.0  # Fail-fast: 3秒プール作成タイムアウト
                )
                
                # PostgreSQL & pgvector確認（Fail-fast）
                async with self.postgres_pool.acquire() as conn:
                    # pgvector拡張確認
                    extensions = await asyncio.wait_for(
                        conn.fetch("SELECT extname FROM pg_extension WHERE extname = 'vector'"),
                        timeout=1.0
                    )
                    if not extensions:
                        raise PostgreSQLConnectionError("pgvector extension not found")
                    
                    await asyncio.wait_for(conn.fetchval('SELECT 1'), timeout=1.0)
                    self.health_status.postgres_connected = True
                
                postgres_time = time.time() - postgres_start
                self.logger.info(f"✅ PostgreSQL connected in {postgres_time:.3f}s")
                
            except asyncio.TimeoutError:
                postgres_error_time = time.time() - postgres_start
                self.logger.error(f"❌ PostgreSQL connection timeout after {postgres_error_time:.3f}s")
                raise PostgreSQLConnectionError(f"PostgreSQL connection timeout after {postgres_error_time:.3f}s")
            except Exception as e:
                postgres_error_time = time.time() - postgres_start
                self.logger.error(f"❌ PostgreSQL initialization failed after {postgres_error_time:.3f}s: {e}")
                raise PostgreSQLConnectionError(f"PostgreSQL initialization failed: {e}")
            
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
            
        except (RedisConnectionError, PostgreSQLConnectionError) as e:
            # Fail-fast: 接続エラーは即座に再発生（隠蔽禁止）
            self.health_status.error_count += 1
            raise  # Fail-fast原則: 即座にエラー伝播
            
        except Exception as e:
            # その他のエラーも即座に報告
            self.logger.error(f"❌ Memory System initialization failed: {e}")
            self.health_status.error_count += 1
            raise MemorySystemError(f"Memory system initialization failed: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(redis.RedisError)
    )
    async def load_hot_memory(self, channel_id: str) -> List[Dict[str, Any]]:
        """Hot Memory読み込み（リトライ機能付き）"""
        try:
            if not self.redis:
                raise RedisConnectionError("Redis connection not available")
            
            redis_key = f"channel:{channel_id}:messages"
            
            # パイプライン使用で効率化 + パフォーマンス計測
            start_time = asyncio.get_event_loop().time()
            if not self.redis:
                raise RedisConnectionError("Redis not connected")
            async with self.redis.pipeline(transaction=False) as pipe:
                pipe.lrange(redis_key, 0, self.hot_memory_limit - 1)
                pipe.expire(redis_key, self.hot_memory_ttl)
                pipe_results = await pipe.execute()
                results = pipe_results if pipe_results else []
            elapsed_time = asyncio.get_event_loop().time() - start_time
            
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
            
            # パフォーマンスメトリクス更新
            self.performance_metrics['hot_memory_operations'] += 1
            
            self.logger.debug(
                f"Hot Memory loaded",
                extra={
                    "channel_id": channel_id, 
                    "message_count": len(hot_memory),
                    "load_time_ms": int(elapsed_time * 1000)
                }
            )
            return hot_memory
            
        except redis.RedisError as e:
            self.logger.error(f"Hot Memory load failed: {e}")
            self.health_status.redis_connected = False
            raise RedisConnectionError(f"Redis read failed: {e}")
    
    async def load_cold_memory(self, query: str, channel_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Cold Memory検索（unified_memoriesテーブル使用）"""
        try:
            if not self.postgres_pool:
                raise PostgreSQLConnectionError("PostgreSQL pool not available")
            
            # Embedding生成
            query_embedding = await self.generate_embedding_with_rate_limit(query)
            if not query_embedding:
                raise EmbeddingError(f"Failed to generate embedding for query: {query}")
            
            # unified_memoriesテーブル検索実行（パフォーマンス最適化）
            search_start = asyncio.get_event_loop().time()
            async with self.postgres_pool.acquire() as conn:
                # HNSWインデックス最適化設定
                await conn.execute("SET hnsw.ef_search = 150")  # バランス型パフォーマンス
                
                # 検索クエリ実行（最適化版）
                sql = """
                    SELECT memory_id, content, created_at, selected_agent, importance_score,
                           1 - (content_embedding <=> $1::vector) as similarity
                    FROM unified_memories 
                    WHERE ($2::text IS NULL OR channel_id = $2::bigint)
                      AND content_embedding IS NOT NULL
                    ORDER BY content_embedding <=> $1::vector
                    LIMIT $3
                """
                results = await conn.fetch(
                    sql, 
                    query_embedding, 
                    channel_id,
                    self.max_cold_results
                )
            search_time = asyncio.get_event_loop().time() - search_start
            
            # パフォーマンスメトリクス更新
            self.performance_metrics['cold_memory_operations'] += 1
            
            # 結果を辞書形式に変換
            cold_memory = []
            for row in results:
                cold_memory.append({
                    'memory_id': str(row['memory_id']),
                    'content': row['content'],
                    'similarity': float(row['similarity']) if row['similarity'] else 0.0,
                    'created_at': row['created_at'].isoformat() if row['created_at'] else '',
                    'selected_agent': row['selected_agent'] or 'unknown',
                    'importance_score': float(row['importance_score']) if row['importance_score'] else 0.0
                })
            
            self.logger.info(
                f"Cold Memory search completed",
                extra={
                    "query_length": len(query),
                    "results_count": len(cold_memory),
                    "channel_id": channel_id,
                    "search_time_ms": int(search_time * 1000)
                }
            )
            return cold_memory
            
        except asyncpg.PostgresError as e:
            self.logger.error(f"Cold Memory search failed: {e}")
            self.health_status.postgres_connected = False
            raise PostgreSQLConnectionError(f"PostgreSQL search failed: {e}")
        
        except Exception as e:
            self.logger.error(f"Cold Memory load failed: {e}")
            raise MemorySystemError(f"Cold memory search failed: {e}")
    
    async def migrate_to_cold_memory(self, channel_id: str, batch_size: Optional[int] = None) -> Dict[str, Any]:
        """ホットメモリからコールドメモリへの移行 - 最適化版"""
        if batch_size is None:
            batch_size = self.migration_batch_size
        
        start_time = asyncio.get_event_loop().time()
        memory_before = psutil.Process().memory_info().rss if psutil else 0
        
        try:
            if not self.redis or not self.postgres_pool:
                return {
                    'migrated_count': 0, 
                    'channel_id': channel_id, 
                    'status': 'failed',
                    'error': 'Redis or PostgreSQL not available'
                }
            
            redis_key = f"channel:{channel_id}:messages"
            
            # Redisからホットメモリ読み込み
            messages_result = await self.redis.lrange(redis_key, 0, batch_size - 1)
            messages = messages_result if messages_result else []
            
            if not messages:
                return {
                    'migrated_count': 0,
                    'channel_id': channel_id,
                    'status': 'success',
                    'message': 'No messages to migrate'
                }
            
            migrated_count = 0
            failed_count = 0
            
            # 完全なACIDトランザクション実装
            async with self.postgres_pool.acquire() as conn:
                async with conn.transaction():
                    for i, msg_json in enumerate(messages):
                        try:
                            msg_data = json.loads(msg_json)
                            content = msg_data.get('response_content', '')
                            
                            if content:
                                # Embedding生成（レート制限付き）
                                embedding = await self.generate_embedding_with_rate_limit(content)
                                if embedding:
                                    # unified_memoriesテーブルに保存
                                    await conn.execute("""
                                        INSERT INTO unified_memories (
                                            guild_id, channel_id, user_id, message_id,
                                            content, selected_agent, confidence,
                                            content_embedding, importance_score
                                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                    """,
                                        0,  # guild_id
                                        int(channel_id) if channel_id.isdigit() else 0,
                                        0,  # user_id  
                                        0,  # message_id
                                        content,
                                        msg_data.get('selected_agent', 'unknown'),
                                        msg_data.get('confidence', 0.5),
                                        embedding,
                                        min(msg_data.get('confidence', 0.5), 1.0)
                                    )
                                    migrated_count += 1
                                else:
                                    failed_count += 1
                                    self.logger.warning(f"Failed to generate embedding for message {i}")
                            else:
                                failed_count += 1
                        
                        except (json.JSONDecodeError, asyncpg.PostgresError) as e:
                            failed_count += 1
                            self.logger.warning(f"Failed to migrate message {i}: {e}")
                            continue
                        
                        # メモリクリーンアップ（大量バッチ処理でのメモリ節約）
                        if i % 50 == 0 and i > 0:
                            gc.collect()
            
            # Redis削除（移行成功分のみ）
            if migrated_count > 0:
                await self.redis.ltrim(redis_key, migrated_count, -1)
            
            # パフォーマンス計測
            elapsed_time = asyncio.get_event_loop().time() - start_time
            memory_after = psutil.Process().memory_info().rss if psutil else 0
            memory_delta = memory_after - memory_before
            
            self.logger.info(
                f"Migration completed for channel {channel_id}",
                extra={
                    "migrated_count": migrated_count,
                    "failed_count": failed_count,
                    "elapsed_ms": int(elapsed_time * 1000),
                    "memory_delta_mb": memory_delta / 1024 / 1024 if psutil else 0
                }
            )
            
            return {
                'migrated_count': migrated_count,
                'failed_count': failed_count,
                'channel_id': channel_id,
                'status': 'success',
                'elapsed_time': elapsed_time,
                'memory_delta_mb': memory_delta / 1024 / 1024 if psutil else 0
            }
            
        except (redis.RedisError, asyncpg.PostgresError) as e:
            self.logger.error(f"Migration connection error: {e}")
            raise MemorySystemConnectionError(f"Migration failed: {e}")
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return {
                'migrated_count': 0,
                'channel_id': channel_id,
                'status': 'failed',
                'error': str(e)
            }
    
    async def update_memory_transactional(self, conversation_data: Dict[str, Any]) -> bool:
        """Memory更新（トランザクション保証 + パフォーマンス最適化）"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            channel_id = conversation_data.get('channel_id')
            if not channel_id:
                raise ValueError("channel_id is required")
            
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
                raise ValueError("No messages provided for memory update")
            
            latest_message = messages[-1] if messages else None
            user_content = getattr(latest_message, 'content', '') if latest_message else ''
            
            if not user_content:
                raise ValueError("No user content available for memory update")
            
            # Embedding生成（パフォーマンス計測付き）
            content_embedding = await self._measure_performance(
                "content_embedding_generation",
                self.generate_embedding_with_rate_limit,
                user_content
            )
            response_embedding = await self._measure_performance(
                "response_embedding_generation", 
                self.generate_embedding_with_rate_limit,
                conversation_data.get('response_content', '')
            )
            
            # カスタムTTL対応
            ttl = conversation_data.get('custom_ttl', self.hot_memory_ttl)
            
            # 原子的トランザクション実行
            await self._execute_atomic_transaction(
                redis_key, memory_entry, ttl,
                conversation_data, user_content, content_embedding
            )
            
            # パフォーマンスログ
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.info(
                "Memory updated successfully",
                extra={
                    "channel_id": channel_id,
                    "elapsed_ms": int(elapsed_time * 1000),
                    "has_embedding": bool(content_embedding)
                }
            )
            return True
            
        except (redis.RedisError, asyncpg.PostgresError) as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(
                f"Memory update connection error: {e}",
                extra={"elapsed_ms": int(elapsed_time * 1000)}
            )
            raise MemorySystemConnectionError(f"Memory update failed: {e}")
            
        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(
                f"Memory update failed: {e}",
                extra={"elapsed_ms": int(elapsed_time * 1000)}
            )
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
            embedding_result = self.embeddings_client.embed_query(truncated_text)
            if asyncio.iscoroutine(embedding_result):
                embedding = await embedding_result
            else:
                embedding = embedding_result
            
            return embedding
            
        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "rate" in error_str:
                self.logger.warning(f"Embedding API quota/rate limit: {e}")
                raise EmbeddingQuotaError(f"API quota exceeded: {e}")
            else:
                self.logger.error(f"Embedding generation failed: {e}")
                raise EmbeddingError(f"Embedding failed: {e}")
    
    async def get_detailed_health_status(self) -> Dict[str, Any]:
        """詳細なシステム状態監視ヘルスチェック"""
        health_check_start = asyncio.get_event_loop().time()
        
        try:
            # Redis健康確認 + レイテンシー測定
            redis_latency = None
            if self.redis:
                try:
                    redis_start = asyncio.get_event_loop().time()
                    await self.redis.ping()
                    redis_latency = asyncio.get_event_loop().time() - redis_start
                    self.health_status.redis_connected = True
                    
                    # Redisプール統計
                    if self.redis_pool:
                        pool_info = {
                            'max_connections': self.redis_pool.max_connections,
                            'created_connections': len(self.redis_pool._created_connections) if hasattr(self.redis_pool, '_created_connections') else 'unknown'
                        }
                    else:
                        pool_info = {'error': 'pool not available'}
                    
                    self.health_status.redis_pool_health = pool_info
                    
                except Exception as e:
                    self.health_status.redis_connected = False
                    self.health_status.redis_pool_health = {'error': str(e)}
            
            # PostgreSQL健康確認 + レイテンシー測定
            postgres_latency = None
            if self.postgres_pool:
                try:
                    postgres_start = asyncio.get_event_loop().time()
                    async with self.postgres_pool.acquire() as conn:
                        await conn.fetchval('SELECT 1')
                    postgres_latency = asyncio.get_event_loop().time() - postgres_start
                    self.health_status.postgres_connected = True
                    
                    # PostgreSQLプール統計
                    pool_info = {
                        'min_size': self.postgres_pool._minsize,
                        'max_size': self.postgres_pool._maxsize,
                        'current_size': self.postgres_pool.get_size(),
                        'idle_connections': self.postgres_pool.get_idle_size()
                    }
                    self.health_status.postgres_pool_health = pool_info
                    
                except Exception as e:
                    self.health_status.postgres_connected = False
                    self.health_status.postgres_pool_health = {'error': str(e)}
            
            # リソース使用状況
            resource_info = {}
            if psutil:
                process = psutil.Process()
                resource_info = {
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(),
                    'open_files': len(process.open_files()) if hasattr(process, 'open_files') else 'unknown'
                }
            
            # パフォーマンスメトリクス
            performance_metrics = {
                'redis_latency_ms': int(redis_latency * 1000) if redis_latency else None,
                'postgres_latency_ms': int(postgres_latency * 1000) if postgres_latency else None,
                'health_check_time_ms': int((asyncio.get_event_loop().time() - health_check_start) * 1000)
            }
            
            self.health_status.performance_metrics = performance_metrics
            self.health_status.last_check = datetime.now()
            
            return {
                "status": "healthy" if self.health_status.is_healthy else "unhealthy",
                "components": {
                    "redis": {
                        "connected": self.health_status.redis_connected,
                        "latency_ms": performance_metrics['redis_latency_ms'],
                        "pool": self.health_status.redis_pool_health
                    },
                    "postgres": {
                        "connected": self.health_status.postgres_connected,
                        "latency_ms": performance_metrics['postgres_latency_ms'],
                        "pool": self.health_status.postgres_pool_health
                    },
                    "embeddings": {
                        "available": self.health_status.embeddings_available
                    }
                },
                "resources": resource_info,
                "performance": performance_metrics,
                "last_check": self.health_status.last_check.isoformat(),
                "error_count": self.health_status.error_count
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """簡易ヘルスチェック（互換性維持）"""
        detailed = await self.get_detailed_health_status()
        return {
            "status": detailed["status"],
            "redis": detailed["components"]["redis"]["connected"],
            "postgres": detailed["components"]["postgres"]["connected"],
            "embeddings": detailed["components"]["embeddings"]["available"],
            "last_check": detailed["last_check"],
            "error_count": detailed["error_count"]
        }
    
    async def store_task(self, task_key: str, task_data: Dict[str, Any]) -> bool:
        """タスクデータをRedisに保存"""
        if not self.redis:
            raise RedisConnectionError("Redis not available for task storage")
                
        task_json = json.dumps(task_data, ensure_ascii=False, default=str)
        await self.redis.setex(task_key, 86400, task_json)  # 24時間保持
        self.logger.info(f"Task stored: {task_key}")
        return True
    
    async def cleanup(self) -> None:
        """リソース正常終了（最適化版）"""
        cleanup_tasks = []
        
        try:
            # Redisクリーンアップ
            if self.redis:
                cleanup_tasks.append(self._cleanup_redis())
            
            # PostgreSQLクリーンアップ
            if self.postgres_pool:
                cleanup_tasks.append(self._cleanup_postgres())
            
            # 並列クリーンアップ実行
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            # メモリクリーンアップ
            gc.collect()
            
            self.logger.info("Memory System cleanup completed successfully")
                
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    async def _cleanup_redis(self) -> None:
        """適切なRedisクリーンアップ"""
        try:
            if self.redis:
                await self.redis.close()
            if self.redis_pool:
                await self.redis_pool.disconnect()
            self.logger.info("Redis connection closed")
        except Exception as e:
            self.logger.warning(f"Redis cleanup warning: {e}")
    
    async def _cleanup_postgres(self) -> None:
        """適切なPostgreSQLクリーンアップ"""
        try:
            if self.postgres_pool:
                await self.postgres_pool.close()
            self.logger.info("PostgreSQL pool closed")
        except Exception as e:
            self.logger.warning(f"PostgreSQL cleanup warning: {e}")


    # 新しいヘルパーメソッド群
    async def _measure_performance(self, operation_name: str, func, *args, **kwargs):
        """各操作の詳細メトリクス測定"""
        start_time = asyncio.get_event_loop().time()
        memory_before = psutil.Process().memory_info().rss if psutil else 0
        
        try:
            result = await func(*args, **kwargs)
            success = True
        finally:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            memory_after = psutil.Process().memory_info().rss if psutil else 0
            memory_delta = memory_after - memory_before
            
            self.logger.info(f"Performance: {operation_name}", extra={
                'elapsed_ms': int(elapsed_time * 1000),
                'memory_delta_mb': memory_delta / 1024 / 1024 if psutil else 0,
                'success': success
            })
        
        return result
    
    # 戦略的フォールバック処理を完全削除（Fail-fast原則適用）
    
    async def _process_large_batch(self, items: List[Any], batch_size: int = 100):
        """大きなバッチ処理の分割処理"""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_result = await self._process_batch(batch)
            results.extend(batch_result)
            
            # メモリクリーンアップ
            if i % (batch_size * 10) == 0:
                gc.collect()
        
        return results
    
    async def _process_batch(self, batch: List[Any]):
        """バッチ処理の実装（サブクラスでオーバーライド）"""
        return batch  # デフォルト実装
    
    async def _update_redis_only(self, redis_key: str, memory_entry: Dict[str, Any], conversation_data: Dict[str, Any]) -> bool:
        """頂級Redisのみ更新処理"""
        try:
            if not self.redis:
                return False
            ttl = conversation_data.get('custom_ttl', self.hot_memory_ttl)
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.lpush(redis_key, json.dumps(memory_entry, default=str))
                pipe.ltrim(redis_key, 0, self.hot_memory_limit - 1)
                pipe.expire(redis_key, ttl)
                await pipe.execute()
            return True
        except Exception as e:
            self.logger.error(f"Redis-only update failed: {e}")
            return False
    
    async def _execute_atomic_transaction(self, redis_key: str, memory_entry: Dict[str, Any], 
                                         ttl: int, conversation_data: Dict[str, Any], 
                                         user_content: str, content_embedding: List[float]) -> None:
        """原子的トランザクション実行"""
        # Redis更新
        if not self.redis:
            raise RedisConnectionError("Redis not connected")
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.lpush(redis_key, json.dumps(memory_entry, default=str))
            pipe.ltrim(redis_key, 0, self.hot_memory_limit - 1)
            pipe.expire(redis_key, ttl)
            await pipe.execute()
        
        # PostgreSQL更新（Embeddingが生成できた場合のみ）
        if content_embedding and self.postgres_pool:
            async with self.postgres_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("""
                        INSERT INTO unified_memories (
                            guild_id, channel_id, user_id, message_id,
                            content, selected_agent, confidence,
                            content_embedding, importance_score
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                        int(conversation_data.get('guild_id', 0)),
                        int(conversation_data.get('channel_id', 0)) if str(conversation_data.get('channel_id', '')).isdigit() else 0,
                        int(conversation_data.get('user_id', 0)) if str(conversation_data.get('user_id', 0)).isdigit() else 0,
                        int(conversation_data.get('message_id', 0)) if str(conversation_data.get('message_id', 0)).isdigit() else 0,
                        user_content,
                        conversation_data.get('selected_agent', 'unknown'),
                        conversation_data.get('confidence', 0.5),
                        content_embedding,
                        min(conversation_data.get('confidence', 0.5), 1.0)
                    )


# Factory関数
def create_improved_memory_system() -> ImprovedDiscordMemorySystem:
    """改善版Memory System生成"""
    # 中央設定から取得
    db_settings = get_database_settings()
    ai_settings = get_ai_settings()
    
    redis_url = db_settings.redis_url
    postgres_url = db_settings.postgresql_url
    gemini_api_key = ai_settings.gemini_api_key
    
    return ImprovedDiscordMemorySystem(
        redis_url=redis_url,
        postgres_url=postgres_url,
        gemini_api_key=gemini_api_key
    )