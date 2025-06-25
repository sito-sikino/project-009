"""
Performance Monitoring System - Phase 5 Refactor
パフォーマンス監視システム
"""

import asyncio
import time
import psutil
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import os


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    timestamp: datetime
    operation_name: str
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class BenchmarkTarget:
    """ベンチマーク目標値"""
    operation_name: str
    target_time_ms: float
    description: str
    critical: bool = True  # 重要度（目標未達成時のアラート）


class PerformanceMonitor:
    """
    パフォーマンス監視システム
    
    Features:
    - リアルタイム性能測定
    - ベンチマーク比較
    - メトリクス永続化
    - アラート機能
    - 統計レポート生成
    """
    
    def __init__(self, storage_path: str = "benchmarks/"):
        self.logger = logging.getLogger(__name__)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Phase 5 ベンチマーク目標値
        self.benchmark_targets = {
            "batch_embedding_250": BenchmarkTarget(
                operation_name="batch_embedding_250",
                target_time_ms=30000,  # 30秒
                description="バッチ埋め込み250件処理",
                critical=True
            ),
            "memory_migration_1000": BenchmarkTarget(
                operation_name="memory_migration_1000",
                target_time_ms=60000,  # 60秒
                description="メモリ移行1000件処理",
                critical=True
            ),
            "similarity_search": BenchmarkTarget(
                operation_name="similarity_search",
                target_time_ms=500,    # 500ms
                description="類似検索単一クエリ",
                critical=True
            ),
            "integrated_workflow": BenchmarkTarget(
                operation_name="integrated_workflow",
                target_time_ms=600000, # 10分
                description="統合ワークフロー全体",
                critical=True
            ),
            "fail_fast_response": BenchmarkTarget(
                operation_name="fail_fast_response",
                target_time_ms=100,    # 100ms
                description="Fail-fastエラー検出",
                critical=True
            ),
            "memory_usage_check": BenchmarkTarget(
                operation_name="memory_usage_check",
                target_time_ms=1536 * 1024 * 1024,  # 1.5GB (bytes)
                description="メモリ使用量制限",
                critical=True
            )
        }
        
        # メトリクス履歴
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = int(os.getenv('PERFORMANCE_HISTORY_SIZE', '1000'))
    
    async def measure_performance(self, operation_name: str, coro_or_func, *args, **kwargs):
        """
        コルーチンまたは関数の性能測定
        
        Args:
            operation_name: 操作名
            coro_or_func: 測定対象のコルーチンまたは関数
            *args, **kwargs: 関数の引数
            
        Returns:
            (result, metrics): 実行結果とメトリクス
        """
        # 初期リソース測定
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        start_time = time.perf_counter()
        start_timestamp = datetime.now()
        
        error_message = None
        result = None
        success = False
        
        try:
            # 実行
            if asyncio.iscoroutinefunction(coro_or_func):
                result = await coro_or_func(*args, **kwargs)
            else:
                result = coro_or_func(*args, **kwargs)
            success = True
            
        except Exception as e:
            error_message = str(e)
            self.logger.warning(f"Performance measurement error in {operation_name}: {e}")
            
        finally:
            # 終了リソース測定
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # ms
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            final_cpu = process.cpu_percent()
            
            # メトリクス作成
            metrics = PerformanceMetrics(
                timestamp=start_timestamp,
                operation_name=operation_name,
                execution_time_ms=execution_time,
                memory_usage_mb=final_memory,
                cpu_usage_percent=final_cpu,
                success=success,
                error_message=error_message,
                additional_data={
                    'initial_memory_mb': initial_memory,
                    'memory_delta_mb': final_memory - initial_memory,
                    'cpu_delta_percent': final_cpu - initial_cpu
                }
            )
            
            # 履歴に追加
            self.add_metrics(metrics)
            
            # ベンチマーク評価
            self.evaluate_benchmark(metrics)
            
        return result, metrics
    
    def add_metrics(self, metrics: PerformanceMetrics):
        """メトリクス履歴に追加"""
        self.metrics_history.append(metrics)
        
        # 履歴サイズ制限
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    def evaluate_benchmark(self, metrics: PerformanceMetrics):
        """ベンチマーク評価とアラート"""
        target = self.benchmark_targets.get(metrics.operation_name)
        if not target:
            return
        
        # メモリ使用量は特別扱い
        if metrics.operation_name == "memory_usage_check":
            memory_bytes = metrics.memory_usage_mb * 1024 * 1024
            if memory_bytes > target.target_time_ms:  # target_time_msをメモリ制限として使用
                self.logger.warning(
                    f"🔴 Memory usage exceeded target: "
                    f"{metrics.memory_usage_mb:.1f}MB > {target.target_time_ms/1024/1024:.1f}MB"
                )
            else:
                self.logger.info(
                    f"✅ Memory usage within target: "
                    f"{metrics.memory_usage_mb:.1f}MB < {target.target_time_ms/1024/1024:.1f}MB"
                )
            return
        
        # 実行時間評価
        if metrics.execution_time_ms > target.target_time_ms:
            severity = "🔴 CRITICAL" if target.critical else "🟡 WARNING"
            self.logger.warning(
                f"{severity} Performance target missed: {metrics.operation_name} "
                f"{metrics.execution_time_ms:.1f}ms > {target.target_time_ms:.1f}ms target"
            )
        else:
            self.logger.info(
                f"✅ Performance target achieved: {metrics.operation_name} "
                f"{metrics.execution_time_ms:.1f}ms < {target.target_time_ms:.1f}ms target"
            )
    
    def get_performance_report(self, 
                             operation_name: Optional[str] = None,
                             hours: int = 24) -> Dict[str, Any]:
        """性能レポート生成"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # フィルタリング
        filtered_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time and (not operation_name or m.operation_name == operation_name)
        ]
        
        if not filtered_metrics:
            return {"message": "No metrics found for the specified criteria"}
        
        # 統計計算
        execution_times = [m.execution_time_ms for m in filtered_metrics if m.success]
        success_count = sum(1 for m in filtered_metrics if m.success)
        total_count = len(filtered_metrics)
        
        report = {
            "summary": {
                "total_operations": total_count,
                "successful_operations": success_count,
                "success_rate_percent": (success_count / total_count * 100) if total_count > 0 else 0,
                "time_range_hours": hours
            }
        }
        
        if execution_times:
            import statistics
            report["performance"] = {
                "avg_execution_time_ms": statistics.mean(execution_times),
                "median_execution_time_ms": statistics.median(execution_times),
                "min_execution_time_ms": min(execution_times),
                "max_execution_time_ms": max(execution_times),
                "std_deviation_ms": statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            }
        
        # ベンチマーク比較
        if operation_name and operation_name in self.benchmark_targets:
            target = self.benchmark_targets[operation_name]
            if execution_times:
                avg_time = statistics.mean(execution_times)
                report["benchmark"] = {
                    "target_ms": target.target_time_ms,
                    "current_avg_ms": avg_time,
                    "performance_ratio": avg_time / target.target_time_ms,
                    "target_achieved": avg_time <= target.target_time_ms
                }
        
        return report
    
    def save_benchmark_results(self, filename: Optional[str] = None):
        """ベンチマーク結果を永続化"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        filepath = self.storage_path / filename
        
        # 全操作のレポート生成
        full_report = {
            "timestamp": datetime.now().isoformat(),
            "benchmark_targets": {name: asdict(target) for name, target in self.benchmark_targets.items()},
            "reports": {}
        }
        
        for operation_name in self.benchmark_targets.keys():
            full_report["reports"][operation_name] = self.get_performance_report(operation_name)
        
        # ファイルに保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📊 Benchmark results saved to {filepath}")
        return str(filepath)
    
    def load_benchmark_results(self, filename: str) -> Dict[str, Any]:
        """保存されたベンチマーク結果を読み込み"""
        filepath = self.storage_path / filename
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Benchmark file not found: {filepath}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in benchmark file: {e}")
            return {}


# グローバルインスタンス
_global_monitor: Optional[PerformanceMonitor] = None

def get_performance_monitor() -> PerformanceMonitor:
    """グローバルパフォーマンスモニター取得"""
    global _global_monitor
    if _global_monitor is None:
        storage_path = os.getenv('BENCHMARK_RESULTS_PATH', './benchmarks/')
        _global_monitor = PerformanceMonitor(storage_path)
    return _global_monitor


# デコレータ関数
def monitor_performance(operation_name: str):
    """パフォーマンス監視デコレータ"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            result, metrics = await monitor.measure_performance(operation_name, func, *args, **kwargs)
            return result
        return wrapper
    return decorator