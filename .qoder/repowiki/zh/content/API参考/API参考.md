# API参考

<cite>
**本文档中引用的文件**  
- [evolving_agent.py](file://rdagent/core/evolving_agent.py)
- [scenario.py](file://rdagent/core/scenario.py)
- [experiment.py](file://rdagent/core/experiment.py)
- [developer.py](file://rdagent/core/developer.py)
- [evaluation.py](file://rdagent/core/evaluation.py)
- [cli.py](file://rdagent/app/cli.py)
- [DataScienceScen.py](file://rdagent/scenarios/data_science/scen/__init__.py)
- [CoSTEER.py](file://rdagent/components/coder/CoSTEER/__init__.py)
- [proposal.py](file://rdagent/components/proposal/__init__.py)
- [runner.py](file://rdagent/components/runner/__init__.py)
</cite>

## 目录
1. [简介](#简介)
2. [核心模块](#核心模块)
3. [组件模块](#组件模块)
4. [场景模块](#场景模块)
5. [命令行接口](#命令行接口)

## 简介
RD-Agent是一个自动化研发框架，旨在通过迭代式进化方法实现智能体对复杂任务的自主开发。本API参考文档详细介绍了框架的核心类、组件、场景和命令行接口，为开发者提供完整的公共接口说明。

## 核心模块

### EvolvingAgent类
`EvoAgent`是RD-Agent框架中的核心抽象类，定义了进化智能体的基本接口。该类采用泛型设计，支持不同类型评估器和可进化对象的组合。

**构造函数参数**
- `max_loop` (int): 最大进化循环次数
- `evolving_strategy` (EvolvingStrategy): 进化策略对象

**方法**
- `multistep_evolve(evo, eva)`: 执行多步进化过程，返回生成器对象，允许调用者进行流程控制和日志记录

`RAGEvoAgent`是`EvoAgent`的具体实现，集成了检索增强生成(RAG)功能，支持知识检索和反馈机制。

**构造函数参数**
- `max_loop` (int): 最大进化循环次数
- `evolving_strategy` (EvolvingStrategy): 进化策略对象
- `rag` (Any): RAG检索系统
- `with_knowledge` (bool): 是否启用知识检索
- `with_feedback` (bool): 是否启用反馈机制
- `knowledge_self_gen` (bool): 是否启用知识自生成
- `enable_filelock` (bool): 是否启用文件锁
- `filelock_path` (str | None): 文件锁路径

**方法**
- `multistep_evolve(evo, eva)`: 执行多步进化过程，包含知识检索、进化、评估和知识更新等完整流程

**异常抛出**
- 无显式异常抛出，但可能抛出由底层组件引发的异常

**Section sources**
- [evolving_agent.py](file://rdagent/core/evolving_agent.py#L1-L115)

### Scenario类
`Scenario`类定义了场景的抽象基类，为不同应用场景提供统一的接口规范。

**属性**
- `background` (str): 场景背景信息
- `source_data` (str): 源数据描述
- `rich_style_description` (str): 富文本风格描述
- `experiment_setting` (str | None): 实验设置信息

**方法**
- `get_source_data_desc(task=None)`: 获取源数据描述，可根据具体任务调整
- `get_scenario_all_desc(task=None, filtered_tag=None, simple_background=None)`: 组合所有描述信息
- `get_runtime_environment()`: 获取运行环境信息

**异常抛出**
- 无显式异常抛出

**Section sources**
- [scenario.py](file://rdagent/core/scenario.py#L1-L64)

### Experiment类
`Experiment`类是RD-Agent框架中实验的核心数据结构，用于组织和管理任务序列及其实现。

**构造函数参数**
- `sub_tasks` (Sequence[ASpecificTask]): 子任务序列
- `based_experiments` (Sequence[ASpecificWSForExperiment]): 基于的实验序列
- `hypothesis` (Hypothesis | None): 假设对象

**属性**
- `hypothesis` (Hypothesis | None): 实验假设
- `sub_tasks` (Sequence[ASpecificTask]): 子任务列表
- `sub_workspace_list` (list[ASpecificWSForSubTasks | None]): 子工作区列表
- `based_experiments` (Sequence[ASpecificWSForExperiment]): 基于的实验列表
- `experiment_workspace` (ASpecificWSForExperiment | None): 实验工作区
- `prop_dev_feedback` (Feedback | None): 开发者反馈
- `running_info` (RunningInfo): 运行信息
- `sub_results` (dict[str, float]): 子结果字典
- `local_selection` (tuple[int, ...] | None): 本地选择
- `plan` (ExperimentPlan | None): 实验计划
- `user_instructions` (UserInstructions | None): 用户指令

**方法**
- `set_user_instructions(user_instructions)`: 设置用户指令
- `create_ws_ckp()`: 创建工作区检查点
- `recover_ws_ckp()`: 恢复工作区检查点

**异常抛出**
- 无显式异常抛出

**Section sources**
- [experiment.py](file://rdagent/core/experiment.py#L1-L482)

## 组件模块

### Coder组件
`CoSTEER`是RD-Agent框架中Coder组件的核心实现，继承自`Developer`类，负责代码的生成和进化。

**构造函数参数**
- `settings` (CoSTEERSettings): CoSTEER配置
- `eva` (RAGEvaluator): 评估器
- `es` (EvolvingStrategy): 进化策略
- `evolving_version` (int): 进化版本
- `with_knowledge` (bool): 是否启用知识
- `knowledge_self_gen` (bool): 是否启用知识自生成
- `max_loop` (int | None): 最大循环次数

**方法**
- `get_develop_max_seconds()`: 获取开发最大秒数
- `_get_last_fb()`: 获取最后的反馈
- `should_use_new_evo(base_fb, new_fb)`: 判断是否使用新的进化结果
- `develop(exp)`: 开发实验
- `_exp_postprocess_by_feedback(evo, feedback)`: 根据反馈对实验进行后处理

**异常抛出**
- `CoderError`: 当所有任务都失败时抛出

**Section sources**
- [CoSTEER.py](file://rdagent/components/coder/CoSTEER/__init__.py#L1-L176)

### Runner组件
`CachedRunner`是RD-Agent框架中Runner组件的实现，通过缓存机制优化实验执行。

**构造函数参数**
- `*args, **kwargs`: 传递给父类的参数

**方法**
- `get_cache_key(exp)`: 获取缓存键
- `assign_cached_result(exp, cached_res)`: 分配缓存结果

**异常抛出**
- 无显式异常抛出

**Section sources**
- [runner.py](file://rdagent/components/runner/__init__.py#L1-L20)

### Proposal组件
`LLMHypothesisGen`和`LLMHypothesis2Experiment`是RD-Agent框架中Proposal组件的核心类，负责从假设生成到实验的转换。

**LLMHypothesisGen类**
- `__init__(scen)`: 构造函数
- `prepare_context(trace)`: 准备上下文
- `convert_response(response)`: 转换响应
- `gen(trace, plan=None)`: 生成假设

**LLMHypothesis2Experiment类**
- `__init__()`: 构造函数
- `prepare_context(hypothesis, trace)`: 准备上下文
- `convert_response(response, hypothesis, trace)`: 转换响应
- `convert(hypothesis, trace)`: 转换假设为实验

**异常抛出**
- 无显式异常抛出

**Section sources**
- [proposal.py](file://rdagent/components/proposal/__init__.py#L1-L138)

## 场景模块

### DataScienceScen类
`DataScienceScen`是数据科学场景的具体实现，继承自`Scenario`类。

**构造函数参数**
- `competition` (str): 竞赛名称

**属性**
- `competition` (str): 竞赛名称
- `raw_description` (str): 原始描述
- `metric_name` (str | None): 指标名称
- `metric_direction` (bool): 指标方向
- `timeout_increase_count` (int): 超时增加计数

**方法**
- `reanalyze_competition_description()`: 重新分析竞赛描述
- `real_debug_timeout()`: 获取实际调试超时
- `recommend_debug_timeout()`: 获取推荐调试超时
- `real_full_timeout()`: 获取实际完整超时
- `recommend_full_timeout()`: 获取推荐完整超时
- `increase_timeout()`: 增加超时
- `get_competition_full_desc()`: 获取竞赛完整描述
- `get_scenario_all_desc(eda_output=None)`: 获取场景所有描述
- `get_runtime_environment()`: 获取运行环境

**异常抛出**
- `FileNotFoundError`: 当无法找到竞赛数据时抛出

**Section sources**
- [DataScienceScen.py](file://rdagent/scenarios/data_science/scen/__init__.py#L1-L289)

## 命令行接口

### CLI命令
RD-Agent提供了丰富的命令行接口，通过`typer`库实现。

**可用命令**
- `fin_factor`: 运行金融因子进化应用
- `fin_model`: 运行金融模型进化应用
- `fin_quant`: 运行金融量化交易应用
- `fin_factor_report`: 运行基于报告的因子提取应用
- `general_model`: 运行通用模型研究应用
- `data_science`: 运行数据科学应用
- `grade_summary`: 生成评分摘要
- `ui`: 启动Web界面
- `server_ui`: 启动服务器Web界面
- `health_check`: 运行健康检查
- `collect_info`: 收集系统信息
- `ds_user_interact`: 启动数据科学用户交互界面

**选项**
- `--port`: 指定端口号
- `--log_dir`: 指定日志目录
- `--debug`: 启用调试模式
- `--competition`: 指定竞赛名称
- `--report-folder`: 指定报告文件夹路径

**典型调用方式**
```bash
# 运行数据科学应用
rdagent data_science --competition playground-series-s4e8

# 运行金融因子进化应用
rdagent fin_factor

# 运行基于报告的因子提取应用
rdagent fin_factor_report --report-folder=/path/to/reports

# 启动Web界面
rdagent ui --port=8080 --debug
```

**异常处理**
- 命令行接口会捕获并处理底层异常，向用户显示友好的错误信息

**Section sources**
- [cli.py](file://rdagent/app/cli.py#L1-L87)