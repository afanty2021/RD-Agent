# Tushare CSV 数据转换为 Qlib 格式指南

## 概述

本指南说明如何将 Tushare CSV 格式的行情数据转换为 Qlib 专用的二进制格式，以便 RD-Agent 使用最新的数据。

## 数据流程

```
┌─────────────────┐
│  Tushare CSV    │
│  (原始数据源)    │
│  stock_data/    │
│  5468 个 CSV    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  dump_bin.py    │
│  (Qlib 转换)    │
│  CSV → .bin     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Qlib 格式      │
│  features/      │
│  *.bin 文件     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RD-Agent       │
│  generate.py    │
│  .bin → .h5     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  训练数据        │
│  daily_pv.h5    │
└─────────────────┘
```

## 当前状态

### 已有数据
- **Tushare CSV**: `~/.qlib/qlib_data/cn_data/stock_data/` (5468 个文件，2000年至今)
- **Qlib 二进制**: `~/.qlib/qlib_data/cn_data/features/` (部分历史数据)

### 问题
- Qlib 二进制数据可能不是最新的
- RD-Agent 训练时使用的是 Qlib 二进制格式，而不是 CSV

## 解决方案

### 自动转换脚本

使用提供的自动转换脚本：

```bash
cd /Users/berton/Github/RD-Agent
python scripts/convert_tushare_csv_to_qlib.py
```

### 脚本功能

1. **备份现有数据** (可选)
   - 自动备份现有的 Qlib 二进制数据
   - 备份位置: `~/.qlib/qlib_data/cn_data_backup_YYYYMMDD_HHMMSS/`

2. **数据转换**
   - 使用 Qlib 的 `dump_bin.py` 将 CSV 转换为二进制格式
   - 并行处理 (16 线程)
   - 支持进度跟踪

3. **结果验证**
   - 检查生成的目录结构
   - 统计转换的股票数量
   - 显示二进制文件信息

4. **更新 RD-Agent 数据** (可选)
   - 重新生成 `daily_pv.h5` 文件
   - RD-Agent 会在下次运行时自动使用新数据

## 手动转换步骤

如果自动脚本出现问题，可以手动执行转换：

### 1. 使用 Qlib dump_bin.py

```bash
cd /Users/berton/Github/qlib

# 导出 CSV 文件目录和 Qlib 目录
export CSV_DIR=~/.qlib/qlib_data/cn_data/stock_data
export QLIB_DIR=~/.qlib/qlib_data/cn_data

# 执行转换
python scripts/dump_bin.py dump_all \
    --csv_path $CSV_DIR \
    --qlib_dir $QLIB_DIR \
    --freq day \
    --max_workers 16 \
    --date_field_name trade_date \
    --symbol_field_name ts_code
```

### 2. 验证转换结果

```bash
# 检查目录结构
ls -la ~/.qlib/qlib_data/cn_data/

# 检查股票数量
ls ~/.qlib/qlib_data/cn_data/features/ | wc -l

# 检查二进制文件
ls ~/.qlib/qlib_data/cn_data/features/sh600000/
```

### 3. 重新生成 RD-Agent 数据

```bash
cd /Users/berton/Github/RD-Agent

# 方法1: 使用 Python 脚本
python -c "from rdagent.scenarios.qlib.experiment.utils import generate_data_folder_from_qlib; generate_data_folder_from_qlib()"

# 方法2: 让 RD-Agent 自动生成 (下次运行时)
# RD-Agent 会在首次运行时自动检测并生成数据
```

## 数据字段说明

### Tushare CSV 字段
```csv
ts_code,trade_date,open,high,low,close,pre_close,vol,amount
000001.SZ,20240101,10.50,10.80,10.30,10.70,10.40,1234567.89,1234567890.12
```

### 字段映射
| Tushare 字段 | Qlib 字段 | 说明 |
|------------|-----------|------|
| trade_date | date | 交易日期 |
| ts_code | instrument | 股票代码 |
| open | $open | 开盘价 |
| high | $high | 最高价 |
| low | $low | 最低价 |
| close | $close | 收盘价 |
| vol | volume | 成交量 |
| amount | amount | 成交额 |

## 常见问题

### Q1: 转换速度慢怎么办？

增加并行线程数：
```bash
python scripts/convert_tushare_csv_to_qlib.py
# 在脚本中修改 max_workers 参数（默认 16）
```

### Q2: 内存不足怎么办？

分批转换：
```bash
# 先转换部分股票
ls ~/.qlib/qlib_data/cn_data/stock_data/*.csv | head -1000 | xargs -I {} cp {} /tmp/stock_data_subset/
python scripts/dump_bin.py dump_all --csv_path /tmp/stock_data_subset/ ...
```

### Q3: 转换后 RD-Agent 仍使用旧数据？

1. 删除 RD-Agent 缓存：
```bash
rm -rf /Users/berton/Github/RD-Agent/rdagent/scenarios/qlib/experiment/factor_data_template/daily_pv*.h5
```

2. 重新生成数据：
```bash
python -c "from rdagent.scenarios.qlib.experiment.utils import generate_data_folder_from_qlib; generate_data_folder_from_qlib()"
```

### Q4: 如何验证转换成功？

```python
import qlib
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data")

from qlib.data import D

# 检查数据是否可用
instruments = D.instruments()
print(f"股票数量: {len(instruments)}")

# 检查数据范围
data = D.features(instruments[:10], ["$close"], freq="day")
print(f"数据形状: {data.shape}")
print(f"时间范围: {data.index.get_level_values('datetime').min()} 到 {data.index.get_level_values('datetime').max()}")
```

## 高级选项

### 使用 TuShare API 直接作为数据源

Qlib 支持 TuShare API 作为直接数据源，无需转换为 CSV：

```python
import qlib
from qlib.contrib.data.tushare import TuShareProvider

# 使用 TuShare API
provider = TuShareProvider(token=os.getenv("TUSHARE_TOKEN"))
qlib.init(provider_uri=provider, region="cn")

# RD-Agent 会自动使用这个数据源
```

### 增量更新

使用 Qlib 的增量更新功能：

```bash
cd /Users/berton/Github/qlib

# 增量更新（只更新最新数据）
python scripts/dump_bin.py dump_update \
    --csv_path ~/.qlib/qlib_data/cn_data/stock_data \
    --qlib_dir ~/.qlib/qlib_data/cn_data
```

## 参考资料

- [Qlib 官方文档](https://qlib.readthedocs.io/)
- [dump_bin.py 源码](https://github.com/microsoft/qlib/blob/main/scripts/dump_bin.py)
- [TuShare API 文档](https://tushare.pro/document/2)

---

*最后更新: 2025-12-29*
