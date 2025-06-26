#!/usr/bin/env python3
"""
Discord Multi-Agent System Configuration
Clean Architecture - 設定管理モジュール
"""

import os
from typing import Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """環境設定列挙型"""
    DEVELOPMENT = "development"
    TEST = "test" 
    PRODUCTION = "production"


@dataclass
class DiscordSettings:
    """Discord関連設定"""
    # Bot tokens (必須)
    reception_token: str
    spectra_token: str
    lynq_token: str
    paz_token: str
    
    # Bot IDs (メンション用)
    spectra_bot_id: int = 0
    lynq_bot_id: int = 0
    paz_bot_id: int = 0
    
    # Channel IDs
    command_center_id: int = 0
    lounge_id: int = 0
    development_id: int = 0
    creation_id: int = 0
    
    @classmethod
    def from_env(cls) -> 'DiscordSettings':
        """環境変数からDiscord設定を生成"""
        return cls(
            reception_token=cls._get_required_env('DISCORD_RECEPTION_TOKEN'),
            spectra_token=cls._get_required_env('DISCORD_SPECTRA_TOKEN'),
            lynq_token=cls._get_required_env('DISCORD_LYNQ_TOKEN'),
            paz_token=cls._get_required_env('DISCORD_PAZ_TOKEN'),
            spectra_bot_id=int(cls._get_required_env('DISCORD_SPECTRA_BOT_ID')),
            lynq_bot_id=int(cls._get_required_env('DISCORD_LYNQ_BOT_ID')),
            paz_bot_id=int(cls._get_required_env('DISCORD_PAZ_BOT_ID')),
            command_center_id=int(cls._get_required_env('COMMAND_CENTER_CHANNEL_ID')),
            lounge_id=int(cls._get_required_env('LOUNGE_CHANNEL_ID')),
            development_id=int(cls._get_required_env('DEVELOPMENT_CHANNEL_ID')),
            creation_id=int(cls._get_required_env('CREATION_CHANNEL_ID'))
        )
    
    @staticmethod
    def _get_required_env(key: str) -> str:
        """必須環境変数の取得（コメント除去対応）"""
        value = os.getenv(key)
        if not value:
            raise EnvironmentError(f"Required environment variable '{key}' is not set")
        # コメントを除去（# で分割して最初を取得）
        return value.split('#')[0].strip()
    
    @property
    def channel_ids(self) -> Dict[str, int]:
        """チャンネルID辞書を返す"""
        return {
            "command_center": self.command_center_id,
            "lounge": self.lounge_id,
            "development": self.development_id,
            "creation": self.creation_id
        }
    
    @property
    def bot_ids(self) -> Dict[str, int]:
        """ボットID辞書を返す"""
        return {
            "spectra": self.spectra_bot_id,
            "lynq": self.lynq_bot_id,
            "paz": self.paz_bot_id
        }
    
    def validate(self) -> None:
        """Discord設定の検証"""
        tokens = [
            self.reception_token,
            self.spectra_token, 
            self.lynq_token,
            self.paz_token
        ]
        
        if not all(tokens):
            raise ValueError("All Discord bot tokens must be provided")
        
        # トークン形式の検証（test/production環境で統一）
        # 両環境でリアルDiscordトークンを使用
        for token in tokens:
            if not token:
                raise ValueError("Discord token cannot be empty")
            if len(token) < 50:  # Discord botトークンは通常50文字以上
                raise ValueError(f"Invalid Discord token format: {token[:10]}...")
            # 実際のDiscordトークンの基本パターンチェック
            if not (token.count('.') >= 2):  # Discord tokenは通常ピリオドを含む
                raise ValueError(f"Invalid Discord token pattern: {token[:10]}...")


@dataclass
class AISettings:
    """AI関連設定"""
    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    
    # Embedding設定
    embedding_model: str = "text-embedding-004"
    embedding_batch_size: int = 100
    
    @classmethod
    def from_env(cls) -> 'AISettings':
        """環境変数からAI設定を生成"""
        return cls(
            gemini_api_key=cls._get_required_env('GEMINI_API_KEY'),
            gemini_model=os.getenv('GEMINI_MODEL', 'gemini-2.0-flash'),
            embedding_model=os.getenv('EMBEDDING_MODEL', 'text-embedding-004'),
            embedding_batch_size=int(os.getenv('EMBEDDING_BATCH_SIZE', '100'))
        )
    
    @staticmethod
    def _get_required_env(key: str) -> str:
        """必須環境変数の取得（コメント除去対応）"""
        value = os.getenv(key)
        if not value:
            raise EnvironmentError(f"Required environment variable '{key}' is not set")
        # コメントを除去（# で分割して最初を取得）
        return value.split('#')[0].strip()
    
    def validate(self) -> None:
        """AI設定の検証"""
        if not self.gemini_api_key:
            raise ValueError("Gemini API key is required")
        
        if self.embedding_batch_size <= 0:
            raise ValueError("Embedding batch size must be positive")


@dataclass
class DatabaseSettings:
    """データベース関連設定"""
    # Redis設定
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_max_connections: int = 10
    
    # PostgreSQL設定
    postgresql_url: str = "postgresql://user:pass@localhost:5432/discord_agents"
    postgresql_pool_size: int = 20
    postgresql_max_overflow: int = 30
    postgres_pool_min_size: int = 2
    postgres_pool_max_size: int = 10
    
    # メモリシステム設定
    hot_memory_ttl_seconds: int = 86400  # 24時間
    cold_memory_retention_days: int = 30
    memory_migration_batch_size: int = 100
    
    @classmethod
    def from_env(cls) -> 'DatabaseSettings':
        """環境変数からDB設定を生成"""
        return cls(
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
            redis_db=int(os.getenv('REDIS_DB', '0')),
            redis_password=os.getenv('REDIS_PASSWORD'),
            redis_max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '10')),
            postgresql_url=os.getenv('POSTGRESQL_URL', 'postgresql://user:pass@localhost:5432/discord_agents'),
            postgresql_pool_size=int(os.getenv('POSTGRESQL_POOL_SIZE', '20')),
            postgresql_max_overflow=int(os.getenv('POSTGRESQL_MAX_OVERFLOW', '30')),
            postgres_pool_min_size=int(os.getenv('POSTGRES_POOL_MIN_SIZE', '2')),
            postgres_pool_max_size=int(os.getenv('POSTGRES_POOL_MAX_SIZE', '10')),
            hot_memory_ttl_seconds=int(os.getenv('HOT_MEMORY_TTL_SECONDS', '86400')),
            cold_memory_retention_days=int(os.getenv('COLD_MEMORY_RETENTION_DAYS', '30')),
            memory_migration_batch_size=int(os.getenv('MEMORY_MIGRATION_BATCH_SIZE', '100'))
        )


@dataclass
class SystemSettings:
    """システム関連設定"""
    # 環境設定
    environment: Environment = Environment.PRODUCTION
    debug: bool = False
    
    # ログ設定
    log_level: str = "INFO"
    log_file: str = "logs/discord_agent.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_rotation: bool = True
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # ヘルスチェック設定
    health_check_port: int = 8000
    health_check_host: str = "0.0.0.0"
    
    # パフォーマンス設定
    max_concurrent_users: int = 50
    message_queue_size: int = 1000
    
    # 自発発言設定
    autonomous_speech_test_interval: int = 10  # seconds
    autonomous_speech_prod_interval: int = 300  # seconds (5 minutes)
    
    # アプリケーション情報
    app_version: str = "v0.3.0"
    
    # ワークフロー制御（テスト用）
    test_workflow_time: Optional[str] = None
    
    # ワークフロー統合時間制御（単一情報源）
    workflow_morning_workflow_time: str = "06:00"    # PROCESSING phase starts + long-term memory processing
    workflow_active_transition_time: str = "07:00"   # ACTIVE phase starts (after morning workflow completion)
    workflow_work_conclusion_time: str = "20:00"     # FREE phase starts + work conclusion event  
    workflow_system_rest_time: str = "00:00"         # STANDBY phase starts + system rest event
    
    @classmethod
    def from_env(cls) -> 'SystemSettings':
        """環境変数からシステム設定を生成"""
        env_str = os.getenv('ENVIRONMENT', 'production').lower()
        environment = Environment(env_str)
        
        return cls(
            environment=environment,
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO').upper(),
            log_file=os.getenv('LOG_FILE', 'logs/discord_agent.log'),
            health_check_port=int(os.getenv('HEALTH_CHECK_PORT', '8000')),
            health_check_host=os.getenv('HEALTH_CHECK_HOST', '0.0.0.0'),
            max_concurrent_users=int(os.getenv('MAX_CONCURRENT_USERS', '50')),
            message_queue_size=int(os.getenv('MESSAGE_QUEUE_SIZE', '1000')),
            autonomous_speech_test_interval=int(os.getenv('AUTONOMOUS_SPEECH_TEST_INTERVAL', '10')),
            autonomous_speech_prod_interval=int(os.getenv('AUTONOMOUS_SPEECH_PROD_INTERVAL', '300')),
            app_version=os.getenv('APP_VERSION', 'v0.3.0'),
            test_workflow_time=os.getenv('TEST_WORKFLOW_TIME'),
            workflow_morning_workflow_time=os.getenv('WORKFLOW_MORNING_WORKFLOW_TIME', '06:00'),
            workflow_active_transition_time=os.getenv('WORKFLOW_ACTIVE_TRANSITION_TIME', '07:00'),
            workflow_work_conclusion_time=os.getenv('WORKFLOW_WORK_CONCLUSION_TIME', '20:00'),
            workflow_system_rest_time=os.getenv('WORKFLOW_SYSTEM_REST_TIME', '00:00')
        )
    
    @classmethod
    def _get_required_env(cls, key: str) -> str:
        """必須環境変数の取得"""
        value = os.getenv(key)
        if not value:
            raise EnvironmentError(f"Required environment variable '{key}' is not set")
        return value
    
    @property
    def is_test(self) -> bool:
        """テスト環境かどうか"""
        return self.environment == Environment.TEST
    
    @property
    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def autonomous_speech_interval(self) -> int:
        """環境に応じた自発発言間隔"""
        return self.autonomous_speech_test_interval if self.is_test else self.autonomous_speech_prod_interval
    
    def parse_time_setting(self, time_str: str) -> tuple[int, int]:
        """時間設定文字列をパース（HH:MM → (hour, minute)）"""
        try:
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError(f"Invalid time range: {time_str}")
            return hour, minute
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid time format '{time_str}': must be HH:MM format") from e
    
    @property
    def workflow_phase_hours(self) -> dict[str, int]:
        """ワークフローフェーズの開始時刻（統合時間ソースから生成）"""
        return {
            'processing': self.parse_time_setting(self.workflow_morning_workflow_time)[0],
            'active': self.parse_time_setting(self.workflow_active_transition_time)[0],
            'free': self.parse_time_setting(self.workflow_work_conclusion_time)[0],
            'standby': self.parse_time_setting(self.workflow_system_rest_time)[0]
        }


@dataclass
class PerformanceSettings:
    """パフォーマンス監視設定"""
    # パフォーマンス閾値（必須設定）
    hot_memory_target_ms: int
    cold_memory_target_ms: int
    embedding_target_ms: int
    error_rate_threshold: float
    
    # サーキットブレーカー設定（必須設定）
    circuit_breaker_failure_threshold: int
    circuit_breaker_recovery_timeout: int
    
    # パフォーマンス履歴設定
    performance_history_size: int = 1000
    benchmark_results_path: str = "./benchmarks/"
    
    @classmethod
    def from_env(cls) -> 'PerformanceSettings':
        """環境変数からパフォーマンス設定を生成"""
        return cls(
            hot_memory_target_ms=int(cls._get_required_env('HOT_MEMORY_TARGET_MS')),
            cold_memory_target_ms=int(cls._get_required_env('COLD_MEMORY_TARGET_MS')),
            embedding_target_ms=int(cls._get_required_env('EMBEDDING_TARGET_MS')),
            error_rate_threshold=float(cls._get_required_env('ERROR_RATE_THRESHOLD')),
            circuit_breaker_failure_threshold=int(cls._get_required_env('CIRCUIT_BREAKER_FAILURE_THRESHOLD')),
            circuit_breaker_recovery_timeout=int(cls._get_required_env('CIRCUIT_BREAKER_RECOVERY_TIMEOUT')),
            performance_history_size=int(os.getenv('PERFORMANCE_HISTORY_SIZE', '1000')),
            benchmark_results_path=os.getenv('BENCHMARK_RESULTS_PATH', './benchmarks/')
        )
    
    @staticmethod
    def _get_required_env(key: str) -> str:
        """必須環境変数の取得（コメント除去対応）"""
        value = os.getenv(key)
        if not value:
            raise EnvironmentError(f"Required environment variable '{key}' is not set")
        # コメントを除去（# で分割して最初を取得）
        return value.split('#')[0].strip()


@dataclass
class LongTermMemorySettings:
    """長期記憶システム設定"""
    # 機能有効化フラグ
    enabled: bool = True
    vector_search_enabled: bool = True
    daily_report_enabled: bool = True
    
    # 重複除去・品質設定
    deduplication_threshold: float = 0.8
    min_importance_score: float = 0.4
    
    # API制限設定
    api_quota_daily_limit: int = 3
    
    @classmethod
    def from_env(cls) -> 'LongTermMemorySettings':
        """環境変数から長期記憶設定を生成"""
        return cls(
            enabled=os.getenv('LONG_TERM_MEMORY_ENABLED', 'true').lower() == 'true',
            vector_search_enabled=os.getenv('VECTOR_SEARCH_ENABLED', 'true').lower() == 'true',
            daily_report_enabled=os.getenv('DAILY_REPORT_ENABLED', 'true').lower() == 'true',
            deduplication_threshold=float(os.getenv('DEDUPLICATION_THRESHOLD', '0.8')),
            min_importance_score=float(os.getenv('MIN_IMPORTANCE_SCORE', '0.4')),
            api_quota_daily_limit=int(os.getenv('API_QUOTA_DAILY_LIMIT', '3'))
        )


@dataclass
class EmbeddingSettings:
    """Embedding API設定"""
    # API制限設定
    retry_attempts: int = 3
    batch_size: int = 250
    rpm_limit: int = 15
    
    @classmethod
    def from_env(cls) -> 'EmbeddingSettings':
        """環境変数からEmbedding設定を生成"""
        return cls(
            retry_attempts=int(os.getenv('EMBEDDING_RETRY_ATTEMPTS', '3')),
            batch_size=int(os.getenv('EMBEDDING_BATCH_SIZE', '250')),
            rpm_limit=int(os.getenv('EMBEDDING_RPM_LIMIT', '15'))
        )


@dataclass
class AppSettings:
    """アプリケーション全体設定"""
    discord: DiscordSettings
    ai: AISettings
    database: DatabaseSettings
    system: SystemSettings
    performance: PerformanceSettings
    long_term_memory: LongTermMemorySettings
    embedding: EmbeddingSettings
    
    @classmethod
    def from_env(cls) -> 'AppSettings':
        """環境変数から全設定を生成"""
        return cls(
            discord=DiscordSettings.from_env(),
            ai=AISettings.from_env(),
            database=DatabaseSettings.from_env(),
            system=SystemSettings.from_env(),
            performance=PerformanceSettings.from_env(),
            long_term_memory=LongTermMemorySettings.from_env(),
            embedding=EmbeddingSettings.from_env()
        )
    
    def validate(self) -> None:
        """全設定の検証"""
        self.discord.validate()
        self.ai.validate()
        # database, system, performance, long_term_memory, embeddingは自動検証
    
    @property
    def required_env_vars(self) -> List[str]:
        """必須環境変数リスト"""
        return [
            'DISCORD_RECEPTION_TOKEN',
            'DISCORD_SPECTRA_TOKEN', 
            'DISCORD_LYNQ_TOKEN',
            'DISCORD_PAZ_TOKEN',
            'DISCORD_SPECTRA_BOT_ID',
            'DISCORD_LYNQ_BOT_ID',
            'DISCORD_PAZ_BOT_ID',
            'COMMAND_CENTER_CHANNEL_ID',
            'LOUNGE_CHANNEL_ID',
            'DEVELOPMENT_CHANNEL_ID',
            'CREATION_CHANNEL_ID',
            'GEMINI_API_KEY'
        ]
    
    def get_missing_env_vars(self) -> List[str]:
        """不足している環境変数のリスト"""
        return [var for var in self.required_env_vars if not os.getenv(var)]


# グローバル設定インスタンス
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """アプリケーション設定のシングルトン取得"""
    global _settings
    if _settings is None:
        _settings = AppSettings.from_env()
        _settings.validate()
    return _settings


def reload_settings() -> AppSettings:
    """設定を再読み込み（テスト用）"""
    global _settings
    _settings = None
    return get_settings()


# 便利関数
def get_discord_settings() -> DiscordSettings:
    """Discord設定の取得"""
    return get_settings().discord


def get_ai_settings() -> AISettings:
    """AI設定の取得"""
    return get_settings().ai


def get_database_settings() -> DatabaseSettings:
    """データベース設定の取得"""
    return get_settings().database


def get_system_settings() -> SystemSettings:
    """システム設定の取得"""
    return get_settings().system


def get_performance_settings() -> PerformanceSettings:
    """パフォーマンス設定の取得"""
    return get_settings().performance


def get_long_term_memory_settings() -> LongTermMemorySettings:
    """長期記憶設定の取得"""
    return get_settings().long_term_memory


def get_embedding_settings() -> EmbeddingSettings:
    """Embedding設定の取得"""
    return get_settings().embedding


# 環境変数チェック用関数
def check_required_env_vars() -> None:
    """必須環境変数の存在チェック"""
    settings = get_settings()
    missing_vars = settings.get_missing_env_vars()
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {missing_vars}\n"
            f"Please set these variables before starting the application."
        )


if __name__ == "__main__":
    # 設定テスト実行
    try:
        settings = get_settings()
        print("✅ All settings loaded successfully")
        print(f"Environment: {settings.system.environment.value}")
        print(f"Discord channels configured: {len([c for c in settings.discord.channel_ids.values() if c > 0])}")
        print(f"Log level: {settings.system.log_level}")
        print(f"Health check port: {settings.system.health_check_port}")
    except Exception as e:
        print(f"❌ Settings validation failed: {e}")