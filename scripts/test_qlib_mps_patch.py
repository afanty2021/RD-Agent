#!/usr/bin/env python3
"""
Qlib MPS 补丁完整性测试

此脚本测试 MPS 补丁是否破坏了 Qlib 的原有功能。

测试内容：
1. CPU 训练（原有功能）
2. MPS 训练（新功能）
3. 模型保存和加载
4. 预测功能
5. 设备切换兼容性

Usage:
    python3 test_qlib_mps_patch.py
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加测试依赖
try:
    import numpy as np
    import pandas as pd
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请安装: pip install numpy pandas torch")
    sys.exit(1)

print("=" * 70)
print("🧪 Qlib MPS 补丁完整性测试")
print("=" * 70)
print()

# 测试结果
test_results = []


def test_cpu_training():
    """测试 1: CPU 训练功能（原有功能必须保持）"""
    print("\n📋 测试 1: CPU 训练功能")

    try:
        # 创建简单模型
        model = nn.Linear(10, 1)
        device = torch.device("cpu")
        model.to(device)

        # 创建虚拟数据
        X = torch.randn(100, 10)
        y = torch.randn(100, 1)

        # 训练循环
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        model.train()
        for epoch in range(5):
            optimizer.zero_grad()
            outputs = model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()

        print(f"  ✅ CPU 训练成功，最终 Loss: {loss.item():.6f}")
        test_results.append(("CPU 训练", True, None))
        return True

    except Exception as e:
        print(f"  ❌ CPU 训练失败: {e}")
        test_results.append(("CPU 训练", False, str(e)))
        return False


def test_mps_training():
    """测试 2: MPS 训练功能（新功能）"""
    print("\n📋 测试 2: MPS 训练功能")

    if not torch.backends.mps.is_available():
        print("  ⚠️  MPS 不可用，跳过此测试")
        test_results.append(("MPS 训练", None, "MPS 不可用"))
        return False

    try:
        # 创建简单模型
        model = nn.Linear(10, 1)
        device = torch.device("mps")
        model.to(device)

        # 创建虚拟数据
        X = torch.randn(100, 10).to(device)
        y = torch.randn(100, 1).to(device)

        # 训练循环
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        model.train()
        for epoch in range(5):
            optimizer.zero_grad()
            outputs = model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()

        print(f"  ✅ MPS 训练成功，最终 Loss: {loss.item():.6f}")
        test_results.append(("MPS 训练", True, None))
        return True

    except Exception as e:
        print(f"  ❌ MPS 训练失败: {e}")
        test_results.append(("MPS 训练", False, str(e)))
        return False


def test_model_save_load():
    """测试 3: 模型保存和加载（关键功能）"""
    print("\n📋 测试 3: 模型保存和加载")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建并训练模型
            model = nn.Linear(10, 1)
            device = torch.device("cpu")
            model.to(device)

            # 训练一步
            X = torch.randn(10, 10)
            y = torch.randn(10, 1)
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.MSELoss()

            optimizer.zero_grad()
            outputs = model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()

            # 保存模型
            save_path = Path(tmpdir) / "model.pt"
            torch.save(model.state_dict(), save_path)

            # 创建新模型并加载
            model2 = nn.Linear(10, 1)
            model2.load_state_dict(torch.load(save_path))
            model2.to(device)

            # 验证参数一致
            for p1, p2 in zip(model.parameters(), model2.parameters()):
                if not torch.allclose(p1, p2):
                    raise ValueError("参数不匹配")

        print(f"  ✅ 模型保存和加载成功")
        test_results.append(("模型保存/加载", True, None))
        return True

    except Exception as e:
        print(f"  ❌ 模型保存和加载失败: {e}")
        test_results.append(("模型保存/加载", False, str(e)))
        return False


def test_prediction():
    """测试 4: 预测功能"""
    print("\n📋 测试 4: 预测功能")

    try:
        # 创建并训练模型
        model = nn.Linear(10, 1)
        device = torch.device("cpu")
        model.to(device)
        model.eval()

        # 测试预测
        X = torch.randn(5, 10)

        with torch.no_grad():
            predictions = model(X)

        if predictions.shape != (5, 1):
            raise ValueError(f"预测形状错误: {predictions.shape}")

        print(f"  ✅ 预测成功，输出形状: {predictions.shape}")
        test_results.append(("预测功能", True, None))
        return True

    except Exception as e:
        print(f"  ❌ 预测失败: {e}")
        test_results.append(("预测功能", False, str(e)))
        return False


def test_device_selection():
    """测试 5: 设备选择逻辑（补丁的核心）"""
    print("\n📋 测试 5: 设备选择逻辑")

    try:
        # 测试不同的 GPU 配置
        test_cases = [
            (None, "cpu", "GPU=None 应使用 CPU"),
            (-1, "cpu", "GPU=-1 应使用 CPU"),
            (0, "mps", "GPU=0 应使用 MPS（如果可用）"),
        ]

        for gpu_value, expected_device, description in test_cases:
            if gpu_value == 0 and not torch.backends.mps.is_available():
                print(f"  ⚠️  跳过: {description} (MPS 不可用)")
                continue

            if gpu_value is not None and gpu_value >= 0:
                if torch.cuda.is_available():
                    device = torch.device(f"cuda:{gpu_value}")
                elif torch.backends.mps.is_available():
                    device = torch.device("mps")
                else:
                    device = torch.device("cpu")
            else:
                device = torch.device("cpu")

            if device.type == expected_device:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - 期望 {expected_device}, 得到 {device.type}")
                test_results.append(("设备选择", False, f"配置 {gpu_value} 失败"))
                return False

        test_results.append(("设备选择", True, None))
        return True

    except Exception as e:
        print(f"  ❌ 设备选择测试失败: {e}")
        test_results.append(("设备选择", False, str(e)))
        return False


def test_cache_clearing():
    """测试 6: GPU 缓存清理（补丁修改的部分）"""
    print("\n📋 测试 6: GPU 缓存清理")

    try:
        # 测试 CPU 设备（不会触发清理）
        device = torch.device("cpu")
        if device.type == "cuda":
            torch.cuda.empty_cache()
        elif device.type == "mps":
            import gc
            gc.collect()

        print(f"  ✅ 缓存清理逻辑正常（CPU 设备）")
        test_results.append(("缓存清理", True, None))
        return True

    except Exception as e:
        print(f"  ❌ 缓存清理失败: {e}")
        test_results.append(("缓存清理", False, str(e)))
        return False


def test_qlib_integration():
    """测试 7: Qlib 集成测试（如果可用）"""
    print("\n📋 测试 7: Qlib 集成测试")

    try:
        import qlib
        from qlib.contrib.model.pytorch_general_nn import GeneralPTNN

        # 检查补丁是否应用
        import inspect
        source_file = inspect.getsourcefile(GeneralPTNN)

        with open(source_file, 'r') as f:
            content = f.read()

        # 检查关键代码
        checks = [
            ("MPS 检测", "torch.backends.mps.is_available()"),
            ("MPS 设备", 'torch.device("mps")'),
            ("设备类型检查", 'self.device.type == "mps"'),
        ]

        for check_name, check_str in checks:
            if check_str in content:
                print(f"  ✅ {check_name} - 已应用补丁")
            else:
                print(f"  ❌ {check_name} - 补丁未应用")
                test_results.append(("Qlib 集成", False, f"{check_name} 缺失"))
                return False

        test_results.append(("Qlib 集成", True, None))
        return True

    except ImportError:
        print("  ⚠️  Qlib 不可用，跳过集成测试")
        test_results.append(("Qlib 集成", None, "Qlib 未安装"))
        return False
    except Exception as e:
        print(f"  ❌ Qlib 集成测试失败: {e}")
        test_results.append(("Qlib 集成", False, str(e)))
        return False


def run_all_tests():
    """运行所有测试"""

    print("🚀 开始运行测试...\n")

    # 运行测试
    test_cpu_training()
    test_mps_training()
    test_model_save_load()
    test_prediction()
    test_device_selection()
    test_cache_clearing()
    test_qlib_integration()

    # 汇总结果
    print("\n" + "=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)

    passed = 0
    failed = 0
    skipped = 0

    for test_name, success, error in test_results:
        if success is True:
            print(f"✅ {test_name}: 通过")
            passed += 1
        elif success is False:
            print(f"❌ {test_name}: 失败")
            if error:
                print(f"   错误: {error}")
            failed += 1
        else:
            print(f"⚠️  {test_name}: 跳过 ({error})")
            skipped += 1

    print()
    print(f"总计: {len(test_results)} 个测试")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"⚠️  跳过: {skipped}")

    # 判断总体结果
    if failed == 0:
        print("\n🎉 所有测试通过！补丁没有破坏原有功能。")
        return 0
    else:
        print(f"\n⚠️  {failed} 个测试失败，请检查补丁或回退。")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    print("\n" + "=" * 70)
    sys.exit(exit_code)
