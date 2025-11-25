"""
基准测试工具模块

提供性能基准测试和比较功能
"""

import time
import statistics
from typing import Dict, List, Any, Callable
from contextlib import contextmanager


class BenchmarkRunner:
    """基准测试运行器"""

    def __init__(self):
        self.results = []

    def run_benchmark(self, func: Callable, iterations: int = 100) -> Dict[str, Any]:
        """运行基准测试"""
        times = []

        for i in range(iterations):
            start_time = time.perf_counter()
            result = func()
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            times.append(execution_time)

        return {
            'function': func.__name__,
            'iterations': iterations,
            'results': {
                'min': min(times),
                'max': max(times),
                'avg': statistics.mean(times),
                'median': statistics.median(times),
                'p95': statistics.quantiles(times, 0.95)[0],
                'p99': statistics.quantiles(times, 0.99)[0],
                'std': statistics.stdev(times)
            }
        }

    def compare_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """比较多个基准测试结果"""
        if len(results) < 2:
            return {'status': 'insufficient_data', 'message': '需要至少2个结果进行比较'}

        baseline = results[0]
        improvements = []

        for i, result in enumerate(results[1:], 1):
            improvement = {}

            for metric in ['min', 'max', 'avg', 'median', 'p95', 'p99', 'std']:
                if result['results'][metric] < baseline['results'][metric]:
                    improvement[metric] = {
                        'baseline': baseline['results'][metric],
                        'current': result['results'][metric],
                        'improvement': baseline['results'][metric] - result['results'][metric],
                        'improvement_pct': ((baseline['results'][metric] - result['results'][metric]) / baseline['results'][metric]) * 100
                    }

            if improvement:
                improvements.append(improvement)

        return {
            'status': 'success',
            'baseline': baseline,
            'comparisons': results[1:],
            'improvements': improvements
        }


def run_quick_benchmark():
    """运行快速基准测试"""
    runner = BenchmarkRunner()

    # 测试快速函数
    fast_results = runner.run_benchmark(fast_function, 50)
    print("🚀 快速函数基准测试:")
    print(f"  平均耗时: {fast_results['results']['avg']:.4f}s")
    print(f"  95%分位数: {fast_results['results']['p95']:.4f}s")

    # 测试慢速函数
    slow_results = runner.run_benchmark(slow_function, 50)
    print("\n🐌 慢速函数基准测试:")
    print(f"  平均耗时: {slow_results['results']['avg']:.4f}s")
    print(f"  95%分位数: {slow_results['results']['p95']:.4f}s")

    # 比较结果
    comparison = runner.compare_results([fast_results, slow_results])
    if comparison['status'] == 'success':
        print("\n📊 性能对比:")
        for improvement in comparison['improvements']:
            metric_name = improvement.get('metric', 'unknown')
            baseline_val = improvement.get('baseline', 0)
            current_val = improvement.get('current', 0)
            improvement_pct = improvement.get('improvement_pct', 0)

            print(f"  {metric_name}: {baseline_val:.4f}s → {current_val:.4f}s")
            if improvement_pct > 0:
                print(f"  改善: {improvement_pct:.1f}%")
            else:
                print(f"  恶化: {improvement_pct:.1f}%")


if __name__ == "__main__":
    run_quick_benchmark()