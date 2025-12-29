# Qlib MPS (Apple Silicon) 支持指南

## 📝 概述

本指南说明如何在 Apple Silicon (M1/M2/M3/M4) Mac 上启用 Qlib 的 MPS (Metal Performance Shaders) GPU 加速。

## ✅ 已完成的修改

### 1. Qlib 源码补丁

**文件位置**: `qlib/contrib/model/pytorch_general_nn.py`

**修改内容**:

#### 修改 1: 设备选择逻辑（第 86 行）

**修改前**:
```python
self.device = torch.device("cuda:%d" % (GPU) if torch.cuda.is_available() and GPU >= 0 else "cpu")
```

**修改后**:
```python
# Enhanced device selection with MPS support for Apple Silicon
if GPU is not None and GPU >= 0:
    if torch.cuda.is_available():
        self.device = torch.device("cuda:%d" % GPU)
    elif torch.backends.mps.is_available():
        self.device = torch.device("mps")
        self.logger.info("Using Apple Silicon MPS (Metal Performance Shaders) for acceleration")
    else:
        self.device = torch.device("cpu")
        self.logger.info("GPU specified but not available, using CPU")
else:
    self.device = torch.device("cpu")
```

#### 修改 2: GPU 缓存清理（第 331-332 行）

**修改前**:
```python
if self.use_gpu:
    torch.cuda.empty_cache()
```

**修改后**:
```python
# Clear GPU cache based on device type
if self.use_gpu:
    if self.device.type == "cuda":
        torch.cuda.empty_cache()
    elif self.device.type == "mps":
        # MPS doesn't have explicit cache clearing like CUDA
        # But we can trigger garbage collection
        import gc
        gc.collect()
```

### 2. 配置文件更新

所有 Qlib 配置模板已更新：
- `GPU: null` → `GPU: 0` (启用 GPU/MPS)
- `n_jobs: 20` → `n_jobs: 4` (macOS 优化)

## 🚀 使用方法

### 验证 MPS 支持

运行验证脚本：
```bash
python3 scripts/verify_mps.py
```

预期输出：
```
✅ Qlib is patched with MPS support!
📋 Summary:
  🎯 Your Mac supports MPS acceleration
  ⚡ GPU: GPU should be set to 0 in config
  🚀 Expected speedup: 3-5x faster than CPU
```

### 配置实验

在 `.env` 或配置文件中：
```yaml
GPU: 0        # 启用 MPS (Apple Silicon)
n_jobs: 4     # macOS 优化的并行数
```

### 查看训练日志

训练时应该看到：
```
Using Apple Silicon MPS (Metal Performance Shaders) for acceleration
```

## 📦 补丁工具

### 应用补丁

如果重新安装了 Qlib，可以重新应用补丁：

```bash
python3 scripts/qlib_mps_patch.py
```

### 备份文件

补丁会自动创建备份：
- `pytorch_general_nn.py.backup_before_mps`

## ⚠️ 注意事项

### 1. Qlib 更新

当您更新 Qlib 时，补丁会被覆盖。需要重新运行：
```bash
python3 scripts/qlib_mps_patch.py
```

### 2. 环境迁移

如果您将代码迁移到 Linux + CUDA 环境：
- 保持 `GPU: 0` 配置
- Qlib 会自动检测并使用 CUDA
- 无需修改配置

### 3. 性能调优

如果遇到 MPS 性能问题，可以：
- 减少 `batch_size` (例如 2000 → 1000)
- 减少 `n_jobs` (例如 4 → 2)
- 减少 `num_features` (模型复杂度)

## 🔧 故障排除

### MPS 未启用

**症状**: 训练日志没有显示 MPS 信息

**解决**:
1. 运行 `python3 scripts/verify_mps.py`
2. 检查补丁是否应用
3. 确认 `GPU: 0` 在配置中

### 训练崩溃

**症状**: Segmentation fault 或其他错误

**解决**:
1. 将 `GPU: null` (使用 CPU)
2. 减少 `n_jobs: 2`
3. 减少 `batch_size: 1000`

### 内存不足

**症状**: OOM (Out of Memory) 错误

**解决**:
1. 减少 `batch_size`
2. 减少 `n_jobs`
3. 减少模型复杂度

## 📊 性能对比

| 设备 | 训练速度 | 稳定性 | 推荐使用 |
|------|---------|--------|---------|
| **MPS** | ⚡⚡⚡⚡⚡ (3-5x) | ✅ 良好 | ✅ 推荐 (Apple Silicon) |
| **CPU** | ⚡ (1x) | ✅✅ 最好 | ⚠️ 备选方案 |
| **CUDA** | ⚡⚡⚡⚡⚡ (5-10x) | ✅✅ 最好 | ✅ 推荐 (Linux) |

## 🎯 最佳实践

### 开发阶段
- 使用 **CPU** 进行快速迭代
- 代码修改后立即验证
- 无需担心 GPU 兼容性

### 训练阶段
- 使用 **MPS** 进行完整训练
- 批量处理多个实验
- 充分利用 GPU 加速

### 生产环境
- 迁移到 **Linux + CUDA** 服务器
- 获得最佳性能和稳定性
- 使用分布式训练

## 📚 参考资料

- [PyTorch MPS 文档](https://pytorch.org/docs/stable/notes/mps.html)
- [Apple Metal Performance Shaders](https://developer.apple.com/metal/Metal-Shaders-Language-Guide/)
- [Qlib GitHub](https://github.com/microsoft/qlib)

---

**创建日期**: 2025-12-28
**适用版本**: Qlib 0.9.2+, PyTorch 2.0+
**测试环境**: macOS 26.2, Apple Silicon M4 Pro, Python 3.11
