# RD-Agent 非线性因子与机器学习组合指南

## 📚 目录
1. [核心概念](#核心概念)
2. [自动渐进策略](#自动渐进策略)
3. [方法一：因子模式（推荐）](#方法一因子模式推荐)
4. [方法二：模型模式](#方法二模型模式)
5. [方法三：混合策略](#方法三混合策略)
6. [配置优化](#配置优化)
7. [实战示例](#实战示例)

---

## 核心概念

### 什么是非线性因子？

非线性因子是指使用**机器学习模型**或**复杂数学变换**生成的量化因子，相对于传统的线性因子（如动量、均值等），它们能捕捉更复杂的市场模式。

#### 常见类型

| 类型 | 描述 | 示例 |
|------|------|------|
| **ML组合因子** | 使用ML模型组合多个基础因子 | LightGBM、XGBoost因子组合 |
| **神经网络因子** | 使用深度学习提取特征 | LSTM、Transformer因子 |
| **非线性变换** | 对基础因子进行非线性变换 | log、sqrt、sigmoid变换 |
| **交互因子** | 捕捉因子间的交互效应 | 因子乘积、多项式特征 |

---

## 自动渐进策略

### 🎯 RD-Agent 的智能策略

RD-Agent 内置了**渐进式因子复杂度策略**：

```python
# 源码位置: rdagent/scenarios/qlib/proposal/factor_proposal.py:41

if len(trace.hist) < 15:
    RAG = "Try the easiest and fastest factors to experiment with..."
else:
    RAG = "Now, you need to try factors that can achieve high IC (e.g., machine learning-based factors)."
```

### 策略说明

| 阶段 | 循环数 | 策略 | 目标 |
|------|--------|------|------|
| **探索期** | 1-15 | 简单线性因子 | 快速验证基本假设 |
| **深化期** | 16+ | 机器学习因子 | 追求更高的IC值 |

### 自动触发机制

**无需手动配置**，系统会在第16轮自动切换策略：

```bash
# 运行16轮以上，系统会自动生成ML因子
python rdagent/app/qlib_rd_loop/factor.py --loop_n 20
```

---

## 方法一：因子模式（推荐）

### 📌 概念

直接让 LLM 生成使用机器学习的因子代码。

### 配置方法

#### 方案 A：让系统自动运行（最简单）

```bash
# 直接运行20+轮，系统会自动在第16轮开始生成ML因子
python rdagent/app/qlib_rd_loop/factor.py --loop_n 20
```

#### 方案 B：从现有实验继续

```bash
# 继续您的实验，运行更多循环
python rdagent/app/qlib_rd_loop/factor.py \
    --path "/Users/berton/Github/RD-Agent/log/2025-12-27_09-27-43-735031/__session__/0" \
    --loop_n 20  # 再运行20个循环
```

### 提示词引导（可选）

如果想**立即**生成ML因子（不等到第16轮），可以修改提示词：

**编辑文件**：`rdagent/scenarios/qlib/proposal/factor_proposal.py`

```python
# 原代码（第38-42行）
"RAG": (
    "Try the easiest and fastest factors..."
    if len(trace.hist) < 15
    else "Now, you need to try factors that can achieve high IC..."
)

# 修改为（立即使用ML因子）
"RAG": (
    "Focus on machine learning-based factors and nonlinear combinations. "
    "Use models like LightGBM, XGBoost, or neural networks to create factors."
)
```

### 预期生成的ML因子示例

运行后，系统会生成类似这样的因子：

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

def calculate_ML_Combined_Factor():
    """机器学习组合因子"""
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 计算多个基础因子
    df_reset['momentum_10'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(10)
    )
    df_reset['volatility_20'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.rolling(20).std()
    )
    df_reset['volume_ratio'] = df_reset.groupby('instrument')['$volume'].transform(
        lambda x: x / x.rolling(20).mean()
    )

    # 使用随机森林组合因子
    def ml_combine(group):
        features = group[['momentum_10', 'volatility_20', 'volume_ratio']].dropna()
        if len(features) < 30:
            return pd.Series([np.nan] * len(group), index=group.index)

        # 使用未来收益作为标签（训练时）
        target = group['$close'].shift(-5) / group['$close'] - 1

        train_data = features.dropna()
        train_target = target.loc[train_data.index]

        if len(train_data) < 20:
            return pd.Series([np.nan] * len(group), index=group.index)

        model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
        model.fit(train_data, train_target)

        # 预测因子值
        predictions = model.predict(features)
        return pd.Series(predictions, index=group.index)

    df_reset['ML_Combined'] = df_reset.groupby('instrument', group_keys=False).apply(ml_combine)

    # 恢复MultiIndex
    result = df_reset.set_index(['datetime', 'instrument'])[['ML_Combined']]
    result.to_hdf('result.h5', key='data')
```

---

## 方法二：模型模式

### 📌 概念

使用 Qlib 的**模型模式**，让 RD-Agent 自动训练机器学习模型来预测收益，模型的输出本身就是非线性因子。

### 工作原理

```
基础因子 → ML模型 → 预测收益 → 作为新因子
```

### 使用方法

```bash
# 使用模型模式（不是因子模式）
python rdagent/app/qlib_rd_loop/model.py --loop_n 10
```

### 模型模式 vs 因子模式

| 维度 | 因子模式 | 模型模式 |
|------|----------|----------|
| **目标** | 生成单个因子代码 | 训练完整预测模型 |
| **输出** | 可复用的因子计算代码 | 训练好的模型文件 |
| **复杂度** | 较低（单一因子） | 较高（完整模型） |
| **灵活性** | 高（每个因子独立） | 中（模型结构固定） |

### 模型模式生成的代码示例

```python
import qlib
from qlib.contrib.model.pytorch_nn import DNNModelPytorch
from qlib.contrib.data.handler import DataHandlerLP
from qlib.contrib.evaluate import risk_analysis

class CustomMLModel:
    """自定义机器学习模型"""

    def __init__(self, **kwargs):
        self.model = DNNModelPytorch(
            d_feat=20,  # 特征维度
            hidden_size=[64, 32, 16],  # 神经网络结构
            dropout=0.2,
        )

    def fit(self, dataset):
        """训练模型"""
        # 训练逻辑
        self.model.fit(dataset)

    def predict(self, dataset):
        """预测收益"""
        return self.model.predict(dataset)
```

---

## 方法三：混合策略

### 📌 概念

结合因子和模型两种模式，先用简单因子筛选，再用模型组合。

### 实施步骤

#### 步骤1：先生成基础因子

```bash
# 运行因子模式，生成5-10个基础因子
python rdagent/app/qlib_rd_loop/factor.py --loop_n 5
```

#### 步骤2：切换到模型模式

```bash
# 使用模型模式，自动组合前面的因子
python rdagent/app/qlib_rd_loop/model.py \
    --path <因子实验的路径> \
    --loop_n 5
```

### 量化循环模式

```bash
# 使用 quant 命令自动在因子和模型之间切换
python rdagent/app/qlib_rd_loop/quant.py --loop_n 20
```

这会让 RD-Agent 自动决定何时生成因子，何时训练模型。

---

## 配置优化

### 环境变量配置

创建 `.env` 文件或在启动时设置：

```bash
# 启用更多实验并行
export RD_AGENT_MAX_PARALLEL=4

# 增加进化循环次数
export COSTEER_MAX_LOOP=5

# 设置超时时间（允许更复杂的模型训练）
export TIMEOUT=3600  # 1小时
```

### 配置文件调优

编辑 `pyproject.toml`：

```toml
[tool.rdagent]
# 循环配置
max_loop = 20
max_parallel = 4

# CoSTEER配置
coster_max_loop = 5
enable_diversity = true

# 实验配置
enable_mlflow = true
workspace_path = "./workspace"
```

### 提示词增强（高级）

编辑 `rdagent/components/coder/factor_coder/prompts.yaml`，添加ML示例：

```yaml
evolving_strategy_factor_implementation_v1_system: |-
  ...
  EXAMPLE 4 - Machine Learning Factor:
  ```python
  def calculate_ML_Factor():
      import pandas as pd
      import numpy as np
      from sklearn.ensemble import GradientBoostingRegressor

      df = pd.read_hdf('daily_pv.h5', key='data')
      df_reset = df.reset_index()

      # 计算特征
      df_reset['feature_1'] = ...  # 您的特征工程
      df_reset['feature_2'] = ...

      # 使用Gradient Boosting
      model = GradientBoostingRegressor(n_estimators=100, max_depth=3)

      # 训练和预测
      ...
  ```
```

---

## 实战示例

### 示例1：从零开始运行ML因子

```bash
# 1. 创建新目录
mkdir ml_factor_experiment
cd ml_factor_experiment

# 2. 运行20轮（前15轮简单因子，后5轮ML因子）
python rdagent/app/qlib_rd_loop/factor.py --loop_n 20

# 3. 等待完成...
#    - 轮1-15：生成动量、波动率等简单因子
#    - 轮16-20：开始生成ML组合因子

# 4. 查看结果
rdagent ui --port 19899
```

### 示例2：继续您当前的实验

```bash
# 从现有实验继续，运行更多循环以触发ML因子
python rdagent/app/qlib_rd_loop/factor.py \
    --path "/Users/berton/Github/RD-Agent/log/2025-12-27_09-27-43-735031/__session__/0" \
    --loop_n 15
```

这会在您当前的1个循环基础上，再运行15个循环（总共16个），在第16个循环触发ML因子生成。

### 示例3：手动指定ML因子类型

编辑代码以在提示词中明确指定ML因子类型：

```python
# rdagent/scenarios/qlib/proposal/factor_proposal.py

# 修改 prepare_context 方法
def prepare_context(self, trace: Trace) -> Tuple[dict, bool]:
    ...
    context_dict = {
        ...
        "RAG": """
        Generate machine learning-based factors using these approaches:
        1. Gradient Boosting (XGBoost/LightGBM) combined factors
        2. Random Forest ensemble factors
        3. Neural network-based factors (simple MLP)
        4. Polynomial interaction factors
        5. Nonlinear transformation factors (log, exp, sigmoid)

        Prioritize factors that can achieve IC > 0.05.
        """,
        ...
    }
```

### 示例4：使用模型模式直接训练

```bash
# 直接使用模型模式
python rdagent/app/qlib_rd_loop/model.py --loop_n 10

# 这会自动：
# 1. 使用Alpha158基础因子
# 2. 训练LightGBM/MLP模型
# 3. 评估模型性能
# 4. 根据反馈改进模型结构
```

---

## 监控和评估

### 关键指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| **IC** | > 0.05 | 因子与收益的相关性 |
| **Rank IC** | > 0.05 | 排名相关性 |
| **ICIR** | > 0.5 | IC的稳定性 |
| **年化收益** | > 5% | 扣除成本后的收益 |
| **最大回撤** | < -15% | 风险控制 |

### 查看实验进度

```bash
# 实时日志
tail -f log/latest.log

# Web UI
rdagent ui --port 19899
```

### 分析生成的ML因子

```python
import pandas as pd
import pickle

# 加载实验结果
with open('path/to/experiment.pkl', 'rb') as f:
    exp = pickle.load(f)

# 查看生成的因子
for task in exp.sub_tasks:
    print(f"因子名称: {task.factor_name}")
    print(f"因子描述: {task.factor_description}")

# 查看性能
print(exp.running_info.result)
```

---

## 故障排除

### 问题1：系统没有生成ML因子

**原因**：循环数不足15轮

**解决**：
```bash
# 增加循环数
python rdagent/app/qlib_rd_loop/factor.py --loop_n 20
```

### 问题2：ML因子训练失败

**原因**：内存不足或超时

**解决**：
```bash
# 增加超时时间
export TIMEOUT=7200

# 减少并行数
export RD_AGENT_MAX_PARALLEL=1

# 重新运行
python rdagent/app/qlib_rd_loop/factor.py --loop_n 20
```

### 问题3：生成的ML因子IC值仍然很低

**原因**：特征不足或模型结构有问题

**解决**：
1. 先生成更多基础因子（10-15个）
2. 切换到模型模式让系统自动组合
3. 手动编辑提示词，明确要求更强的模型

---

## 最佳实践

### ✅ 推荐做法

1. **渐进式策略**：先让系统运行15+轮，自动触发ML因子
2. **充分运行**：至少运行20-30轮以充分探索
3. **混合模式**：结合因子和模型两种模式
4. **监控性能**：使用Web UI实时查看IC值变化
5. **保存检查点**：定期保存实验状态

### ❌ 避免做法

1. 不要在第1轮就强制使用ML因子（缺乏基础数据）
2. 不要期望ML因子立即有高IC（需要多次迭代）
3. 不要忽略简单的线性因子（它们可能是组合的基础）
4. 不要设置过短的超时时间（ML训练需要时间）

---

## 总结

| 方法 | 难度 | 效果 | 推荐场景 |
|------|------|------|----------|
| **自动运行15+轮** | ⭐ | ⭐⭐⭐⭐ | 生产环境，自动探索 |
| **修改提示词** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 快速获得特定类型ML因子 |
| **模型模式** | ⭐⭐ | ⭐⭐⭐⭐ | 需要完整预测模型 |
| **混合策略** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 追求最佳性能 |

**快速开始命令**：
```bash
# 最简单的方式 - 让系统自动处理
python rdagent/app/qlib_rd_loop/factor.py --loop_n 20

# 或继续您当前的实验
python rdagent/app/qlib_rd_loop/factor.py \
    --path "/Users/berton/Github/RD-Agent/log/2025-12-27_09-27-43-735031/__session__/0" \
    --loop_n 15
```

运行15+轮后，系统会自动开始生成机器学习因子！🚀
