# RD-Agent Qlib 环境检测问题修复

## 问题描述

RD-Agent 在运行量化因子实验时，会自动创建名为 `rdagent4qlib` 的 conda 环境，而不会检测用户当前已经激活的虚拟环境（如 `Quant-env-3.11`）。

## 根本原因

在 `rdagent/utils/env.py:667-698` 中，`QlibCondaEnv` 类硬编码了环境名：

```python
class QlibCondaConf(CondaConf):
    conda_env_name: str = "rdagent4qlib"  # 硬编码

class QlibCondaEnv(LocalEnv[QlibCondaConf]):
    def prepare(self) -> None:
        envs = subprocess.run("conda env list", ...)
        if self.conf.conda_env_name not in envs.stdout:  # 只检查 "rdagent4qlib"
            # 创建新环境...
```

### 设计缺陷

1. **不检测当前环境**：忽略用户激活的 `Quant-env-3.11`
2. **硬编码环境名**：无法通过配置自定义
3. **重复创建环境**：浪费时间和磁盘空间

## 解决方案

### 方案 1：使用环境变量（临时）

在运行 RD-Agent 前，设置环境变量指向你的环境：

```bash
# 告诉 RD-Agent 使用现有的环境
export QLIB_CONDA_ENV_NAME=Quant-env-3.11

# 然后运行你的命令
rdagent quant factor --loop_n 2
```

**注意**：如果环境名不存在，RD-Agent 仍会创建它。

### 方案 2：修改源码（彻底）

修改 `rdagent/utils/env.py` 中的 `QlibCondaEnv` 类：

```python
import os

class QlibCondaConf(CondaConf):
    conda_env_name: str = "rdagent4qlib"
    enable_cache: bool = False
    default_entry: str = "qrun conf.yaml"
    use_current_env: bool = False  # 新增：是否使用当前激活的环境


class QlibCondaEnv(LocalEnv[QlibCondaConf]):
    def prepare(self) -> None:
        """Prepare the conda environment if not already created."""
        try:
            # 新增：检测当前激活的环境
            if self.conf.use_current_env:
                current_env = os.environ.get('CONDA_DEFAULT_ENV')
                if current_env:
                    print(f"[cyan]Using current activated conda env: {current_env}[/cyan]")
                    # 检查必要依赖
                    self._check_and_install_deps(current_env)
                    return

            envs = subprocess.run("conda env list", capture_output=True, text=True, shell=True)

            # 检查指定环境是否存在
            if self.conf.conda_env_name in envs.stdout:
                print(f"[cyan]Using existing conda env: {self.conf.conda_env_name}[/cyan]")
                return

            print(f"[yellow]Conda env '{self.conf.conda_env_name}' not found, creating...[/yellow]")
            subprocess.check_call(
                f"conda create -y -n {self.conf.conda_env_name} python=3.10",
                shell=True,
            )
            subprocess.check_call(
                f"conda run -n {self.conf.conda_env_name} pip install --upgrade pip cython",
                shell=True,
            )
            subprocess.check_call(
                f"conda run -n {self.conf.conda_env_name} pip install git+https://github.com/microsoft/qlib.git@3e72593b8c985f01979bebcf646658002ac43b00",
                shell=True,
            )
            subprocess.check_call(
                f"conda run -n {self.conf.conda_env_name} pip install catboost xgboost scipy==1.11.4 tables torch",
                shell=True,
            )
        except Exception as e:
            print(f"[red]Failed to prepare conda env: {e}[/red]")

    def _check_and_install_deps(self, env_name: str):
        """检查并安装必要的依赖"""
        # 检查 qlib
        result = subprocess.run(
            f"conda run -n {env_name} python -c 'import qlib'",
            shell=True,
            capture_output=True
        )
        if result.returncode != 0:
            print(f"[yellow]Installing qlib in env {env_name}...[/yellow]")
            subprocess.check_call(
                f"conda run -n {env_name} pip install git+https://github.com/microsoft/qlib.git@3e72593b8c985f01979bebcf646658002ac43b00",
                shell=True,
            )
```

### 方案 3：手动配置（最简单）

在 `Quant-env-3.11` 中安装 RD-Agent 所需的依赖：

```bash
conda activate Quant-env-3.11

# 安装 Qlib（如果还没有）
pip install qlib

# 安装其他依赖
pip install catboost xgboost scipy==1.11.4 tables torch

# 然后设置环境变量
export QLIB_CONDA_ENV_NAME=Quant-env-3.11
```

## 推荐做法

### 开发场景
使用方案 2（修改源码），让 RD-Agent 智能检测环境。

### 生产/快速测试
使用方案 3（手动配置），一次性设置好环境，然后通过环境变量指定。

## 技术说明

### 为什么 RD-Agent 这样设计？

1. **隔离性**：专用环境确保依赖版本一致
2. **可复现性**：所有用户使用相同的环境配置
3. **简化调试**：避免环境差异导致的问题

### 权衡考虑

| 优点 | 缺点 |
|------|------|
| 环境隔离，避免冲突 | 浪费资源（重复创建） |
| 版本一致，可复现 | 不灵活（忽略用户环境） |
| 降低调试复杂度 | 增加设置时间 |

改进建议：**智能检测 + 用户选择** - 先检测当前环境，如果满足要求则使用，否则才创建专用环境。

---

**最后更新**：2025-12-27
**相关文件**：`rdagent/utils/env.py:667-698`
