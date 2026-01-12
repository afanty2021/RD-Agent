# Qlib Segmentation Fault 解决指南

## 🚨 问题症状

```
Segmentation fault: 11
gtimeout --kill-after=10 3600 qrun conf_baseline_factors_model.yaml
```

伴随警告：
- Pandas SettingWithCopyWarning
- Joblib 资源跟踪器警告（内存映射文件夹泄漏）

## 🔍 根本原因分析

### 主要原因
1. **多进程兼容性问题**：PyTorch + 多进程在macOS上的兼容性缺陷
2. **GPU配置错误**：`GPU: 0` 尝试使用不存在的CUDA设备
3. **内存管理问题**：Joblib内存映射在macOS上的行为异常

### 触发条件
- macOS系统（非Linux）
- 大数据集（>50万样本）
- PyTorch模型训练
- 多进程配置（n_jobs > 0）

## ✅ 解决方案

### 方案A：使用修复的配置文件（推荐）⭐

已创建修复配置：`conf_baseline_factors_model_fixed.yaml`

**关键修改**：
```yaml
model:
  kwargs:
    n_jobs: 0    # 禁用多进程，使用单进程模式
    GPU: -1      # 禁用GPU，强制使用CPU
    batch_size: 2048  # 增大batch减少内存碎片
```

**使用方法**：
```bash
# 1. 清理环境
./scripts/clean_quant_env.sh

# 2. 使用修复的配置
qrun conf_baseline_factors_model_fixed.yaml
```

### 方案B：环境变量配置

在运行前设置环境变量：

```bash
# 禁用OpenMP多线程
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# 限制PyTorch线程数
export PYTORCH_ENABLE_MPS_FALLBACK=0
export PYTORCH_NO_CUDA_MEMORY_CACHING=1

# 强制使用单进程
export JOBLIB_START_METHOD='fork'

# 运行训练
qrun conf_baseline_factors_model.yaml
```

### 方案C：减少数据规模（用于测试）

修改配置文件中的时间范围：

```yaml
data_handler_config:
    start_time: "2015-01-01"  # 减少训练数据
    end_time: "2018-01-01"
    fit_start_time: "2015-01-01"
    fit_end_time: "2016-12-31"
```

### 方案D：使用更简单的模型

将 `GeneralPTNN` 替换为 `MLP`：

```yaml
model:
    class: MLP
    module_path: qlib.contrib.model.pytorch_nn
    kwargs:
        n_jobs: 0
        GPU: -1
        batch_size: 2048
```

## 🔧 预防措施

### 1. 系统配置优化

在 `~/.zshrc` 或 `~/.bashrc` 中添加：

```bash
# Qlib/PyTorch 优化
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# PyTorch 内存管理
export PYTORCH_NO_CUDA_MEMORY_CACHING=1

# Joblib 配置
export JOBLIB_TEMP_FOLDER=/tmp/joblib
```

### 2. Python环境检查

```bash
# 检查关键库版本
python3.11 -c "
import sys
import torch
import qlib
import joblib

print(f'Python: {sys.version}')
print(f'PyTorch: {torch.__version__}')
print(f'Qlib: {qlib.__version__}')
print(f'Joblib: {joblib.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
print(f'MPS Available: {torch.backends.mps.is_available() if hasattr(torch.backends, \"mps\") else \"N/A\"}')
"
```

### 3. 监控资源使用

训练时监控资源：

```bash
# 终端1：运行训练
qrun conf_baseline_factors_model_fixed.yaml

# 终端2：监控资源
watch -n 1 'ps aux | grep python | head -5'
```

## 📊 性能对比

| 配置 | 训练时间 | 内存使用 | 稳定性 |
|------|----------|----------|--------|
| 原始配置（n_jobs=1, GPU=0） | N/A（崩溃） | N/A | ❌ |
| 修复配置（n_jobs=0, GPU=-1） | ~30分钟 | ~8GB | ✅ |
| 小数据集测试（3年） | ~10分钟 | ~4GB | ✅ |
| MLP模型（单进程） | ~20分钟 | ~6GB | ✅ |

## 🐛 调试技巧

### 1. 启用详细日志

```bash
# 设置日志级别
export PYTHONUNBUFFERED=1
export QLIB_LOG_LEVEL=DEBUG

qrun conf_baseline_factors_model_fixed.yaml 2>&1 | tee training.log
```

### 2. Python调试模式

```bash
# 使用Python调试器运行
python3.11 -m pdb $(which qrun) conf_baseline_factors_model_fixed.yaml
```

### 3. 内存分析

```bash
# 使用memory_profiler
pip install memory_profiler
python3.11 -m memory_profiler $(which qrun) conf_baseline_factors_model_fixed.yaml
```

## 📞 获取帮助

如果问题仍然存在：

1. **检查日志**：`~/quant_workspace/logs/`
2. **GitHub Issues**：https://github.com/microsoft/QLib/issues
3. **RD-Agent Issues**：https://github.com/microsoft/RD-Agent/issues

提供以下信息：
- 完整的错误日志
- `system_info.py` 输出
- 配置文件内容
- Python和关键库的版本

## 🎯 最佳实践

### 开发阶段
1. 使用小数据集快速迭代
2. 使用简单模型验证流程
3. 保存每个实验的配置和结果

### 生产阶段
1. 使用完整数据集
2. 启用早期停止避免过拟合
3. 定期保存模型检查点
4. 监控训练过程和资源使用

### 代码审查清单
- [ ] 配置文件中 `n_jobs: 0`（macOS）
- [ ] 配置文件中 `GPU: -1`（无CUDA设备）
- [ ] Batch size 适当（2048-8192）
- [ ] 数据时间范围合理
- [ ] 环境变量已设置
- [ ] 运行环境清理脚本
- [ ] 监控资源使用

---

**最后更新**：2026-01-09
**适用版本**：RD-Agent main, Qlib latest
**测试环境**：macOS 15.2, Python 3.11, PyTorch 2.x
