# CoSTEER框架改进方案

> 创建时间：2025-12-27
> 改进范围：代码生成质量、接口规范理解、错误恢复机制

## 问题分析

### 问题1：代码生成质量 - 导入语句缺失

**现象**：
```
UnboundLocalError: cannot access local variable 'np' where it is not associated with a value
```

**根本原因**：
- LLM生成代码时未包含必要的导入语句
- 提示词中没有强制要求导入模板
- 缺少代码生成后的静态验证

**影响**：
- 代码执行失败
- 进化循环提前终止
- 无法完成多轮迭代

### 问题2：接口规范理解 - 静态命名规范

**现象**：
```
列名 'Volume_Trend_10_30' 包含动态参数 (10, 30)，不符合静态命名要求
```

**根本原因**：
- 接口规范仅在系统提示中说明一次
- 缺少正反面示例对比
- 规范的重要性未被充分强调
- 评估反馈中缺少明确的规范违反提示

**影响**：
- 因子实现不符合Qlib接口要求
- 需要多轮迭代才能理解规范
- 降低整体开发效率

### 问题3：错误恢复机制 - 进程终止

**现象**：
```
Loop 1 在 Step 1 (coding) 阶段因错误而终止
```

**根本原因**：
- `multiprocessing_wrapper` 不捕获代码生成异常
- 单个任务失败导致整个循环终止
- 缺少任务级别的错误隔离
- 失败任务未被正确记录到知识库

**影响**：
- 已成功的任务无法复用
- 无法完成多轮进化
- 系统鲁棒性差

## 已实施的改进

### 改进1：增强导入语句要求 (prompts.yaml)

**位置**：`rdagent/components/coder/factor_coder/prompts.yaml:40-50`

**变更内容**：
```yaml
evolving_strategy_factor_implementation_v1_system: |-
  ...
  CRITICAL: Your code MUST include the following import statements at the beginning:
  ```python
  import pandas as pd
  import numpy as np
  ```
  Do NOT forget these imports - they are required for all factor implementations.
  ...
```

**效果**：
- 在系统提示的最高优先级位置强调导入要求
- 使用 "CRITICAL" 和 "Do NOT forget" 增强语气
- 提供明确的代码模板

### 改进2：添加静态命名规范说明 (prompts.yaml)

**位置**：`rdagent/components/coder/factor_coder/prompts.yaml:59-88`

**变更内容**：
```yaml
  6. CRITICAL: Factor column names MUST be static (without parameters in the name).
     - BAD: 'Volume_Trend_10_30' (contains parameters 10 and 30)
     - GOOD: 'VolumeTrend' (parameters hardcoded in function logic, not in name)
  Example:
    # CORRECT: Static factor name
    def calculate_VolumeTrend():  # Static name - no parameters in function name
        df = pd.read_hdf('daily_pv.h5', key='data')
        df_reset = df.reset_index()
        # Parameters (10, 30) hardcoded in logic, not in name
        df_reset['ma10'] = df_reset.groupby('instrument')['$volume'].transform(lambda x: x.rolling(10).mean())
        df_reset['ma30'] = df_reset.groupby('instrument')['$volume'].transform(lambda x: x.rolling(30).mean())
        df_reset['VolumeTrend'] = df_reset['ma10'] / df_reset['ma30']  # Static column name
        ...
```

**效果**：
- 明确定义静态命名规则
- 提供正反面对比示例
- 展示参数硬编码的正确方式

### 改进3：增强错误恢复机制 (evolving_strategy.py)

**位置**：`rdagent/components/coder/CoSTEER/evolving_strategy.py:209-244`

**变更内容**：
```python
# ==================== 2. 并行执行阶段 ====================
# 增强的错误处理：即使单个任务失败，也不终止整个循环
try:
    result = multiprocessing_wrapper([...])
    for index, target_index in enumerate(to_be_finished_task_index):
        code_list[target_index] = result[index]

except Exception as e:
    # 错误恢复：捕获代码生成阶段的异常，记录失败的任务
    logger.error(f"代码生成阶段发生错误: {type(e).__name__}: {e}")
    logger.error(f"失败的任务索引: {to_be_finished_task_index}")

    # 将失败的任务标记为None，继续执行其他任务
    for target_index in to_be_finished_task_index:
        if code_list[target_index] is None:
            # 记录失败的任务信息，避免在下一轮重复尝试
            task_desc = evo.sub_tasks[target_index].get_task_information()
            queried_knowledge.failed_task_info_set.add(task_desc)
            logger.warning(f"任务 {target_index} ({task_desc[:50]}...) 已标记为失败")
```

**效果**：
- 捕获代码生成阶段的异常
- 将失败任务记录到知识库
- 允许其他任务继续执行
- 避免整个循环终止

## 进一步改进建议

### 架构级改进

#### 1. 代码生成后验证 (Code Post-Validation)

**建议实现**：在 `evolving_strategy.py` 中添加代码验证层

```python
def validate_generated_code(code_dict: dict[str, str]) -> tuple[bool, str]:
    """
    验证生成的代码是否符合基本要求

    检查项：
    1. 必要的导入语句 (pandas, numpy)
    2. 函数命名规范 (无参数)
    3. 列名命名规范 (静态命名)
    4. 基本语法正确性
    """
    for filename, code in code_dict.items():
        # 检查导入语句
        required_imports = ['import pandas as pd', 'import numpy as np']
        for req_import in required_imports:
            if req_import not in code:
                return False, f"缺少必要导入: {req_import}"

        # 检查函数命名规范
        if re.search(r'def calculate_\w+_\d+.*\(', code):
            return False, "函数名包含参数，请使用静态命名"

        # 检查列名规范
        if re.search(r"\[['\"][\w]+_\d+_\d+['\"]", code):
            return False, "列名包含参数，请使用静态命名"

    return True, "验证通过"

# 在 implement_one_task 后调用
def implement_one_task_safe(...):
    code_dict = self.implement_one_task(...)
    is_valid, msg = validate_generated_code(code_dict)
    if not is_valid:
        # 自动修复或返回错误反馈
        logger.warning(f"代码验证失败: {msg}")
        return self._fix_common_issues(code_dict, msg)
    return code_dict
```

#### 2. 知识库驱动的规范学习 (Knowledge-Driven Specification Learning)

**建议实现**：增强知识库以存储规范违反案例

```python
@dataclass
class CoSTEERKnowledge:
    ...
    # 新增：规范违反案例
    specification_violations: dict[str, list[str]] = field(default_factory=dict)
    # 格式: {"静态命名": ["Volume_Trend_10_30", "Momentum_5_20_60"], ...}

    def learn_from_violation(self, violation_type: str, bad_example: str):
        """从规范违反中学习"""
        if violation_type not in self.specification_violations:
            self.specification_violations[violation_type] = []
        self.specification_violations[violation_type].append(bad_example)

    def get_violation_warnings(self, task_desc: str) -> list[str]:
        """获取相关规范警告"""
        warnings = []
        for violation_type, examples in self.specification_violations.items():
            for example in examples:
                if example.lower() in task_desc.lower():
                    warnings.append(f"避免使用 {violation_type}: 不应使用 '{example}'")
        return warnings
```

#### 3. 多级错误恢复策略 (Multi-Level Error Recovery)

**建议实现**：在 `evolving_strategy.py` 中实现分级错误处理

```python
class MultiProcessEvolvingStrategy:
    def evolve(self, evo, queried_knowledge, evolving_trace, **kwargs):
        ...
        # ==================== 2. 并行执行阶段（增强版） ====================
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                result = multiprocessing_wrapper([...])
                break  # 成功则退出重试循环
            except Exception as e:
                retry_count += 1
                logger.warning(f"第 {retry_count} 次重试: {e}")

                if retry_count >= max_retries:
                    # 最终重试失败，启用降级策略
                    logger.error("达到最大重试次数，启用降级模式")
                    return self._fallback_evolution(evo, queried_knowledge, evolving_trace)

                # 部分任务成功：识别并隔离失败的任务
                partial_success, failed_indices = self._identify_partial_success(result)
                if partial_success:
                    logger.info(f"部分成功: {len(failed_indices)} 个任务失败")
                    # 仅重试失败的任务
                    to_be_finished_task_index = failed_indices
                else:
                    # 全部失败，等待后重试
                    time.sleep(2 ** retry_count)  # 指数退避
```

#### 4. 代码生成模板系统 (Template-Based Code Generation)

**建议实现**：创建代码生成模板库

```python
# templates/factor_template.py
FACTOR_CODE_TEMPLATE = """
import pandas as pd
import numpy as np

def calculate_{FACTOR_NAME}():
    '''
    Factor: {FACTOR_NAME}
    Description: {FACTOR_DESCRIPTION}
    '''
    # Read data
    df = pd.read_hdf('daily_pv.h5', key='data')

    # Reset index for processing
    df_reset = df.reset_index()

    # TODO: Implement your factor logic here
    # Remember:
    # 1. Use groupby().transform() for window calculations
    # 2. Use static column names (no parameters in name)
    # 3. Set index names to ['datetime', 'instrument']

    # Save result
    result = df_reset.set_index(['date', 'instrument'])[['{FACTOR_NAME}']]
    result.index.names = ['datetime', 'instrument']
    result.to_hdf('result.h5', key='data', mode='w')

if __name__ == '__main__':
    calculate_{FACTOR_NAME}()
"""

# 在 prompts.yaml 中引用
evolving_strategy_factor_implementation_v1_user: |-
  ...
  Please use the following template and fill in your implementation:

  ```python
  {FACTOR_CODE_TEMPLATE}
  ```

  Replace:
  - {FACTOR_NAME} with your static factor name
  - {FACTOR_DESCRIPTION} with your factor description
  - Implement the TODO section with your logic
```

### 配置级改进

#### 5. 环境变量配置验证

**建议在 `.env` 中添加**：
```env
# 代码生成配置
CODE_GENERATION_VALIDATE=true
CODE_GENERATION_AUTO_FIX=true
CODE_GENERATION_MAX_RETRIES=3

# 规范检查配置
SPECIFICATION_CHECK_STATIC_NAMING=true
SPECIFICATION_CHECK_IMPORTS=true
SPECIFICATION_CHECK_MULTIINDEX=true
```

#### 6. 新增配置类 (config.py)

```python
from pydantic import BaseModel, Field

class CodeGenerationSettings(BaseModel):
    """代码生成配置"""
    validate_before_execution: bool = Field(default=True, description="执行前验证代码")
    auto_fix_common_issues: bool = Field(default=True, description="自动修复常见问题")
    max_retries: int = Field(default=3, ge=1, le=10, description="最大重试次数")
    enable_template: bool = Field(default=True, description="启用代码模板")

class SpecificationSettings(BaseModel):
    """规范检查配置"""
    enforce_static_naming: bool = Field(default=True, description="强制静态命名")
    required_imports: list[str] = Field(
        default=["import pandas as pd", "import numpy as np"],
        description="必需的导入语句"
    )
```

### 测试级改进

#### 7. 添加验证测试用例

```python
# test/utils/coder/test_code_validation.py
import pytest
from rdagent.components.coder.CoSTEER.evolving_strategy import validate_generated_code

def test_validate_missing_imports():
    code = {"factor.py": "def calculate_test():\n    return 1"}
    is_valid, msg = validate_generated_code(code)
    assert not is_valid
    assert "pandas" in msg

def test_validate_static_naming_violation():
    code = {"factor.py": "def calculate_Momentum_5_20():\n    df['Momentum_5_20'] = ..."}
    is_valid, msg = validate_generated_code(code)
    assert not is_valid
    assert "静态命名" in msg or "参数" in msg

def test_validate_correct_code():
    code = {"factor.py": """
import pandas as pd
import numpy as np

def calculate_Momentum():
    df['Momentum'] = df['close'] / df['close'].shift(20) - 1
    return df
    """
    is_valid, msg = validate_generated_code(code)
    assert is_valid
```

## 实施优先级

### 高优先级（立即实施）
1. ✅ 提示词增强（已完成）
2. ✅ 错误捕获机制（已完成）
3. ⏳ 代码生成后验证

### 中优先级（短期实施）
4. 知识库规范学习
5. 多级错误恢复
6. 配置系统扩展

### 低优先级（长期优化）
7. 代码模板系统
8. 测试用例完善
9. 性能优化

## 预期效果

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 导入缺失错误率 | ~30% | <5% |
| 规范违反率 | ~20% | <5% |
| 循环完成率 | 50% (2/4) | >90% |
| 平均迭代轮数 | 1轮 | 2-3轮 |

## 相关文件

- `rdagent/components/coder/factor_coder/prompts.yaml` - 提示词配置
- `rdagent/components/coder/CoSTEER/evolving_strategy.py` - 进化策略
- `rdagent/components/coder/CoSTEER/evaluators.py` - 评估系统
- `rdagent/components/coder/CoSTEER/config.py` - 配置管理

---

*最后更新：2025-12-27*
