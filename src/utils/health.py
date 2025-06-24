"""
Health Check API for Production Monitoring
本番環境監視用ヘルスチェック API
"""

import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from urllib.parse import urlparse, parse_qs
import logging

from .monitoring import performance_monitor


def _parse_int_env(env_var: str, default: int) -> int:
    """環境変数を int に解析（コメント対応）"""
    value = os.getenv(env_var, str(default))
    if isinstance(value, str):
        # コメント部分を除去
        value = value.split('#')[0].strip()
    try:
        return int(value)
    except (ValueError, TypeError):
        logging.getLogger(__name__).warning(f"Invalid {env_var} value: {value}, using default: {default}")
        return default


class HealthCheckHandler(BaseHTTPRequestHandler):
    """ヘルスチェック HTTP ハンドラー"""
    
    def __init__(self, memory_system=None, discord_clients=None, *args, **kwargs):
        self.memory_system = memory_system
        self.discord_clients = discord_clients
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """GET リクエスト処理"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        try:
            if path == '/health':
                self._handle_health_check()
            elif path == '/health/live':
                self._handle_liveness_check()
            elif path == '/health/ready':
                self._handle_readiness_check()
            elif path == '/metrics':
                self._handle_metrics()
            elif path == '/status':
                self._handle_detailed_status()
            else:
                self._send_error(404, "Not Found")
        except Exception as e:
            logging.error(f"Health check API error: {e}")
            self._send_error(500, "Internal Server Error")
    
    def _handle_health_check(self):
        """基本ヘルスチェック"""
        try:
            # 既存のイベントループを使用（新しいループを作成しない）
            try:
                # 現在のイベントループを取得
                loop = asyncio.get_running_loop()
                # asyncio.create_task を使用してタスクを作成
                health_task = asyncio.create_task(
                    performance_monitor.health_checker.run_all_checks()
                )
                # タスクが完了するまで待機（ただし、これは同期コンテキストなので実際には実行されない）
                # フォールバック: 同期的な健康状態チェック
                overall_status = performance_monitor.health_checker.get_overall_status()
                health_results = performance_monitor.health_checker.last_results
            except RuntimeError:
                # イベントループが実行されていない場合のフォールバック
                overall_status = performance_monitor.health_checker.get_overall_status()
                health_results = performance_monitor.health_checker.last_results
            
            # HTTP ステータス決定
            if overall_status["status"] == "healthy":
                status_code = 200
            elif overall_status["status"] == "degraded":
                status_code = 200  # 部分的に動作
            else:
                status_code = 503  # Service Unavailable
            
            response = {
                "status": overall_status["status"],
                "timestamp": datetime.now().isoformat(),
                "version": os.getenv("APP_VERSION", "unknown"),
                "components": {
                    name: result.to_dict()
                    for name, result in health_results.items()
                }
            }
            
            self._send_json_response(response, status_code)
            
        except Exception as e:
            self._send_error(500, f"Health check failed: {str(e)}")
    
    def _handle_liveness_check(self):
        """Liveness Probe（Kubernetes用）"""
        # アプリケーションが生きているかの基本チェック
        try:
            response = {
                "status": "alive",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": self._get_uptime()
            }
            self._send_json_response(response, 200)
        except Exception as e:
            self._send_error(500, f"Liveness check failed: {str(e)}")
    
    def _handle_readiness_check(self):
        """Readiness Probe（Kubernetes用）"""
        # アプリケーションがトラフィックを受け取れるかチェック
        try:
            # 既存のイベントループを使用（新しいループを作成しない）
            # 重要なコンポーネントのみチェック
            critical_checks = ['redis', 'postgres', 'discord']
            results = {}
            
            # 直前の結果を使用（リアルタイムチェックは避ける）
            for check_name in critical_checks:
                if check_name in performance_monitor.health_checker.last_results:
                    results[check_name] = performance_monitor.health_checker.last_results[check_name].to_dict()
                else:
                    # フォールバック: 基本的な状態チェック
                    results[check_name] = {
                        "component": check_name,
                        "status": "unknown",
                        "last_check": datetime.now().isoformat(),
                        "response_time_ms": 0.0,
                        "error_count": 0,
                        "details": {"info": "No recent check available"}
                    }
            
            # 全ての重要コンポーネントが健全か
            all_ready = all(
                status_dict["status"] == "healthy" 
                for status_dict in results.values()
            )
            
            response = {
                "ready": all_ready,
                "components": results,
                "timestamp": datetime.now().isoformat()
            }
            
            status_code = 200 if all_ready else 503
            self._send_json_response(response, status_code)
            
        except Exception as e:
            self._send_error(503, f"Readiness check failed: {str(e)}")
    
    def _handle_metrics(self):
        """Prometheus メトリクス出力"""
        try:
            metrics_text = performance_monitor.metrics.get_metrics()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(metrics_text.encode('utf-8'))
            
        except Exception as e:
            self._send_error(500, f"Metrics generation failed: {str(e)}")
    
    def _handle_detailed_status(self):
        """詳細ステータス情報"""
        try:
            # 既存のイベントループを使用（新しいループを作成しない）
            # 最新の結果を基にパフォーマンスレポートを同期的に構築
            try:
                # 現在のイベントループからタスクを作成（ただし、実際には同期的に結果を返す）
                overall_status = performance_monitor.health_checker.get_overall_status()
                circuit_breaker_status = {
                    name: {
                        "state": cb.state.value,
                        "failure_count": cb.failure_count,
                        "last_failure": cb.last_failure_time
                    }
                    for name, cb in performance_monitor.circuit_breakers.items()
                }
                
                performance_report = {
                    "timestamp": datetime.now().isoformat(),
                    "overall_health": overall_status,
                    "circuit_breakers": circuit_breaker_status,
                    "thresholds": performance_monitor.thresholds,
                    "metrics_available": performance_monitor.metrics is not None
                }
            except Exception as sync_error:
                # フォールバック: 基本情報のみ
                performance_report = {
                    "timestamp": datetime.now().isoformat(),
                    "overall_health": {"status": "unknown", "components": {}},
                    "circuit_breakers": {},
                    "thresholds": getattr(performance_monitor, 'thresholds', {}),
                    "metrics_available": False,
                    "sync_error": str(sync_error)
                }
            
            # 追加システム情報
            system_info = {
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                "version": os.getenv("APP_VERSION", "unknown"),
                "python_version": self._get_python_version(),
                "uptime_seconds": self._get_uptime(),
                "memory_usage": self._get_memory_usage(),
                "configuration": {
                    "hot_memory_target_ms": os.getenv("HOT_MEMORY_TARGET_MS", "100"),
                    "cold_memory_target_ms": os.getenv("COLD_MEMORY_TARGET_MS", "3000"),
                    "gemini_rate_limit": os.getenv("GEMINI_API_RATE_LIMIT", "0.25")
                }
            }
            
            response = {
                **performance_report,
                "system": system_info
            }
            
            self._send_json_response(response, 200)
            
        except Exception as e:
            self._send_error(500, f"Status check failed: {str(e)}")
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """JSON レスポンス送信"""
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(json_data.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def _send_error(self, status_code: int, message: str):
        """エラーレスポンス送信"""
        error_response = {
            "error": message,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
        self._send_json_response(error_response, status_code)
    
    def _get_uptime(self) -> float:
        """アップタイム取得（秒）"""
        # 実装を簡易化：プロセス開始時間を基準
        try:
            import psutil
            process = psutil.Process()
            return process.cpu_times().user + process.cpu_times().system
        except:
            return 0.0
    
    def _get_python_version(self) -> str:
        """Python バージョン取得"""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """メモリ使用量取得"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "percent": round(process.memory_percent(), 2)
            }
        except:
            return {"error": "psutil not available"}
    
    def log_message(self, format, *args):
        """ログメッセージを抑制（必要に応じて有効化）"""
        # HTTP アクセスログを抑制
        pass


class HealthCheckServer:
    """ヘルスチェック HTTP サーバー"""
    
    def __init__(self, 
                 port: int = 8000,
                 memory_system=None,
                 discord_clients=None):
        self.port = port
        self.memory_system = memory_system
        self.discord_clients = discord_clients
        self.server = None
        self.server_thread = None
        self.logger = logging.getLogger(__name__)
    
    def create_handler(self):
        """ハンドラークラス作成"""
        memory_system = self.memory_system
        discord_clients = self.discord_clients
        
        class Handler(HealthCheckHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(memory_system, discord_clients, *args, **kwargs)
        
        return Handler
    
    def start(self):
        """サーバー開始"""
        try:
            handler_class = self.create_handler()
            self.server = HTTPServer(('0.0.0.0', self.port), handler_class)
            
            # 別スレッドでサーバー実行
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            self.logger.info(f"Health check server started on port {self.port}")
            self.logger.info(f"Health endpoints:")
            self.logger.info(f"  - GET /health        - Overall health")
            self.logger.info(f"  - GET /health/live   - Liveness probe")
            self.logger.info(f"  - GET /health/ready  - Readiness probe")
            self.logger.info(f"  - GET /metrics       - Prometheus metrics")
            self.logger.info(f"  - GET /status        - Detailed status")
            
        except Exception as e:
            self.logger.error(f"Failed to start health check server: {e}")
            raise
    
    def stop(self):
        """サーバー停止"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.logger.info("Health check server stopped")
    
    def is_running(self) -> bool:
        """サーバー実行状態確認"""
        return (
            self.server is not None and 
            self.server_thread is not None and 
            self.server_thread.is_alive()
        )


# ヘルスチェック用のユーティリティ関数
async def setup_health_monitoring(memory_system, discord_clients, port: int = 8000):
    """
    ヘルスチェック監視セットアップ
    
    Args:
        memory_system: Memory System インスタンス
        discord_clients: Discord クライアントリスト
        port: ヘルスチェック API ポート
    
    Returns:
        HealthCheckServer: ヘルスチェックサーバー
    """
    # パフォーマンス監視のヘルスチェック設定
    performance_monitor.setup_health_checks(memory_system, discord_clients)
    
    # Circuit Breaker 設定
    performance_monitor.create_circuit_breaker(
        "memory_operations",
        failure_threshold=_parse_int_env('CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5),
        recovery_timeout=_parse_int_env('CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60)
    )
    
    performance_monitor.create_circuit_breaker(
        "gemini_api",
        failure_threshold=3,  # API系は厳しめ
        recovery_timeout=30
    )
    
    # ヘルスチェックサーバー作成・開始
    health_server = HealthCheckServer(port, memory_system, discord_clients)
    health_server.start()
    
    return health_server


# Docker ヘルスチェック用コマンド
def docker_health_check():
    """Docker HEALTHCHECK 用エントリーポイント"""
    import urllib.request
    import sys
    
    try:
        port = os.getenv('HEALTH_CHECK_PORT', '8000')
        url = f"http://localhost:{port}/health/ready"
        
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status == 200:
                print("Health check passed")
                sys.exit(0)
            else:
                print(f"Health check failed with status {response.status}")
                sys.exit(1)
                
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Docker ヘルスチェック実行
    docker_health_check()