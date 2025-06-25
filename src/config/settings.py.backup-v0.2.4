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
            spectra_bot_id=int(os.getenv('DISCORD_SPECTRA_BOT_ID')),
            lynq_bot_id=int(os.getenv('DISCORD_LYNQ_BOT_ID')),
            paz_bot_id=int(os.getenv('DISCORD_PAZ_BOT_ID')),
            command_center_id=int(os.getenv('COMMAND_CENTER_CHANNEL_ID')),
            lounge_id=int(os.getenv('LOUNGE_CHANNEL_ID')),
            development_id=int(os.getenv('DEVELOPMENT_CHANNEL_ID')),
            creation_id=int(os.getenv('CREATION_CHANNEL_ID'))
        )
    
    @staticmethod
    def _get_required_env(key: str) -> str:
        """必須環境変数の取得"""
        value = os.getenv(key)
        if not value:
            raise EnvironmentError(f"Required environment variable '{key}' is not set")
        return value
    
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
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Embedding設定
    embedding_model: str = "text-embedding-004"
    embedding_batch_size: int = 100
    
    @classmethod
    def from_env(cls) -> 'AISettings':
        """環境変数からAI設定を生成"""
        return cls(
            gemini_api_key=cls._get_required_env('GEMINI_API_KEY'),
            gemini_model=os.getenv('GEMINI_MODEL'),
            embedding_model=os.getenv('EMBEDDING_MODEL'),
            embedding_batch_size=int(os.getenv('EMBEDDING_BATCH_SIZE'))
        )
    
    @staticmethod
    def _get_required_env(key: str) -> str:
        """必須環境変数の取得"""
        value = os.getenv(key)
        if not value:
            raise EnvironmentError(f"Required environment variable '{key}' is not set")
        return value
    
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
    
    # PostgreSQL設定
    postgresql_url: str = "postgresql://user:pass@localhost:5432/discord_agents"
    postgresql_pool_size: int = 20
    postgresql_max_overflow: int = 30
    
    @classmethod
    def from_env(cls) -> 'DatabaseSettings':
        """環境変数からDB設定を生成"""
        return cls(
            redis_url=os.getenv('REDIS_URL'),
            redis_db=int(os.getenv('REDIS_DB')),
            redis_password=os.getenv('REDIS_PASSWORD'),
            postgresql_url=os.getenv('POSTGRESQL_URL'),
            postgresql_pool_size=int(os.getenv('POSTGRESQL_POOL_SIZE')),
            postgresql_max_overflow=int(os.getenv('POSTGRESQL_MAX_OVERFLOW'))
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
    
    @classmethod
    def from_env(cls) -> 'SystemSettings':
        """環境変数からシステム設定を生成"""
        env_str = os.getenv('ENVIRONMENT').lower()
        environment = Environment(env_str)
        
        return cls(
            environment=environment,
            debug=os.getenv('DEBUG').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL').upper(),
            log_file=os.getenv('LOG_FILE'),
            health_check_port=int(os.getenv('HEALTH_CHECK_PORT')),
            health_check_host=os.getenv('HEALTH_CHECK_HOST'),
            max_concurrent_users=int(os.getenv('MAX_CONCURRENT_USERS')),
            message_queue_size=int(os.getenv('MESSAGE_QUEUE_SIZE')),
            autonomous_speech_test_interval=int(os.getenv('AUTONOMOUS_SPEECH_TEST_INTERVAL')),
            autonomous_speech_prod_interval=int(os.getenv('AUTONOMOUS_SPEECH_PROD_INTERVAL'))
        )
    
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


@dataclass
class AppSettings:
    """アプリケーション全体設定"""
    discord: DiscordSettings
    ai: AISettings
    database: DatabaseSettings
    system: SystemSettings
    
    @classmethod
    def from_env(cls) -> 'AppSettings':
        """環境変数から全設定を生成"""
        return cls(
            discord=DiscordSettings.from_env(),
            ai=AISettings.from_env(),
            database=DatabaseSettings.from_env(),
            system=SystemSettings.from_env()
        )
    
    def validate(self) -> None:
        """全設定の検証"""
        self.discord.validate()
        self.ai.validate()
        # database, systemは自動検証
    
    @property
    def required_env_vars(self) -> List[str]:
        """必須環境変数リスト"""
        return [
            'DISCORD_RECEPTION_TOKEN',
            'DISCORD_SPECTRA_TOKEN', 
            'DISCORD_LYNQ_TOKEN',
            'DISCORD_PAZ_TOKEN',
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