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
            # 非同期タスクを同期実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            health_results = loop.run_until_complete(
                performance_monitor.health_checker.run_all_checks()
            )
            overall_status = performance_monitor.health_checker.get_overall_status()
            
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
                    name: result.status 
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 重要なコンポーネントのみチェック
            critical_checks = ['redis', 'postgres', 'discord']
            results = {}
            
            for check_name in critical_checks:
                if check_name in performance_monitor.health_checker.checks:
                    result = loop.run_until_complete(
                        performance_monitor.health_checker.run_check(check_name)
                    )
                    results[check_name] = result.status
            
            # 全ての重要コンポーネントが健全か
            all_ready = all(
                status == "healthy" 
                for status in results.values()
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            performance_report = loop.run_until_complete(
                performance_monitor.get_performance_report()
            )
            
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
        failure_threshold=int(os.getenv('CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5)),
        recovery_timeout=int(os.getenv('CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60))
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