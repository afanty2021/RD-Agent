"""
性能监控和基准测试模块测试
"""

import pytest
from rdagent.utils.performance import PerformanceMonitor, monitor_performance
from rdagent.utils.benchmark import BenchmarkRunner


def test_performance_monitor_basic():
    """测试性能监控基本功能"""
    monitor = PerformanceMonitor()

    @monitor_performance
    def test_function():
        time.sleep(0.1)
        return "test_completed"

    @monitor_performance
    def test_function_with_error():
        raise ValueError("测试错误")

    # 执行测试
    with pytest.raises(ValueError):
        test_function_with_error()


def test_benchmark_runner_basic():
    """测试基准运行器基本功能"""
    runner = BenchmarkRunner()

    # 测试基准测试功能
    results = runner.run_benchmark(test_function, 10)
    assert results['status'] == 'success'
    assert 'results' in results
    assert 'avg' in results['results']
    assert isinstance(results['results']['avg'], (int, float))


def test_benchmark_runner_comparison():
    """测试基准比较功能"""
    runner = BenchmarkRunner()

    # 运行快速和慢速测试
    fast_results = runner.run_benchmark(test_function, 50)
    slow_results = runner.run_benchmark(slow_function, 50)

    # 比较结果
    comparison = runner.compare_results([fast_results, slow_results])
    assert comparison['status'] == 'success'
    assert 'improvements' in comparison


if __name__ == "__main__":
    test_performance_monitor_basic()
    test_benchmark_runner_basic()
    test_benchmark_runner_comparison()

    print("\n🧪 所有性能测试通过!")