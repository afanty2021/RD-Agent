# D.features() 自动过滤股票的源码实现路径

## 📊 完整调用链

```
用户代码: D.features(instruments=D.instruments('csi300'), fields=..., start_time=..., end_time=...)
    ↓
BaseProvider.features()  [data.py:1305]
    ↓
DatasetD.dataset()  [data.py:1329]
    ↓
LocalDatasetProvider.dataset()  [data.py:1000]
    ↓
LocalDatasetProvider.get_instruments_d()  [data.py:1009]
    ↓
DatasetProvider.get_instruments_d()  [data.py:548]
    ↓
Inst.list_instruments()  [data.py:557-559]
    ↓
LocalInstrumentProvider.list_instruments()  [data.py:756]
    ↓
[返回过滤后的 instruments_d 字典]
    ↓
LocalDatasetProvider.dataset_processor()  [data.py:1024]
    ↓
[为每只股票加载数据]
```

## 🔍 关键源码位置

### 1. 入口点: D.features()

**文件**: `/qlib/data/data.py:1305-1346`

```python
class BaseProvider:
    def features(
        self,
        instruments,      # D.instruments('csi300') 的返回值
        fields,
        start_time=None,
        end_time=None,
        freq="day",
        disk_cache=None,
        inst_processors=[],
    ):
        # ...
        disk_cache = C.default_disk_cache if disk_cache is None else disk_cache
        fields = list(fields)
        try:
            return DatasetD.dataset(  # ← 调用 DatasetD.dataset()
                instruments,
                fields,
                start_time,
                end_time,
                freq,
                disk_cache,
                inst_processors=inst_processors,
            )
        except TypeError:
            return DatasetD.dataset(
                instruments,
                fields,
                start_time,
                end_time,
                freq,
                inst_processors=inst_processors,
            )
```

### 2. 股票过滤核心: DatasetProvider.get_instruments_d()

**文件**: `/qlib/data/data.py:548-568`

```python
@staticmethod
def get_instruments_d(instruments, freq):
    """
    Parse different types of input instruments to output instruments_d
    """
    if isinstance(instruments, dict):
        if "market" in instruments:
            # ← 关键！如果是配置字典（包含 'market' 键）
            # 调用 Inst.list_instruments() 进行股票过滤
            instruments_d = Inst.list_instruments(
                instruments=instruments,  # ← {'market': 'csi300', 'filter_pipe': []}
                freq=freq,
                as_list=False
            )
            # 返回格式: {stock_code: [(start_date, end_date), ...], ...}
        else:
            # 已经是 instruments_d 格式
            instruments_d = instruments
    elif isinstance(instruments, (list, tuple, pd.Index, np.ndarray)):
        # 用户直接提供股票列表
        instruments_d = list(instruments)
    else:
        raise ValueError("Unsupported input type for param `instrument`")
    return instruments_d
```

### 3. 具体过滤实现: LocalInstrumentProvider.list_instruments()

**文件**: `/qlib/data/data.py:756-802`

```python
def list_instruments(
    self, instruments, start_time=None, end_time=None, freq="day", as_list=False
):
    market = instruments["market"]  # ← 'csi300'

    # 1. 从缓存或文件加载原始数据
    if market in H["i"]:
        _instruments = H["i"][market]
    else:
        _instruments = self._load_instruments(market, freq=freq)
        H["i"][market] = _instruments
    # _instruments 格式: {stock_code: [(start, end), ...], ...}

    # 2. 获取日历边界
    cal = Cal.calendar(freq=freq)
    start_time = pd.Timestamp(start_time or cal[0])
    end_time = pd.Timestamp(end_time or cal[-1])

    # 3. 按日期范围过滤股票 ← 这是核心！
    _instruments_filtered = {
        inst: list(
            filter(
                lambda x: x[0] <= x[1],  # 确保时间段有效
                [
                    (
                        max(start_time, pd.Timestamp(x[0])),  # 与start_time取最大值
                        min(end_time, pd.Timestamp(x[1]))    # 与end_time取最小值
                    )
                    for x in spans
                ],
            )
        )
        for inst, spans in _instruments.items()
    }

    # 4. 移除空时间段
    _instruments_filtered = {
        key: value for key, value in _instruments_filtered.items() if value
    }

    # 5. 应用 filter_pipe 中的过滤器
    filter_pipe = instruments["filter_pipe"]
    for filter_config in filter_pipe:
        from . import filter as F
        filter_t = getattr(F, filter_config["filter_type"]).from_config(filter_config)
        _instruments_filtered = filter_t(
            _instruments_filtered, start_time, end_time, freq
        )

    # 6. 返回结果
    if as_list:
        return list(_instruments_filtered)
    return _instruments_filtered
```

### 4. 数据加载: LocalDatasetProvider.dataset_processor()

**文件**: `/qlib/data/data.py:587-651`

```python
@staticmethod
def dataset_processor(
    instruments_d,  # ← 过滤后的 instruments_d
    column_names,
    start_time,
    end_time,
    freq,
    inst_processors=[]
):
    """
    Load and process the data, return the data set.
    """
    normalize_column_names = normalize_cache_fields(column_names)
    workers = max(min(C.get_kernels(freq), len(instruments_d)), 1)

    # 创建迭代器
    if isinstance(instruments_d, dict):
        it = instruments_d.items()  # ← {(stock, spans), ...}
    else:
        it = zip(instruments_d, [None] * len(instruments_d))

    inst_l = []
    task_l = []

    # ← 为每只股票创建加载数据的任务
    for inst, spans in it:
        inst_l.append(inst)
        task_l.append(
            delayed(DatasetProvider.inst_calculator)(
                inst,       # ← 股票代码
                start_time, # ← 过滤后的开始时间
                end_time,   # ← 过滤后的结束时间
                freq,
                normalize_column_names,
                spans,      # ← 有效时间段
                C,
                inst_processors,
            )
        )

    # 并行加载数据
    data = dict(
        zip(
            inst_l,
            ParallelExt(n_jobs=workers, backend=C.joblib_backend)(task_l),
        )
    )

    # 移除空数据并合并
    new_data = dict()
    for inst in sorted(data.keys()):
        if len(data[inst]) > 0:
            new_data[inst] = data[inst]

    if len(new_data) > 0:
        data = pd.concat(new_data, names=["instrument"], sort=False)
        data = DiskDatasetCache.cache_to_origin_data(data, column_names)

    return data
```

## 🔑 关键机制总结

### 1. 日期范围过滤 (第768-787行)

```python
# 使用日历边界
cal = Cal.calendar(freq=freq)
start_time = pd.Timestamp(start_time or cal[0])
end_time = pd.Timestamp(end_time or cal[-1])

# 对每只股票的每个时间段进行过滤
_instruments_filtered = {
    inst: list(
        filter(
            lambda x: x[0] <= x[1],  # 确保 start <= end
            [
                (
                    max(start_time, pd.Timestamp(x[0])),  # 取较晚的开始时间
                    min(end_time, pd.Timestamp(x[1]))     # 取较早的结束时间
                )
                for x in spans  # 遍历该股票的所有时间段
            ]
        )
    )
    for inst, spans in _instruments.items()
}
```

**过滤逻辑**:
- 如果股票的时间段 `[(start_1, end_1), (start_2, end_2), ...]`
- 与查询时间范围 `[start_time, end_time]` 取交集
- 只保留有交集的时间段

### 2. 数据文件格式

```
~/.qlib/qlib_data/cn_data/instruments/csi300.txt:
    SZ000001    2005-04-08    2005-06-30
    SZ000002    2005-04-08    2005-06-30
    SH600000    2005-04-08    2099-12-31    ← 一直在指数中
    SH600036    2010-01-04    2020-12-31    ← 只在指数中10年
    ...
```

### 3. 实际过滤示例

```python
# 查询参数
instruments = {'market': 'csi300', 'filter_pipe': []}
start_time = '2024-01-01'
end_time = '2024-12-31'

# 对某只股票 SH600036 的时间段: [(2010-01-04, 2020-12-31)]
# 查询范围: [2024-01-01, 2024-12-31]

# 过滤后: []
# 因为 2020-12-31 < 2024-01-01，该股票不在查询范围内

# 对某只股票 SH600000 的时间段: [(2005-04-08, 2099-12-31)]
# 查询范围: [2024-01-01, 2024-12-31]

# 过滤后: [(2024-01-01, 2024-12-31)]
# 取交集后得到有效时间段
```

## 📋 源码文件索引

| 功能 | 文件 | 行号 |
|------|------|------|
| `D.features()` 入口 | `data.py` | 1305-1346 |
| `DatasetD.dataset()` | `data.py` | 1000-1033 |
| `get_instruments_d()` 判断 | `data.py` | 548-568 |
| `list_instruments()` 过滤 | `data.py` | 756-802 |
| `dataset_processor()` 加载 | `data.py` | 587-651 |
| `inst_calculator()` 单股 | `data.py` | 654-684 |

## 💡 为什么会自动过滤？

1. **`D.instruments('csi300')`** 返回的是**配置字典**
   ```python
   {'market': 'csi300', 'filter_pipe': []}
   ```

2. **`get_instruments_d()`** 识别到这是配置，调用 `Inst.list_instruments()`

3. **`list_instruments()`** 执行：
   - 加载 `csi300.txt` 文件（包含历史所有成分股）
   - 根据 `start_time` 和 `end_time` 过滤有效时间段
   - 应用 `filter_pipe` 中的额外过滤器

4. **`dataset_processor()`** 只为过滤后的股票加载数据

## ⚠️ 重要注意事项

### 用户看到的股票数量 != CSI300的300只

**原因**:
1. **查询日期范围**: 如果查询 2024-01-01 到 2024-12-31，可能只有部分股票在该时间段有效
2. **成分股变动**: CSI300 的成分股会定期调整
3. **数据可用性**: 某些股票可能在查询时间段内停牌或退市

### 如何获取完整列表？

```python
# 方法1：获取当前时刻的所有有效股票
instruments = Inst.list_instruments(
    instruments={'market': 'csi300', 'filter_pipe': []},
    freq='day',
    as_list=True  # 返回列表而不是字典
)
print(f"当前有效股票数: {len(instruments)}")

# 方法2：查看数据加载后的股票数量
df = D.features(
    instruments=D.instruments('csi300'),
    fields=['$close'],
    start_time='2024-01-01',
    end_time='2024-12-31',
    freq='day'
)
print(f"查询范围内的股票数: {df.reset_index()['instrument'].nunique()}")
```
