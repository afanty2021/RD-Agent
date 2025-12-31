# 数据使用示例

本目录包含演示如何使用 RD-Agent 数据的独立可运行示例脚本。

## 📁 文件列表

| 脚本 | 说明 | 输出文件 |
|------|------|----------|
| `ex01_basic_financial_factors.py` | 基础财务因子（ROE、PE、DebtToAssets） | `ex01_basic_financial_factors_output.h5` |
| `ex02_composite_value_momentum.py` | 复合因子：价值 + 动量组合 | `ex02_composite_value_momentum_output.h5` |
| `ex03_industry_relative_strength.py` | 行业相对强度因子（行业中性） | `ex03_industry_relative_strength_output.h5` |
| `ex04_report_period_roe.py` | 报告期概念：正确使用财务数据 | `ex04_report_period_roe_output.h5` |
| `run_all_examples.py` | 主运行脚本（运行所有或单个示例） | - |

## 🚀 快速开始

### 1. 检查环境

```bash
python run_all_examples.py --check-only
```

### 2. 列出所有示例

```bash
python run_all_examples.py --list
```

### 3. 运行单个示例

```bash
# 运行示例 1：基础财务因子
python run_all_examples.py --example 1

# 运行示例 2：复合因子
python run_all_examples.py --example 2

# 运行示例 3：行业相对强度
python run_all_examples.py --example 3

# 运行示例 4：报告期概念
python run_all_examples.py --example 4
```

### 4. 运行所有示例

```bash
python run_all_examples.py --all
```

## 📊 示例详解

### 示例 1：基础财务因子

演示如何使用 `daily_pv.h5` 中的 22 个财务数据列创建基础因子。

**包含因子：**
- **ROE Factor** - 净资产收益率（盈利能力）
- **PE Factor** - 市盈率（估值）
- **DebtToAssets Factor** - 资产负债率（偿债风险）

**核心概念：**
- 截面标准化（z-score、rank）
- 过滤缺失值
- 因子统计和分析

```bash
python ex01_basic_financial_factors.py
```

### 示例 2：复合因子 - 价值 + 动量

演示如何结合技术面数据和财务数据创建复合因子。

**因子构成：**
- **价值信号** (40%): PE 百分位倒数
- **动量信号** (60%): 20日收益率 z-score

**学术依据：**
- Asness, Moskowitz, Pedersen (2013): "Value and Momentum Everywhere"
- 价值和动量负相关，组合后更稳定

```bash
python ex02_composite_value_momentum.py
```

### 示例 3：行业相对强度因子

演示如何使用行业分类数据创建行业中性因子。

**包含因子：**
- **行业相对 PE** - 在行业内比较估值
- **行业相对 ROE** - 在行业内比较盈利能力
- **行业中性动量** - 在行业内比较价格动量

**优势：**
- 消除行业偏差
- 降低行业集中风险
- 更公平的公司间比较

```bash
python ex03_industry_relative_strength.py
```

### 示例 4：报告期概念

演示如何正确使用季度财务数据，避免前视偏差（look-ahead bias）。

**核心问题：**
- 财务数据是季度报告，不能简单 forward-fill
- 必须使用公告日期确定数据可用性

**正确做法：**
- 使用 `end_date`（报告期结束日）和 `ann_date`（公告日期）
- 每个交易日使用该日或之前公布的最新财报

```bash
python ex04_report_period_roe.py
```

## 📖 数据文件

所有示例使用的数据文件位于：

```
~/git_ignore_folder/factor_implementation_source_data/daily_pv.h5
```

**数据结构：**
- **索引**: MultiIndex `(datetime, instrument)`
- **列数**: 29 列
  - 6 列价格/成交量数据
  - 22 列财务数据
  - 1 列现有因子

**财务数据列：**
- 估值：PE, PB, PS, PCF
- 盈利能力：ROE, ROA, ROIC, NetProfitMargin, GrossProfitMargin
- 成长能力：EPS_Growth, CFPS_Growth, NetProfit_Growth, OP_Growth
- 偿债能力：DebtToAssets, CurrentRatio, QuickRatio, OCF_To_Debt
- 运营能力：AssetsTurnover, AR_Turnover, CA_Turnover
- 基础指标：EPS, BPS, OCFPS, CFPS, EBITDA

## 🔧 依赖包

```bash
pip install pandas numpy pytables
```

## 📚 相关文档

- [数据 README](../../../../../git_ignore_folder/factor_implementation_source_data/README.md)
- [报告期概念详解](../REPORT_PERIOD_CONCEPT.md)
- [报告期工具函数](../report_period_utils.py)
- [因子编码提示词](../prompts.yaml)

## 💡 使用建议

1. **学习顺序**：
   - 先运行示例 1，了解基础财务数据
   - 再运行示例 2，学习复合因子构建
   - 然后运行示例 3，掌握行业中性方法
   - 最后运行示例 4，理解报告期概念

2. **实践建议**：
   - 每个示例都是独立的，可以单独运行
   - 修改参数观察因子变化
   - 使用输出文件进行进一步分析

3. **进阶使用**：
   - 结合 Qlib 框架进行完整回测
   - 尝试其他财务指标组合
   - 实现自己的因子逻辑

## 🐛 故障排除

### 问题：找不到数据文件

```
❌ 错误: 找不到数据文件
```

**解决方案：**
1. 确认数据路径正确
2. 运行数据准备脚本

### 问题：缺少依赖包

```
❌ 错误: No module named 'tables'
```

**解决方案：**
```bash
pip install pytables
```

### 问题：行业分类文件缺失

```
❌ 错误: 在行业目录中找不到行业分类文件
```

**解决方案：**
1. 确保已准备行业分类数据
2. 检查 `~/.qlib/qlib_data/cn_data/industry_data/` 目录

## 📞 获取帮助

如有问题，请查阅：
- [主项目 README](../../../../README.md)
- [Qlib 文档](https://qlib.readthedocs.io/)

---

*最后更新：2025-12-31*
