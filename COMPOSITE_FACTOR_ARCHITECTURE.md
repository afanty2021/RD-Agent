# RD-Agent 复合因子架构设计方案

## 📊 问题分析

### 当前状态
1. **数据源单一**：只使用日频价格/成交量数据（OHLCV）
2. **因子类型局限**：所有生成的因子都是技术分析因子
3. **收益率瓶颈**：第27轮运行中IC/Rank IC表现平平

### 可用数据源
根据Qlib和Tushare的研究，以下数据已可用：

#### 1️⃣ 财务数据（Tushare Pro）
```python
# 估值指标
PE, PE_TTM      # 市盈率
PB, PS, PS_TTM  # 市净率、市销率

# 盈利能力
ROE, ROA        # 净资产收益率、总资产收益率
OperatingProfitGrowRate  # 营业利润增长率
NetProfitGrowRate        # 净利润增长率

# 成长能力
OperatingRevenueGrowRate # 营业收入增长率

# 偿债能力
DebtToAssets    # 资产负债率
CurrentRatio    # 流动比率

# 运营能力
TotalAssetTurnover      # 总资产周转率
InventoryTurnover       # 存货周转率

# 市值数据
TotalMV, CircMV         # 总市值、流通市值
```

#### 2️⃣ 行业数据（申万2021分类）
```python
# L1（一级行业）：29个
# 机械设备, 电子, 医药生物, 化工, 汽车, 计算机, etc.

# L2（二级行业）：110个
# 电气设备, 元器件, 软件服务, 专用机械, 汽车配件, etc.

# 数据来源：~/.qlib/qlib_data/cn_data/industry_data/
# 文件：tushare_stock_to_industry_dict_*.json
```

---

## 🎯 复合因子架构设计

### 核心理念：三层因子融合
```
┌─────────────────────────────────────────────────┐
│          Layer 3: Ensemble Factor               │
│      (Final Combined Alpha Signal)               │
└─────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────┐
│       Layer 2: Cross-Sectional Normalization    │
│    (Time-specific Z-score, Industry Neutral)    │
└─────────────────────────────────────────────────┘
                        ↕
┌───────────┬───────────┬───────────┬─────────────┐
│ Technical │  Financial │  Industry  │ Interaction  │
│  Factors  │  Factors  │  Factors  │   Factors   │
└───────────┴───────────┴───────────┴─────────────┘
```

---

## 🏗️ 实现方案

### Phase 1: 数据层改造

#### 1.1 扩展数据生成脚本
修改 `rdagent/scenarios/qlib/experiment/factor_data_template/generate.py`：

```python
import qlib
from qlib.data import D

# 新增：加载财务数据
financial_fields = [
    # 基础行情
    "$open", "$close", "$high", "$low", "$volume", "$amount",
    # 估值指标
    "PE", "PE_TTM", "PB", "PS", "PS_TTM",
    # 盈利能力
    "ROE", "ROA", "OperatingProfitGrowRate", "NetProfitGrowRate",
    # 成长能力
    "OperatingRevenueGrowRate",
    # 市值
    "TotalMV", "CircMV",
]

data_financial = D.features(
    instruments,
    financial_fields,
    freq="day"
).swaplevel().sort_index().loc["2008-12-29":].sort_index()

data_financial.to_hdf("./daily_pv_financial_all.h5", key="data")

# 新增：生成行业分类数据
import json
from pathlib import Path

industry_file = Path.home() / '.qlib/qlib_data/cn_data/industry_data/tushare_stock_to_industry_dict_20251229_161019.json'
with open(industry_file) as f:
    industry_mapping = json.load(f)

# 转换为DataFrame并保存
industry_df = pd.DataFrame([
    {"instrument": k, "industry_l1": v.get("industry_l1"), "industry_l2": v.get("industry_l2")}
    for k, v in industry_mapping.items()
])
industry_df.to_hdf("./industry_classification.h5", key="data")
```

#### 1.2 创建数据加载工具类
新建 `rdagent/scenarios/qlib/experiment/utils_enhanced.py`：

```python
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict

class EnhancedDataLoader:
    """增强的数据加载器，支持多源数据"""

    def __init__(self, data_folder: str):
        self.data_folder = Path(data_folder)

    def load_base_data(self) -> pd.DataFrame:
        """加载基础价格/成交量数据"""
        return pd.read_hdf(self.data_folder / "daily_pv.h5", key='data')

    def load_financial_data(self) -> pd.DataFrame:
        """加载财务数据"""
        path = self.data_folder / "daily_pv_financial.h5"
        if path.exists():
            return pd.read_hdf(path, key='data')
        return pd.DataFrame()

    def load_industry_mapping(self) -> Dict[str, Dict[str, str]]:
        """加载行业分类映射"""
        path = self.data_folder / "industry_classification.h5"
        if path.exists():
            df = pd.read_hdf(path, key='data')
            return df.set_index('instrument').to_dict('index')
        return {}

    def merge_all_data(self,
                       base_df: pd.DataFrame,
                       financial_df: Optional[pd.DataFrame] = None,
                       industry_mapping: Optional[Dict] = None) -> pd.DataFrame:
        """合并所有数据源"""

        df = base_df.copy()

        # 合并财务数据
        if financial_df is not None and len(financial_df) > 0:
            df = df.join(financial_df, how='left')

        # 添加行业分类
        if industry_mapping:
            df_reset = df.reset_index()
            df_reset['industry_l1'] = df_reset['instrument'].map(
                lambda x: industry_mapping.get(x, {}).get('industry_l1', 'Unknown')
            )
            df_reset['industry_l2'] = df_reset['instrument'].map(
                lambda x: industry_mapping.get(x, {}).get('industry_l2', 'Unknown')
            )
            df = df_reset.set_index(['datetime', 'instrument'])

        return df
```

---

### Phase 2: 因子层增强

#### 2.1 创建复合因子模板库
新建 `rdagent/components/coder/factor_coder/composite_templates.py`：

```python
"""
复合因子模板库

提供财务因子、行业因子和交互因子的标准模板
"""

# ==================== 财务因子模板 ====================

FINANCIAL_FACTOR_PE = """
def calculate_PE_Momentum():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv_financial.h5', key='data')
    df_reset = df.reset_index()

    # PE动量因子：低PE股票的动量效应
    # 逻辑：低估值股票可能有更好的上涨空间

    # 计算PE的横截面分位数（每天）
    df_reset['PE_percentile'] = df_reset.groupby('datetime')['PE'].transform(
        lambda x: x.rank(pct=True)
    )

    # 低PE定义为分位数<0.3
    df_reset['Low_PE'] = (df_reset['PE_percentile'] < 0.3).astype(int)

    # 计算动量（20日收益率）
    df_reset['momentum_20d'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=20)
    )

    # PE动量因子 = 动量 × (1 - PE分位数)
    # 低PE股票获得更高权重
    df_reset['PE_Momentum'] = df_reset['momentum_20d'] * (1 - df_reset['PE_percentile'])

    result = df_reset.set_index(['datetime', 'instrument'])[['PE_Momentum']]
    result.to_hdf('result.h5', key='data')
"""

FINANCIAL_FACTOR_ROE = """
def calculate_ROE_Trend():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv_financial.h5', key='data')
    df_reset = df.reset_index()

    # ROE趋势因子：寻找盈利能力持续改善的公司

    # 计算ROE的60日变化率
    df_reset = df_reset.sort_values(['instrument', 'datetime'])
    df_reset['ROE_change'] = df_reset.groupby('instrument')['ROE'].transform(
        lambda x: x.pct_change(periods=60)
    )

    # 标准化ROE和ROE变化
    df_reset['ROE_zscore'] = df_reset.groupby('datetime')['ROE'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )
    df_reset['ROE_change_zscore'] = df_reset.groupby('datetime')['ROE_change'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # ROE趋势因子 = 高ROE + 上升趋势
    df_reset['ROE_Trend'] = (
        df_reset['ROE_zscore'] * 0.5 +
        df_reset['ROE_change_zscore'] * 0.5
    )

    result = df_reset.set_index(['datetime', 'instrument'])[['ROE_Trend']]
    result.to_hdf('result.h5', key='data')
"""

# ==================== 行业因子模板 ====================

INDUSTRY_FACTOR_MOMENTUM = """
def calculate_Industry_Momentum():
    import pandas as pd
    import numpy as np
    import json
    from pathlib import Path

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 加载行业分类
    industry_file = Path.home() / '.qlib/qlib_data/cn_data/industry_data/tushare_stock_to_industry_dict_20251229_161019.json'
    with open(industry_file) as f:
        industry_mapping = json.load(f)

    # 映射股票到L2行业（110个细分行业）
    df_reset['industry_l2'] = df_reset['instrument'].map(
        lambda x: industry_mapping.get(x, {}).get('industry_l2', 'Unknown')
    )

    # 计算个股动量（5日收益率）
    df_reset['stock_return_5d'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=5)
    )

    # 计算行业平均动量
    industry_momentum = df_reset.groupby(['datetime', 'industry_l2'])['stock_return_5d'].transform('mean')

    # 行业动量因子：使用行业动量作为因子值
    df_reset['Industry_Momentum'] = industry_momentum.values

    # 过滤掉无行业分类的股票
    df_valid = df_reset[df_reset['industry_l2'] != 'Unknown'].copy()

    result = df_valid.set_index(['datetime', 'instrument'])[['Industry_Momentum']]
    result.to_hdf('result.h5', key='data')
"""

INDUSTRY_FACTOR_RELATIVE_STRENGTH = """
def calculate_Industry_Relative_Strength():
    import pandas as pd
    import numpy as np
    import json
    from pathlib import Path

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 加载行业分类
    industry_file = Path.home() / '.qlib/qlib_data/cn_data/industry_data/tushare_stock_to_industry_dict_20251229_161019.json'
    with open(industry_file) as f:
        industry_mapping = json.load(f)

    df_reset['industry_l2'] = df_reset['instrument'].map(
        lambda x: industry_mapping.get(x, {}).get('industry_l2', 'Unknown')
    )

    # 计算个股收益率
    df_reset['stock_return'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=10)
    )

    # 计算行业平均收益率
    industry_return = df_reset.groupby(['datetime', 'industry_l2'])['stock_return'].transform('mean')

    # 行业相对强度 = 个股收益 - 行业收益
    df_reset['Industry_Relative_Strength'] = df_reset['stock_return'] - industry_return

    # 过滤
    df_valid = df_reset[df_reset['industry_l2'] != 'Unknown'].copy()

    result = df_valid.set_index(['datetime', 'instrument'])[['Industry_Relative_Strength']]
    result.to_hdf('result.h5', key='data')
"""

# ==================== 交互因子模板 ====================

INTERACTION_FACTOR_VALUE_MOMENTUM = """
def calculate_Value_Momentum_Combo():
    import pandas as pd
    import numpy as np
    import json
    from pathlib import Path

    df = pd.read_hdf('daily_pv_financial.h5', key='data')
    df_reset = df.reset_index()

    # 加载行业分类
    industry_file = Path.home() / '.qlib/qlib_data/cn_data/industry_data/tushare_stock_to_industry_dict_20251229_161019.json'
    with open(industry_file) as f:
        industry_mapping = json.load(f)

    df_reset['industry_l2'] = df_reset['instrument'].map(
        lambda x: industry_mapping.get(x, {}).get('industry_l2', 'Unknown')
    )

    # 1. 计算价值信号（PE分位数倒数）
    df_reset['PE_signal'] = df_reset.groupby('datetime')['PE'].transform(
        lambda x: 1 - (x.rank(pct=True))
    )

    # 2. 计算动量信号
    df_reset['momentum_signal'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=20)
    )
    df_reset['momentum_signal'] = df_reset.groupby('datetime')['momentum_signal'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # 3. 计算行业动量
    df_reset['stock_return'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=5)
    )
    df_reset['industry_momentum'] = df_reset.groupby(['datetime', 'industry_l2'])['stock_return'].transform('mean')

    # 4. 组合因子 = 价值信号 + 动量信号 + 行业动量
    df_reset['Value_Momentum_Combo'] = (
        df_reset['PE_signal'] * 0.3 +
        df_reset['momentum_signal'] * 0.5 +
        df_reset['industry_momentum'] * 0.2
    )

    # 过滤
    df_valid = df_reset[(df_reset['industry_l2'] != 'Unknown') & (df_reset['PE'].notna())].copy()

    result = df_valid.set_index(['datetime', 'instrument'])[['Value_Momentum_Combo']]
    result.to_hdf('result.h5', key='data')
"""

INTERACTION_FACTOR_QUALITY_MOMENTUM = """
def calculate_Quality_Momentum_Combo():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv_financial.h5', key='data')
    df_reset = df.reset_index()

    # 1. 质量信号（ROE + ROA）
    df_reset['quality_signal'] = (
        df_reset.groupby('datetime')['ROE'].transform(
            lambda x: (x - x.mean()) / (x.std() + 1e-12)
        ) +
        df_reset.groupby('datetime')['ROA'].transform(
            lambda x: (x - x.mean()) / (x.std() + 1e-12)
        )
    ) / 2

    # 2. 成长信号（营收增长 + 利润增长）
    df_reset['growth_signal'] = (
        df_reset.groupby('datetime')['OperatingRevenueGrowRate'].transform(
            lambda x: (x - x.mean()) / (x.std() + 1e-12)
        ) +
        df_reset.groupby('datetime')['NetProfitGrowRate'].transform(
            lambda x: (x - x.mean()) / (x.std() + 1e-12)
        )
    ) / 2

    # 3. 动量信号
    df_reset['momentum_signal'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=20)
    )
    df_reset['momentum_signal'] = df_reset.groupby('datetime')['momentum_signal'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # 4. 组合：质量(0.3) + 成长(0.3) + 动量(0.4)
    df_reset['Quality_Momentum_Combo'] = (
        df_reset['quality_signal'] * 0.3 +
        df_reset['growth_signal'] * 0.3 +
        df_reset['momentum_signal'] * 0.4
    )

    result = df_reset.set_index(['datetime', 'instrument'])[['Quality_Momentum_Combo']]
    result.to_hdf('result.h5', key='data')
"""
```

---

### Phase 3: 提示词增强

#### 3.1 修改 `prompts.yaml`
在现有的提示词中添加：

```yaml
# ========== 新增：多源数据因子模板 ==========

COMPOSITE_FACTOR_INTRODUCTION: |-
  IMPORTANT - Multi-Source Data Strategy:

  Your factors should COMBINE multiple data sources for better performance:

  1. Technical Factors (price/volume): Short-term signals
  2. Financial Factors (fundamentals): Long-term value
  3. Industry Factors (sector trends): Context-aware signals
  4. Interaction Factors: Synergy between different domains

  EXAMPLE COMBINATIONS:
  - Value + Momentum: Low PE stocks with strong momentum
  - Quality + Growth: High ROE + High revenue growth
  - Industry Rotation: Sector momentum + individual stock strength
  - Multi-factor: Combine 3+ different signal sources

COMPOSITE_FACTOR_EXAMPLE_TEMPLATES: |-
  {% include 'composite_templates.py' %}

FACTOR_SELECTION_GUIDANCE: |-
  When selecting factors, prioritize:
  1. Financial + Technical combinations (highest alpha)
  2. Industry-neutral factors (more robust)
  3. Cross-sectional normalization (critical)
  4. Interaction effects (non-linear value)
```

---

### Phase 4: 评估器增强

#### 4.1 添加复合因子评估指标
新建 `rdagent/components/coder/factor_coder/composite_evaluator.py`：

```python
"""
复合因子评估器

评估复合因子的多维度表现
"""

class CompositeFactorEvaluator:
    """复合因子评估器"""

    @staticmethod
    def evaluate_interaction_effects(factor_df: pd.DataFrame) -> Dict:
        """评估因子间的交互效应"""

        # 1. 单因子IC
        single_ics = {}

        # 2. 组合因子IC
        combined_ic = ...

        # 3. 交互效应增量
        interaction_gain = combined_ic - max(single_ics.values())

        return {
            "single_ics": single_ics,
            "combined_ic": combined_ic,
            "interaction_gain": interaction_gain,
            "synergy_score": interaction_gain / max(single_ics.values())
        }

    @staticmethod
    def evaluate_industry_neutrality(factor_df: pd.DataFrame,
                                     industry_mapping: Dict) -> Dict:
        """评估行业中性化程度"""

        # 计算行业暴露度
        industry_exposure = ...

        # 计算主动风险
        active_risk = ...

        return {
            "industry_neutral": industry_exposure < 0.1,
            "active_risk": active_risk,
            "concentration_ratio": ...
        }

    @staticmethod
    def evaluate_turnover(factor_series: pd.Series) -> Dict:
        """评估因子换手率"""

        turnover = factor_series.diff().abs().mean()

        return {
            "avg_turnover": turnover,
            "turnover_stability": ...
        }
```

---

## 📈 预期效果

### 收益率提升路径

1. **单因子优化**（IC提升0.02-0.05）
   - 财务因子：价值、质量、成长
   - 行业因子：行业动量、相对强度

2. **组合因子**（IC再提升0.03-0.08）
   - 价值+动量：经典组合
   - 质量+成长：基本面驱动
   - 行业中性：降低风险

3. **动态权重**（IC再提升0.02-0.04）
   - 市场状态识别
   - 因子权重自适应

**预期总IC提升：0.07 - 0.17**

---

## 🚀 实施步骤

### Step 1: 数据准备 ✅ **已完成**
- [x] 财务数据转换脚本 `scripts/convert_tushare_financial_to_hdf5.py`
- [x] 数据合并脚本 `scripts/merge_financial_price_data.py`
- [x] 前向填充脚本 `scripts/forward_fill_financial_data.py`
- [x] 数据验证：7,584,444行 × 29列，3875只股票
- [x] 财务字段覆盖率：5.74%（前向填充后）

### Step 2: 工具类开发 ✅ **已完成**
- [x] 实现 `EnhancedDataLoader` (`rdagent/scenarios/qlib/experiment/utils_enhanced.py`)
- [x] 实现复合因子模板库 (`rdagent/components/coder/factor_coder/composite_templates.py`)
- [x] 单元测试 (`scripts/test_composite_factor.py`)
- [x] 测试结果：ROE趋势因子、质量+动量组合因子均通过

### Step 3: 提示词优化 ✅ **已完成**
- [x] 更新 `prompts.yaml` 添加 `composite_factor_priority_guidance`
- [x] 添加4个复合因子示例模板
- [x] 添加因子选择引导和多源数据策略说明

### Step 4: 评估器增强 ⏳ **待实施**
- [ ] 实现复合因子评估器
- [ ] 添加交互效应评估
- [ ] 添加行业中性评估

### Step 5: 集成测试 ⏳ **进行中**
- [x] 端到端测试（复合因子生成）
- [ ] 性能对比（新旧因子IC对比）
- [ ] 参数调优

**完成进度：3/5 (60%)**

---

## 🔑 关键成功因素

1. **数据质量**：确保财务数据和行业分类准确
2. **前瞻性**：避免使用未来数据（时间泄漏）
3. **标准化**：所有因子必须横截面标准化
4. **行业中性**：降低行业偏离度
5. **换手率控制**：平衡因子效果和交易成本

---

## 📚 参考资料

1. **因子投资经典文献**
   - Fama-French 五因子模型
   - Grinold-Kahn 积极管理
   - Qlib量化框架文档

2. **行业分类标准**
   - 申万2021行业分类
   - Tushare行业数据API

3. **财务分析**
   - 杜邦分析法
   - 财务比率手册

---

## ✅ 已完成工作总结

### 数据处理流程（2025-12-30完成）

#### 1. 财务数据转换
**文件**: `scripts/convert_tushare_financial_to_hdf5.py`

**功能**:
- 读取Tushare财务CSV数据（184,436行）
- 转换股票代码格式（000001.SZ → 000001SZ）
- 映射21个财务指标字段
- 生成HDF5格式输出（32.95 MB）

**财务字段映射**:
```python
FINANCIAL_FIELDS_MAPPING = {
    # 估值指标
    "eps": "EPS", "bps": "BPS", "ocfps": "OCFPS", "cfps": "CFPS",
    # 盈利能力
    "roe": "ROE", "roa": "ROA", "roic": "ROIC",
    "netprofit_margin": "NetProfitMargin", "grossprofit_margin": "GrossProfitMargin",
    # 成长能力
    "basic_eps_yoy": "EPS_Growth", "cfps_yoy": "CFPS_Growth",
    "netprofit_yoy": "NetProfit_Growth", "op_yoy": "OP_Growth",
    # 偿债能力
    "debt_to_assets": "DebtToAssets", "current_ratio": "CurrentRatio",
    "quick_ratio": "QuickRatio", "ocf_to_debt": "OCF_To_Debt",
    # 运营能力
    "assets_turn": "AssetsTurnover", "ar_turn": "AR_Turnover", "ca_turn": "CA_Turnover",
    # 其他
    "ebitda": "EBITDA",
}
```

#### 2. 数据合并
**文件**: `scripts/merge_financial_price_data.py`

**功能**:
- 解决股票代码格式不匹配问题
  - 价格数据：SH600000, SZ000001
  - 财务数据：000001.SZ
- 标准化代码格式后合并
- 生成合并数据（1.5 GB, 7,584,444行 × 29列）

**匹配结果**:
- 价格数据股票数：3,875
- 财务数据股票数：5,466
- 匹配股票数：3,661

#### 3. 前向填充处理
**文件**: `scripts/forward_fill_financial_data.py`

**功能**:
- 对每只股票独立进行前向填充
- 最大填充周期：500个交易日（约1.5年）
- 将财务数据覆盖率从0.09%提升到5.74%
- 额外填充428,000+行数据

**填充前后对比**:
| 字段 | 填充前覆盖率 | 填充后覆盖率 | 增加行数 |
|------|-------------|-------------|----------|
| EPS | 0.09% | 5.74% | +427,972 |
| ROE | 0.09% | 5.71% | +425,978 |
| ROA | 0.09% | 5.60% | +422,894 |

### 代码实现

#### 1. 增强数据加载器
**文件**: `rdagent/scenarios/qlib/experiment/utils_enhanced.py`

**核心类**: `EnhancedDataLoader`

**方法**:
```python
class EnhancedDataLoader:
    def load_base_data(self) -> pd.DataFrame
    def load_financial_data(self) -> pd.DataFrame
    def load_industry_mapping(self) -> Dict[str, Dict[str, str]]
    def merge_all_data(self, base_df, financial_df, industry_mapping) -> pd.DataFrame
    def get_industry_groups(self, df, level="l2") -> Dict[str, List[str]]
    def get_available_fields(self, df) -> Dict[str, List[str]]
```

#### 2. 复合因子模板库
**文件**: `rdagent/components/coder/factor_coder/composite_templates.py`

**模板分类**:
- **财务因子**: PE_Momentum, ROE_Trend
- **行业因子**: Industry_Momentum, Industry_Relative_Strength
- **交互因子**: Value_Momentum_Combo, Quality_Growth_Momentum_Combo

#### 3. 提示词增强
**文件**: `rdagent/components/coder/factor_coder/prompts.yaml`

**新增内容**:
- `composite_factor_priority_guidance`: 多源数据策略指导
- 4个完整的复合因子示例模板
- 研究支持的因子组合建议

### 测试验证

#### 测试脚本
**文件**: `scripts/test_composite_factor.py`

**测试结果**:

**测试1: ROE趋势因子**
- 因子覆盖率：2.91%
- 因子均值：-0.0016（标准化正确）
- 因子标准差：0.6937
- 样本值：SZ300841的ROE_Trend=0.3845

**测试2: 质量+动量组合因子**
- 因子覆盖率：5.57%
- 因子均值：0.0075
- 因子标准差：0.6506
- 样本值：
  - SZ300841: Quality=1.98, Combo=0.64
  - SZ300837: Quality=0.79, Combo=0.37

### 数据文件位置

```
~/.qlib/qlib_data/cn_data/financial_data/
├── a_share_financial_latest.csv          # 原始Tushare数据
├── daily_pv_financial.h5                 # 转换后HDF5（32.95 MB）
├── daily_pv_financial_merged.h5          # 合并后数据（1.5 GB）
└── daily_pv_financial_filled.h5          # 前向填充后（1.5 GB）

git_ignore_folder/factor_implementation_source_data/
├── daily_pv.h5                           # 价格数据（203 MB）
└── daily_pv_financial.h5                 # 复制后的财务数据（1.5 GB）
```

### 下一步工作

1. **评估器增强**: 实现复合因子评估器，添加交互效应和行业中性评估
2. **性能对比**: 运行RD-Agent，对比新旧因子的IC表现
3. **参数调优**: 根据回测结果优化因子权重和组合策略

---

*最后更新：2025-12-30*
