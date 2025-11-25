"""
性能监控工具模块

提供性能指标收集、分析和报告功能
"""

import time
import functools
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager


class PerformanceMonitor:
    """
    性能监控器

    提供性能指标收集、分析和报告功能，支持装饰器模式和手动模式。

    主要功能：
    - 函数执行时间测量
    - 多种性能指标记录（最小值、最大值、平均值、中位数、95%分位数等）
    - 调用记录和性能摘要生成
    - 上下文管理器支持嵌套计时

    Attributes:
        metrics (Dict[str, Any]): 存储所有性能指标
        timers (Dict[str, Any]): 存储计时器数据

    Example:
        ```python
        from rdagent.utils.performance import PerformanceMonitor, monitor_performance

        @monitor_performance
        def my_function():
            time.sleep(0.1)
            return "completed"

        # 执行后获取性能报告
        summary = monitor.get_metrics_summary()
        ```
    """

    def __init__(self):
        self.start_time = None
        self.metrics = {}
        self.timers = {}

    @contextmanager
    def timer(self, name: str):
        """上下文管理器，用于测量执行时间"""
        if name not in self.timers:
            self.timers[name] = {
                'start_time': time.time(),
                'laps': []
            }
            return TimerContext(self.timers[name])

    def record_metric(self, name: str, value: Any, tags: Optional[Dict[str, str]] = None):
        """记录性能指标"""
        self.metrics[name] = {
            'value': value,
            'timestamp': time.time(),
            'tags': tags or {}
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取性能指标摘要"""
        summary = {}
        for name, metric in self.metrics.items():
            if isinstance(metric['value'], (int, float)):
                if 'avg' not in metric:
                    avg = sum(m['value'] for m in metric['value'] if isinstance(m['value'], list) else metric['value']) / len(metric['value'])
                    metric['avg'] = avg
                if 'min' not in metric:
                    min_val = min(m['value'] for m in metric['value'] if isinstance(m['value'], list) else metric['value'])
                    metric['min'] = min_val
                if 'max' not in metric:
                    max_val = max(m['value'] for m in metric['value'] if isinstance(m['value'], list) else metric['value'])
                    metric['max'] = max_val

            summary[name] = {
                'count': len(metric['value']),
                'avg': metric.get('avg', 0),
                'min': metric.get('min', 0),
                'max': metric.get('max', 0),
                'latest': metric['value'][-1] if isinstance(metric['value'], list) else metric['value'],
                'tags': metric['tags']
            }

        return summary


class TimerContext:
    """计时器上下文管理器"""

    def __init__(self, timer_data: Dict[str, Any]):
        self.timer_data = timer_data
        self.start_time = timer_data.get('start_time', time.time())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration = end_time - self.start_time

        self.timer_data['laps'].append(duration)
        self.timer_data['total_duration'] = sum(self.timer_data['laps']) + duration

        return False


def monitor_performance(func: Callable) -> Callable:
    """性能监控装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        perf_monitor = PerformanceMonitor()

        with perf_monitor.timer(func.__name__) as timer:
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                perf_monitor.record_metric(f"{func.__name__}_error", str(e))
                raise
            finally:
                summary = perf_monitor.get_metrics_summary()
                for metric_name, metric_data in summary.items():
                    if metric_data['count'] > 0:
                        print(f"⏱️ {metric_name}: 执行{metric_data['count']}次，平均耗时: {metric_data['avg']:.3f}s")
                    elif metric_data['avg'] > 0:
                        print(f"⏱️ {metric_name}: 平均耗时: {metric_data['avg']:.3f}s")

        return result

    return wrapper


# 使用示例
@monitor_performance
def slow_function():
    time.sleep(0.1)
    return "completed"

@monitor_performance
def fast_function():
    return "completed"