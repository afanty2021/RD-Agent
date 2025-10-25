# 因子Coder API 详细文档

<cite>
**本文档引用的文件**
- [factor.py](file://rdagent/app/qlib_rd_loop/factor.py)
- [evolving_strategy.py](file://rdagent/components/coder/factor_coder/evolving_strategy.py)
- [factor_execution_template.txt](file://rdagent/components/coder/factor_coder/factor_execution_template.txt)
- [prompts.yaml](file://rdagent/components/coder/factor_coder/prompts.yaml)
- [factor.py](file://rdagent/components/coder/factor_coder/factor.py)
- [factor_proposal.py](file://rdagent/scenarios/qlib/proposal/factor_proposal.py)
- [conf.py](file://rdagent/app/qlib_rd_loop/conf.py)
- [config.py](file://rdagent/components/coder/factor_coder/config.py)
- [factor_experiment.py](file://rdagent/scenarios/qlib/experiment/factor_experiment.py)
- [factor_runner.py](file://rdagent/scenarios/qlib/developer/factor_runner.py)
- [factor_coder.py](file://rdagent/scenarios/qlib/developer/factor_coder.py)
</cite>

## 目录
1. [简介](#简介)
2. [系统架构概览](#系统架构概览)
3. [核心组件分析](#核心组件分析)
4. [因子表达式构造逻辑](#因子表达式构造逻辑)
5. [演化策略实现](#演化策略实现)
6. [代码模板注入机制](#代码模板注入机制)
7. [提示工程与LLM交互](#提示工程与llm交互)
8. [因子生成任务配置](#因子生成任务配置)
9. [执行与评估闭环](#执行与评估闭环)
10. [与FactorProposal和FactorRunner集成](#与factorproposal和factorrunner集成)
11. [实际调用示例](#实际调用示例)
12. [总结](#总结)

## 简介

因子Coder是基于Qlib框架的量化金融因子自动化生成系统，专门设计用于在量化投资场景下自动生成Alpha因子代码。该系统通过结合提示工程（Prompt Engineering）、演化策略（Evolving Strategy）和代码模板注入机制，实现了从因子概念到可执行代码的完整自动化流程。

系统的核心目标是：
- 基于自然语言描述自动生成符合Alpha因子规范的Python代码
- 通过迭代优化确保生成的因子具有统计显著性和市场有效性
- 提供完整的因子开发、测试和部署流水线
- 支持复杂的金融数据处理和因子计算逻辑

## 系统架构概览

因子Coder系统采用分层架构设计，主要包含以下核心层次：

```mermaid
graph TB
subgraph "用户接口层"
CLI[命令行接口]
Config[配置管理]
end
subgraph "工作流管理层"
RDLoop[因子研发循环]
FactorExp[因子实验]
FactorTask[因子任务]
end
subgraph "代码生成层"
FactorCoder[因子编码器]
EvolvingStrategy[演化策略]
Prompts[提示工程]
end
subgraph "执行环境层"
FactorWorkspace[因子工作空间]
ExecutionTemplate[执行模板]
DataEngine[数据引擎]
end
subgraph "评估反馈层"
FactorRunner[因子运行器]
Evaluators[评估器]
Feedback[反馈系统]
end
CLI --> RDLoop
Config --> FactorExp
RDLoop --> FactorExp
FactorExp --> FactorTask
FactorTask --> FactorCoder
FactorCoder --> EvolvingStrategy
FactorCoder --> Prompts
EvolvingStrategy --> FactorWorkspace
FactorWorkspace --> ExecutionTemplate
FactorWorkspace --> DataEngine
FactorWorkspace --> FactorRunner
FactorRunner --> Evaluators
Evaluators --> Feedback
```

**图表来源**
- [factor.py](file://rdagent/app/qlib_rd_loop/factor.py#L1-L61)
- [factor_experiment.py](file://rdagent/scenarios/qlib/experiment/factor_experiment.py#L1-L91)
- [evolving_strategy.py](file://rdagent/components/coder/factor_coder/evolving_strategy.py#L1-L174)

## 核心组件分析

### FactorRDLoop - 因子研发循环

FactorRDLoop是系统的核心控制器，继承自通用的RDLoop类，专门负责因子研发的迭代流程。

```mermaid
classDiagram
class FactorRDLoop {
+tuple skip_loop_error
+running(prev_out) dict
}
class RDLoop {
+run(step_n, loop_n, all_duration)
+load(path, checkout)
}
class FactorEmptyError {
+message : str
}
FactorRDLoop --|> RDLoop
FactorRDLoop --> FactorEmptyError : "raises"
```

**图表来源**
- [factor.py](file://rdagent/app/qlib_rd_loop/factor.py#L15-L30)

**章节来源**
- [factor.py](file://rdagent/app/qlib_rd_loop/factor.py#L1-L61)

### FactorTask - 因子任务定义

FactorTask封装了单个因子的所有相关信息，包括名称、描述、公式和变量定义。

```mermaid
classDiagram
class FactorTask {
+str factor_name
+str factor_description
+str factor_formulation
+dict variables
+str factor_resources
+bool factor_implementation
+get_task_information() str
+get_task_brief_information() str
+get_task_information_and_implementation_result() dict
+from_dict(dict) FactorTask
}
class CoSTEERTask {
+str name
+str description
+str *args
+dict **kwargs
}
FactorTask --|> CoSTEERTask
```

**图表来源**
- [factor.py](file://rdagent/components/coder/factor_coder/factor.py#L15-L76)

**章节来源**
- [factor.py](file://rdagent/components/coder/factor_coder/factor.py#L15-L76)

### FactorFBWorkspace - 因子工作空间

FactorFBWorkspace负责因子代码的执行环境管理，包括数据准备、代码执行和结果输出。

```mermaid
sequenceDiagram
participant Client as 客户端
participant Workspace as FactorFBWorkspace
participant Template as 执行模板
participant Executor as Python执行器
participant Data as 数据源
Client->>Workspace : execute()
Workspace->>Workspace : before_execute()
Workspace->>Data : 准备输入数据
Workspace->>Template : 注入因子代码
Workspace->>Executor : 执行Python脚本
Executor-->>Workspace : 返回执行结果
Workspace->>Workspace : 读取result.h5
Workspace-->>Client : 返回因子值DataFrame
```

**图表来源**
- [factor.py](file://rdagent/components/coder/factor_coder/factor.py#L89-L226)

**章节来源**
- [factor.py](file://rdagent/components/coder/factor_coder/factor.py#L76-L231)

## 因子表达式构造逻辑

### 因子表达式结构

因子表达式是系统的核心抽象，包含了因子的完整数学描述和实现信息：

| 组件 | 类型 | 描述 | 示例 |
|------|------|------|------|
| factor_name | str | 因子唯一标识符 | "Momentum_1M" |
| factor_description | str | 因子功能描述 | "基于过去1个月收益率的动量因子" |
| factor_formulation | str | 数学公式表达式 | "$M_t = \frac{P_t}{P_{t-20}} - 1$" |
| variables | dict | 变量定义映射 | {"price": "收盘价序列", "period": "回望期"} |
| factor_resources | str | 资源引用路径 | "data/fundamental/" |

### 表达式验证机制

系统通过多层次验证确保因子表达式的正确性：

```mermaid
flowchart TD
Start([因子表达式输入]) --> Parse["解析因子公式"]
Parse --> ValidateVars["验证变量定义"]
ValidateVars --> CheckMath["检查数学合法性"]
CheckMath --> TypeCheck["类型兼容性检查"]
TypeCheck --> SemanticCheck["语义一致性验证"]
SemanticCheck --> Success{"验证通过?"}
Success --> |是| GenerateCode["生成Python代码"]
Success --> |否| ErrorReport["报告验证错误"]
GenerateCode --> ExecuteTest["执行测试"]
ExecuteTest --> Output["返回因子值"]
ErrorReport --> Retry["重新输入"]
Retry --> Parse
```

**章节来源**
- [factor.py](file://rdagent/components/coder/factor_coder/factor.py#L50-L76)

## 演化策略实现

### 多进程演化策略

FactorMultiProcessEvolvingStrategy是系统的核心演化算法，基于CoSTEER框架实现智能代码生成。

```mermaid
classDiagram
class FactorMultiProcessEvolvingStrategy {
+int num_loop
+bool haveSelected
+error_summary(...) str
+implement_one_task(...) str
+assign_code_list_to_evo(...) EvolvingSubject
}
class MultiProcessEvolvingStrategy {
+assign_code_list_to_evo(...)
}
class CoSTEERQueriedKnowledge {
+task_to_similar_task_successful_knowledge
+task_to_former_failed_traces
}
FactorMultiProcessEvolvingStrategy --|> MultiProcessEvolvingStrategy
FactorMultiProcessEvolvingStrategy --> CoSTEERQueriedKnowledge : "使用"
```

**图表来源**
- [evolving_strategy.py](file://rdagent/components/coder/factor_coder/evolving_strategy.py#L15-L174)

### 智能代码生成流程

演化策略通过以下步骤实现智能代码生成：

```mermaid
sequenceDiagram
participant Strategy as 演化策略
participant Knowledge as 知识库
participant LLM as 大语言模型
participant Validator as 代码验证器
Strategy->>Knowledge : 查询相似成功案例
Strategy->>Knowledge : 获取失败历史记录
Strategy->>LLM : 构建生成提示
LLM-->>Strategy : 返回候选代码
Strategy->>Validator : 验证代码质量
Validator-->>Strategy : 返回验证结果
Strategy->>Strategy : 更新知识库
Strategy->>Strategy : 决定是否接受新代码
```

**图表来源**
- [evolving_strategy.py](file://rdagent/components/coder/factor_coder/evolving_strategy.py#L50-L150)

**章节来源**
- [evolving_strategy.py](file://rdagent/components/coder/factor_coder/evolving_strategy.py#L15-L174)

## 代码模板注入机制

### 执行模板结构

factor_execution_template.txt定义了因子代码的标准执行框架：

```mermaid
graph LR
subgraph "模板结构"
A[导入模块] --> B[加载验证数据]
B --> C[实例化特征工程类]
C --> D[拟合模型]
D --> E[转换数据]
E --> F[保存结果]
end
subgraph "关键组件"
G[pandas] --> H[numpy]
H --> I[feature_engineering_cls]
I --> J[X_valid.pkl]
J --> K[result.h5]
end
A -.-> G
B -.-> J
C -.-> I
D -.-> I
E -.-> I
F -.-> K
```

**图表来源**
- [factor_execution_template.txt](file://rdagent/components/coder/factor_coder/factor_execution_template.txt#L1-L16)

### 模板注入过程

模板注入通过以下机制实现动态代码生成：

| 步骤 | 操作 | 目的 |
|------|------|------|
| 1 | 读取模板内容 | 获取标准执行框架 |
| 2 | 注入因子代码 | 将用户生成的因子代码嵌入模板 |
| 3 | 创建临时脚本 | 在工作空间中生成可执行脚本 |
| 4 | 设置执行环境 | 配置Python路径和依赖 |
| 5 | 执行代码 | 运行完整的因子计算流程 |
| 6 | 收集结果 | 从HDF5文件提取因子值 |

**章节来源**
- [factor.py](file://rdagent/components/coder/factor_coder/factor.py#L159-L165)

## 提示工程与LLM交互

### 提示模板系统

系统通过prompts.yaml文件管理所有提示模板，支持多种场景的代码生成需求。

```mermaid
graph TB
subgraph "提示模板分类"
A[代码反馈提示] --> A1[evaluator_code_feedback_v1_system]
A --> A2[evaluator_code_feedback_v1_user]
B[演化策略提示] --> B1[evolving_strategy_factor_implementation_v1_system]
B --> B2[evolving_strategy_factor_implementation_v2_user]
C[错误总结提示] --> C1[evolving_strategy_error_summary_v2_system]
C --> C2[evolving_strategy_error_summary_v2_user]
D[最终决策提示] --> D1[evaluator_final_decision_v1_system]
D --> D2[evaluator_final_decision_v1_user]
end
subgraph "应用场景"
E[代码质量评估]
F[错误诊断修复]
G[最终效果验证]
end
A1 --> E
B2 --> F
C1 --> F
D1 --> G
D2 --> G
```

**图表来源**
- [prompts.yaml](file://rdagent/components/coder/factor_coder/prompts.yaml#L1-L210)

### 提示工程最佳实践

系统采用以下提示工程原则：

| 原则 | 实现方式 | 效果 |
|------|----------|------|
| 明确指令 | 结构化JSON输出格式 | 减少LLM误解 |
| 上下文丰富 | 包含历史反馈和相似案例 | 提高代码质量 |
| 错误导向 | 专注于关键问题而非细节 | 加快修复速度 |
| 渐进复杂度 | 从简单到复杂的逐步指导 | 降低学习曲线 |

**章节来源**
- [prompts.yaml](file://rdagent/components/coder/factor_coder/prompts.yaml#L1-L210)

## 因子生成任务配置

### 配置参数详解

系统通过FactorCoSTEERSettings类管理所有配置参数：

```mermaid
classDiagram
class FactorCoSTEERSettings {
+str data_folder
+str data_folder_debug
+bool simple_background
+int file_based_execution_timeout
+str select_method
+str python_bin
}
class CoSTEERSettings {
+use_cache : bool
+knowledge_base : str
+evolution_rate : float
}
FactorCoSTEERSettings --|> CoSTEERSettings
```

**图表来源**
- [config.py](file://rdagent/components/coder/factor_coder/config.py#L8-L49)

### 环境配置函数

get_factor_env函数提供了灵活的环境配置能力：

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| conf_type | Optional[str] | None | 配置类型选择 |
| extra_volumes | dict | {} | 额外挂载卷 |
| running_timeout_period | int | 600 | 运行超时时间 |
| enable_cache | Optional[bool] | None | 是否启用缓存 |

**章节来源**
- [config.py](file://rdagent/components/coder/factor_coder/config.py#L25-L49)

## 执行与评估闭环

### 完整执行流程

系统实现了从因子生成到效果评估的完整闭环：

```mermaid
flowchart TD
Start([开始因子实验]) --> GenFactors["生成因子任务"]
GenFactors --> ExecuteFactors["执行因子代码"]
ExecuteFactors --> CollectResults["收集因子结果"]
CollectResults --> Evaluate["评估因子效果"]
Evaluate --> CompareSOTA{"与SOTA比较"}
CompareSOTA --> |优于SOTA| UpdateSOTA["更新最优因子库"]
CompareSOTA --> |不优于SOTA| LearnFromFailures["从失败中学习"]
UpdateSOTA --> FeedbackLoop["反馈循环"]
LearnFromFailures --> FeedbackLoop
FeedbackLoop --> GenFactors
```

**图表来源**
- [factor_runner.py](file://rdagent/scenarios/qlib/developer/factor_runner.py#L60-L184)

### 因子效果评估指标

系统使用多维度指标评估因子性能：

| 指标类别 | 具体指标 | 计算方法 | 重要性 |
|----------|----------|----------|--------|
| 统计指标 | IC值 | 信息系数 | 核心 |
| 收益指标 | 年化收益 | 时间加权回报率 | 关键 |
| 风险指标 | 最大回撤 | 最大亏损幅度 | 重要 |
| 稳定性指标 | Rank IC | 排序信息系数 | 辅助 |

**章节来源**
- [factor_runner.py](file://rdagent/scenarios/qlib/developer/factor_runner.py#L34-L184)

## 与FactorProposal和FactorRunner集成

### FactorProposal集成

FactorProposal负责从研究论文和报告中提取因子概念：

```mermaid
sequenceDiagram
participant Proposal as FactorProposal
participant Parser as 文档解析器
participant TaskGen as 任务生成器
participant FactorTask as 因子任务
Proposal->>Parser : 解析研究报告
Parser-->>Proposal : 提取因子概念
Proposal->>TaskGen : 生成因子任务
TaskGen->>FactorTask : 创建FactorTask对象
FactorTask-->>Proposal : 返回任务列表
```

**图表来源**
- [factor_proposal.py](file://rdagent/scenarios/qlib/proposal/factor_proposal.py#L1-L133)

### FactorRunner集成

FactorRunner负责执行因子实验并提供反馈：

```mermaid
classDiagram
class QlibFactorRunner {
+calculate_information_coefficient(...)
+deduplicate_new_factors(...)
+develop(exp) QlibFactorExperiment
}
class CachedRunner {
+develop(exp) Experiment
+get_cache_key(...)
+assign_cached_result(...)
}
class QlibFactorExperiment {
+experiment_workspace : QlibFBWorkspace
+result : DataFrame
+stdout : str
}
QlibFactorRunner --|> CachedRunner
QlibFactorRunner --> QlibFactorExperiment : "处理"
```

**图表来源**
- [factor_runner.py](file://rdagent/scenarios/qlib/developer/factor_runner.py#L34-L184)

**章节来源**
- [factor_proposal.py](file://rdagent/scenarios/qlib/proposal/factor_proposal.py#L1-L133)
- [factor_runner.py](file://rdagent/scenarios/qlib/developer/factor_runner.py#L34-L184)

## 实际调用示例

### 基础因子生成调用

以下是使用因子Coder生成Alpha因子的基本流程：

```bash
# 启动因子生成循环
python rdagent/app/qlib_rd_loop/factor.py \
    --step_n 1 \
    --loop_n 5 \
    --all_duration "2h"
```

### 高级配置调用

```bash
# 使用特定配置路径启动
python rdagent/app/qlib_rd_loop/factor.py \
    --path "/path/to/session/1/0_propose" \
    --checkout \
    --checkout_path "/custom/path"
```

### 环境变量配置

系统支持通过环境变量进行配置：

| 环境变量 | 默认值 | 描述 |
|----------|--------|------|
| FACTOR_CoSTEER_data_folder | git_ignore_folder/factor_implementation_source_data | 数据文件夹路径 |
| FACTOR_CoSTEER_python_bin | python | Python可执行文件路径 |
| FACTOR_CoSTEER_file_based_execution_timeout | 3600 | 执行超时时间（秒） |

**章节来源**
- [factor.py](file://rdagent/app/qlib_rd_loop/factor.py#L32-L61)

## 总结

因子Coder API是一个功能完备的量化金融因子自动化生成系统，具有以下核心特性：

### 技术优势

1. **智能化代码生成**：基于CoSTEER框架的多进程演化策略，能够智能生成高质量因子代码
2. **完善的评估体系**：提供多维度的因子效果评估和反馈机制
3. **灵活的配置管理**：支持多种环境配置和参数调优
4. **标准化的执行流程**：从因子概念到可执行代码的完整自动化流程

### 应用价值

- **提高因子开发效率**：大幅减少人工编写因子代码的时间成本
- **保证代码质量**：通过迭代优化确保生成的因子具有统计显著性
- **支持复杂金融场景**：能够处理多维度、多层次的因子计算需求
- **促进量化研究创新**：为量化研究员提供强大的工具支持

### 发展方向

未来系统可以在以下方面进一步优化：
- 增强对复杂金融模型的支持
- 扩展多资产类别的因子生成能力
- 优化大规模因子库的管理机制
- 加强与主流量化平台的集成

因子Coder API为量化金融领域的自动化因子开发提供了强有力的技术支撑，是推动量化研究智能化发展的重要工具。