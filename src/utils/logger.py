#!/usr/bin/env python3
"""
Discord Multi-Agent System Logging
Clean Architecture - ログ管理モジュール
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..config.settings import get_system_settings, SystemSettings


class ColoredFormatter(logging.Formatter):
    """カラー付きログフォーマッター（開発環境用）"""
    
    # カラーコード
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # レベルに応じたカラー適用
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class PerformanceFilter(logging.Filter):
    """パフォーマンス関連ログのフィルター"""
    
    def __init__(self, min_duration: float = 1.0):
        super().__init__()
        self.min_duration = min_duration
    
    def filter(self, record):
        # パフォーマンスログのフィルタリング
        if hasattr(record, 'duration') and record.duration < self.min_duration:
            return False
        return True


class AgentLoggerAdapter(logging.LoggerAdapter):
    """エージェント情報付きログアダプター"""
    
    def __init__(self, logger, agent_name: str):
        super().__init__(logger, {'agent': agent_name})
    
    def process(self, msg, kwargs):
        # エージェント名を含むログメッセージ
        agent = self.extra['agent']
        return f"[{agent.upper()}] {msg}", kwargs


class LoggerManager:
    """ログマネージャー - Clean Architecture対応"""
    
    def __init__(self, settings: Optional[SystemSettings] = None):
        self.settings = settings or get_system_settings()
        self._loggers: Dict[str, logging.Logger] = {}
        self._initialized = False
    
    def setup_logging(self) -> None:
        """ログシステムの初期化"""
        if self._initialized:
            return
        
        # ログディレクトリ作成
        log_file_path = Path(self.settings.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ルートロガー設定
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.settings.log_level))
        
        # 既存ハンドラークリア
        root_logger.handlers.clear()
        
        # ハンドラー追加
        self._add_console_handler(root_logger)
        self._add_file_handler(root_logger)
        
        if self.settings.log_rotation:
            self._add_rotating_handler(root_logger)
        
        self._initialized = True
        
        # 初期化ログ
        logger = self.get_logger(__name__)
        logger.info(f"🚀 Logging system initialized")
        logger.info(f"Log level: {self.settings.log_level}")
        logger.info(f"Log file: {self.settings.log_file}")
        logger.info(f"Environment: {self.settings.environment.value}")
    
    def _add_console_handler(self, logger: logging.Logger) -> None:
        """コンソールハンドラー追加"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 開発環境ではカラー付きフォーマッター使用
        if not self.settings.is_production:
            formatter = ColoredFormatter(self.settings.log_format)
        else:
            formatter = logging.Formatter(self.settings.log_format)
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def _add_file_handler(self, logger: logging.Logger) -> None:
        """ファイルハンドラー追加"""
        file_handler = logging.FileHandler(
            self.settings.log_file,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, self.settings.log_level))
        
        # ファイルには常にプレーンフォーマット
        formatter = logging.Formatter(self.settings.log_format)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    def _add_rotating_handler(self, logger: logging.Logger) -> None:
        """ローテーションハンドラー追加"""
        rotating_handler = logging.handlers.RotatingFileHandler(
            self.settings.log_file + '.rotating',
            maxBytes=self.settings.log_max_bytes,
            backupCount=self.settings.log_backup_count,
            encoding='utf-8'
        )
        rotating_handler.setLevel(logging.DEBUG)
        
        # 詳細フォーマット（ローテーションファイル用）
        detailed_format = (
            "%(asctime)s | %(name)s:%(lineno)d | %(levelname)s | "
            "%(funcName)s() | %(message)s"
        )
        formatter = logging.Formatter(detailed_format)
        rotating_handler.setFormatter(formatter)
        
        logger.addHandler(rotating_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """ロガー取得（キャッシュ機能付き）"""
        if not self._initialized:
            self.setup_logging()
        
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        
        return self._loggers[name]
    
    def get_agent_logger(self, agent_name: str, module_name: str = None) -> AgentLoggerAdapter:
        """エージェント専用ロガー取得"""
        logger_name = module_name or f"agent.{agent_name}"
        base_logger = self.get_logger(logger_name)
        return AgentLoggerAdapter(base_logger, agent_name)
    
    def add_performance_logger(self, name: str, min_duration: float = 1.0) -> logging.Logger:
        """パフォーマンス専用ロガー追加"""
        logger = self.get_logger(f"performance.{name}")
        
        # パフォーマンスフィルター追加
        perf_filter = PerformanceFilter(min_duration)
        logger.addFilter(perf_filter)
        
        return logger
    
    def cleanup(self) -> None:
        """ログシステムのクリーンアップ"""
        for handler in logging.getLogger().handlers:
            handler.close()
        
        logging.getLogger().handlers.clear()
        self._loggers.clear()
        self._initialized = False


# グローバルログマネージャー
_log_manager: Optional[LoggerManager] = None


def get_log_manager() -> LoggerManager:
    """ログマネージャーのシングルトン取得"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LoggerManager()
    return _log_manager


def setup_logging() -> None:
    """ログシステム初期化（アプリケーション起動時用）"""
    get_log_manager().setup_logging()


def get_logger(name: str) -> logging.Logger:
    """標準ロガー取得"""
    return get_log_manager().get_logger(name)


def get_agent_logger(agent_name: str, module_name: str = None) -> AgentLoggerAdapter:
    """エージェント専用ロガー取得"""
    return get_log_manager().get_agent_logger(agent_name, module_name)


def get_performance_logger(name: str, min_duration: float = 1.0) -> logging.Logger:
    """パフォーマンス専用ロガー取得"""
    return get_log_manager().add_performance_logger(name, min_duration)


# 便利な関数群
def log_function_call(logger: logging.Logger, func_name: str, **kwargs) -> None:
    """関数呼び出しログ"""
    params = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"🔧 Calling {func_name}({params})")


def log_performance(logger: logging.Logger, operation: str, duration: float, **context) -> None:
    """パフォーマンスログ"""
    context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
    logger.info(f"⚡ {operation}: {duration:.3f}s ({context_str})", extra={'duration': duration})


def log_error_with_context(logger: logging.Logger, error: Exception, context: Dict[str, Any]) -> None:
    """コンテキスト付きエラーログ"""
    context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
    logger.error(f"❌ {type(error).__name__}: {error} | Context: {context_str}")


def log_agent_action(agent_name: str, action: str, channel: str = None, **kwargs) -> None:
    """エージェント行動ログ"""
    logger = get_agent_logger(agent_name)
    
    location = f" in #{channel}" if channel else ""
    details = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    details_str = f" ({details})" if details else ""
    
    logger.info(f"🤖 {action}{location}{details_str}")


# システム状態ログ関数
def log_system_startup() -> None:
    """システム起動ログ"""
    logger = get_logger("system.startup")
    logger.info("🚀 Discord Multi-Agent System starting...")
    logger.info(f"🌍 Environment: {get_system_settings().environment.value}")
    logger.info(f"🔧 Clean Architecture v0.2.2")


def log_system_shutdown() -> None:
    """システム終了ログ"""
    logger = get_logger("system.shutdown")
    logger.info("👋 Discord Multi-Agent System shutting down...")


def log_component_status(component: str, status: str, details: str = None) -> None:
    """コンポーネント状態ログ"""
    logger = get_logger(f"system.{component}")
    
    status_emoji = {
        "starting": "🔄",
        "ready": "✅", 
        "error": "❌",
        "stopping": "⏹️"
    }.get(status, "ℹ️")
    
    message = f"{status_emoji} {component.title()}: {status}"
    if details:
        message += f" ({details})"
    
    if status == "error":
        logger.error(message)
    else:
        logger.info(message)


if __name__ == "__main__":
    # ログシステムテスト
    try:
        setup_logging()
        
        # 各種ログのテスト
        logger = get_logger(__name__)
        logger.debug("Debug message test")
        logger.info("Info message test") 
        logger.warning("Warning message test")
        logger.error("Error message test")
        
        # エージェントログテスト
        agent_logger = get_agent_logger("spectra")
        agent_logger.info("Agent message test")
        
        # パフォーマンスログテスト
        perf_logger = get_performance_logger("test")
        log_performance(perf_logger, "test_operation", 0.5, user_count=10)
        
        # 便利関数テスト
        log_agent_action("lynq", "responding", "development", message_length=150)
        log_system_startup()
        
        print("✅ All logging tests passed")
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
    finally:
        get_log_manager().cleanup()