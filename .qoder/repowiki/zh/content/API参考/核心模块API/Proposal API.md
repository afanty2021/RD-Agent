# Proposal API 文档

<cite>
**本文档引用的文件**
- [core/proposal.py](file://rdagent/core/proposal.py)
- [scenarios/data_science/proposal/exp_gen/base.py](file://rdagent/scenarios/data_science/proposal/exp_gen/base.py)
- [scenarios/data_science/proposal/exp_gen/naive.py](file://rdagent/scenarios/data_science/proposal/exp_gen/naive.py)
- [scenarios/data_science/proposal/exp_gen/diversity_strategy.py](file://rdagent/scenarios/data_science/proposal/exp_gen/diversity_strategy.py)
- [scenarios/data_science/proposal/exp_gen/idea_pool.py](file://rdagent/scenarios/data_science/proposal/exp_gen/idea_pool.py)
- [scenarios/data_science/proposal/exp_gen/proposal.py](file://rdagent/scenarios/data_science/proposal/exp_gen/proposal.py)
- [scenarios/data_science/proposal/exp_gen/select/submit.py](file://rdagent/scenarios/data_science/proposal/exp_gen/select/submit.py)
- [scenarios/data_science/proposal/exp_gen/utils.py](file://rdagent/scenarios/data_science/proposal/exp_gen/utils.py)
- [scenarios/data_science/proposal/exp_gen/merge.py](file://rdagent/scenarios/data_science/proposal/exp_gen/merge.py)
- [core/knowledge_base.py](file://rdagent/core/knowledge_base.py)
</cite>

## 目录
1. [简介](#简介)
2. [核心架构](#核心架构)
3. [Proposal 类详解](#proposal-类详解)
4. [BaseProposalModel 抽象类](#baseproposalmodel-抽象类)
5. [提案生成策略](#提案生成策略)
6. [知识库交互机制](#知识库交互机制)
7. [提案选择与合并](#提案选择与合并)
8. [多轮迭代演化](#多轮迭代演化)
9. [扩展指南](#扩展指南)
10. [最佳实践](#最佳实践)

## 简介

Proposal系统是RD-Agent框架的核心组件，负责生成、评估、选择和合并实验提案。该系统采用基于LLM的智能提案生成机制，支持多种策略组合，并通过知识库进行经验积累和传承。

### 主要特性

- **智能提案生成**：基于场景描述和历史反馈生成创新性实验方案
- **多样化策略**：支持naive、diversity等多种提案生成策略
- **知识库集成**：通过知识库存储和检索历史经验
- **多轮演化**：支持提案的迭代优化和合并
- **灵活选择**：提供多种实验选择策略

## 核心架构

```mermaid
graph TB
subgraph "提案生成层"
ExpGen[ExpGen 基类]
NaiveExpGen[NaiveExpGen]
DSProposalV2ExpGen[DSProposalV2ExpGen]
end
subgraph "提案处理层"
DSHypothesis[DSHypothesis]
DSTrace[DSTrace]
TraceAnalysis[TraceAnalysis]
end
subgraph "知识库层"
KnowledgeBase[KnowledgeBase]
DSKnowledgeBase[DSKnowledgeBase]
IdeaPool[IdeaPool]
end
subgraph "选择与合并层"
SOTASelector[SOTA Selector]
MergeExpGen[MergeExpGen]
DiversityStrategy[DiversityStrategy]
end
ExpGen --> DSHypothesis
DSHypothesis --> DSTrace
DSTrace --> KnowledgeBase
KnowledgeBase --> DSKnowledgeBase
DSKnowledgeBase --> IdeaPool
ExpGen --> SOTASelector
SOTASelector --> MergeExpGen
DSProposalV2ExpGen --> DiversityStrategy
```

**图表来源**
- [core/proposal.py](file://rdagent/core/proposal.py#L294-L333)
- [scenarios/data_science/proposal/exp_gen/base.py](file://rdagent/scenarios/data_science/proposal/exp_gen/base.py#L12-L51)
- [scenarios/data_science/proposal/exp_gen/idea_pool.py](file://rdagent/scenarios/data_science/proposal/exp_gen/idea_pool.py#L54-L86)

## Proposal 类详解

### Hypothesis 基础类

Hypothesis类是所有提案的基础抽象，包含提案的核心属性：

```mermaid
classDiagram
class Hypothesis {
+string hypothesis
+string reason
+string concise_reason
+string concise_observation
+string concise_justification
+string concise_knowledge
+__init__(hypothesis, reason, concise_reason, concise_observation, concise_justification, concise_knowledge)
+__str__() string
}
class DSHypothesis {
+COMPONENT component
+string problem_name
+string problem_desc
+string problem_label
+string appendix
+__init__(component, hypothesis, reason, concise_reason, concise_observation, concise_justification, concise_knowledge, problem_name, problem_desc, problem_label, appendix)
+__str__() string
}
class ExperimentFeedback {
+bool decision
+string reason
+string code_change_summary
+string eda_improvement
+Exception exception
+__init__(reason, code_change_summary, decision, eda_improvement, exception)
+__bool__() bool
+from_exception(exception) ExperimentFeedback
}
class HypothesisFeedback {
+string observations
+string hypothesis_evaluation
+string new_hypothesis
+bool acceptable
+__init__(observations, hypothesis_evaluation, new_hypothesis, reason, code_change_summary, decision, eda_improvement, acceptable)
+__str__() string
}
Hypothesis <|-- DSHypothesis
ExperimentFeedback <|-- HypothesisFeedback
```

**图表来源**
- [core/proposal.py](file://rdagent/core/proposal.py#L18-L38)
- [scenarios/data_science/proposal/exp_gen/base.py](file://rdagent/scenarios/data_science/proposal/exp_gen/base.py#L12-L51)

### DSHypothesis 属性详解

| 属性名 | 类型 | 描述 | 必需 |
|--------|------|------|------|
| hypothesis | str | 提案的核心假设陈述 | 是 |
| reason | str | 提案生成的原因和背景 | 是 |
| concise_reason | str | 简洁版本的原因说明 | 否 |
| concise_observation | str | 简洁的观察结果 | 否 |
| concise_justification | str | 简洁的合理性说明 | 否 |
| concise_knowledge | str | 简洁的知识点总结 | 否 |
| component | COMPONENT | 关联的组件类型 | 是 |
| problem_name | str | 目标问题名称 | 否 |
| problem_desc | str | 问题描述 | 否 |
| problem_label | str | 问题标签（SCENARIO_PROBLEM/FEEDBACK_PROBLEM） | 否 |
| appendix | str | 附加信息 | 否 |

**章节来源**
- [scenarios/data_science/proposal/exp_gen/base.py](file://rdagent/scenarios/data_science/proposal/exp_gen/base.py#L12-L51)

## BaseProposalModel 抽象类

### ExpGen 基类

ExpGen是所有提案生成器的抽象基类，定义了提案生成的标准接口：

```mermaid
classDiagram
class ExpGen {
<<abstract>>
+Scenario scen
+__init__(scen)
+gen(trace, plan) Experiment*
+async_gen(trace, loop) Experiment
+reset() void
}
class NaiveExpGen {
+gen(trace, plan) DSExperiment
}
class DSProposalV2ExpGen {
+bool supports_response_schema
+identify_scenario_problem(scenario_desc, sota_exp_desc, exp_gen_plan, sibling_exp) Dict
+identify_feedback_problem(scenario_desc, exp_feedback_list_desc, sota_exp_desc, inject_diverse, sibling_exp) Dict
+identify_problem(current_sub_trace, scenario_desc, sota_exp_desc, exp_feedback_list_desc, inject_diverse, exp_gen_plan, sibling_exp) Dict
+hypothesis_gen(component_desc, scenario_desc, exp_feedback_list_desc, sota_exp_desc, problems, pipeline, enable_idea_pool, is_new_tree, inject_diverse, exp_gen_plan, sibling_exp, former_user_instructions) Dict
+hypothesis_critique(hypothesis_dict, problems_dict, scenario_desc, sota_exp_desc, exp_feedback_list_desc) Dict
+hypothesis_rewrite(hypothesis_dict, critiques_dict, scenario_desc, sota_exp_desc, exp_feedback_list_desc, sibling_exp, former_user_instructions) Dict
}
ExpGen <|-- NaiveExpGen
ExpGen <|-- DSProposalV2ExpGen
```

**图表来源**
- [core/proposal.py](file://rdagent/core/proposal.py#L294-L333)
- [scenarios/data_science/proposal/exp_gen/naive.py](file://rdagent/scenarios/data_science/proposal/exp_gen/naive.py#L13-L56)
- [scenarios/data_science/proposal/exp_gen/proposal.py](file://rdagent/scenarios/data_science/proposal/exp_gen/proposal.py#L519-L799)

### 实现要求

子类必须实现以下方法：

| 方法名 | 参数 | 返回值 | 描述 |
|--------|------|--------|------|
| gen | trace: Trace, plan: ExperimentPlan \| None | Experiment | 生成实验提案的主要方法 |
| async_gen | trace: Trace, loop: LoopBase | Experiment | 异步生成实验提案 |
| reset | 无 | void | 重置提案生成器状态 |

**章节来源**
- [core/proposal.py](file://rdagent/core/proposal.py#L294-L333)

## 提案生成策略

### Naive 策略

Naive策略是最基础的提案生成方式，直接基于当前最佳实验和场景描述生成新提案：

```mermaid
sequenceDiagram
participant Client as 客户端
participant NaiveExpGen as NaiveExpGen
participant SOTA as 最佳实验
participant LLM as LLM后端
Client->>NaiveExpGen : gen(trace, plan)
NaiveExpGen->>SOTA : sota_experiment()
SOTA-->>NaiveExpGen : 最佳实验对象
NaiveExpGen->>NaiveExpGen : 构建提示模板
NaiveExpGen->>LLM : build_messages_and_create_chat_completion()
LLM-->>NaiveExpGen : 任务描述
NaiveExpGen->>NaiveExpGen : 创建PipelineTask
NaiveExpGen->>NaiveExpGen : 注入最佳实验代码
NaiveExpGen-->>Client : DSExperiment
```

**图表来源**
- [scenarios/data_science/proposal/exp_gen/naive.py](file://rdagent/scenarios/data_science/proposal/exp_gen/naive.py#L13-L56)

### V2 策略（推荐）

V2策略采用更复杂的多阶段生成过程：

```mermaid
flowchart TD
Start([开始提案生成]) --> IdentifyProblems[识别问题]
IdentifyProblems --> ScenarioProblems{场景问题?}
ScenarioProblems --> |是| GenScenarioProblems[生成场景问题]
ScenarioProblems --> |否| FeedbackProblems[识别反馈问题]
GenScenarioProblems --> FeedbackProblems
FeedbackProblems --> HypothesisGen[假设生成]
HypothesisGen --> Critique[假设批评]
Critique --> Rewrite[假设重写]
Rewrite --> Validate{验证通过?}
Validate --> |是| CreateExperiment[创建实验]
Validate --> |否| HypothesisGen
CreateExperiment --> End([返回实验])
```

**图表来源**
- [scenarios/data_science/proposal/exp_gen/proposal.py](file://rdagent/scenarios/data_science/proposal/exp_gen/proposal.py#L519-L799)

### 多样性策略

系统支持多种多样性注入策略：

| 策略类 | 描述 | 触发条件 |
|--------|------|----------|
| AlwaysInjectStrategy | 总是注入多样性上下文 | 每次生成时 |
| InjectAtRootStrategy | 仅在创建新根节点时注入 | 新分支开始时 |
| InjectUntilSOTAGainedStrategy | 直到获得SOTA为止注入 | 当前分支未产生成功实验 |

**章节来源**
- [scenarios/data_science/proposal/exp_gen/diversity_strategy.py](file://rdagent/scenarios/data_science/proposal/exp_gen/diversity_strategy.py#L8-L68)

## 知识库交互机制

### DSKnowledgeBase 结构

```mermaid
classDiagram
class KnowledgeBase {
+Path path
+load() void
+dump() void
}
class DSKnowledgeBase {
+set used_idea_id_set
+add_idea(idea) void
+build_idea_pool(idea_pool_json_path) void
+sample_ideas(problems, scenario_desc, exp_feedback_list_desc, sota_exp_desc, competition_desc) Dict
+update_pickled_problem(problems, pickled_problem_name) void
}
class DSIdea {
+string competition
+string idea
+string method
+string context
+Dict hypothesis
+__init__(raw_knowledge)
+__str__() string
+to_formatted_str() string
}
KnowledgeBase <|-- DSKnowledgeBase
DSKnowledgeBase --> DSIdea
```

**图表来源**
- [core/knowledge_base.py](file://rdagent/core/knowledge_base.py#L8-L27)
- [scenarios/data_science/proposal/exp_gen/idea_pool.py](file://rdagent/scenarios/data_science/proposal/exp_gen/idea_pool.py#L54-L185)

### 知识库使用流程

```mermaid
sequenceDiagram
participant Proposal as 提案生成器
participant KB as 知识库
participant LLM as LLM后端
Proposal->>KB : sample_ideas(problems, ...)
KB->>KB : semantic_search(node, constraint_labels)
KB->>KB : 获取相似想法
KB->>LLM : 构建提示模板
LLM-->>KB : 选择最佳想法
KB->>KB : update_pickled_problem()
KB-->>Proposal : 更新的问题字典
```

**图表来源**
- [scenarios/data_science/proposal/exp_gen/idea_pool.py](file://rdagent/scenarios/data_science/proposal/exp_gen/idea_pool.py#L125-L185)

**章节来源**
- [scenarios/data_science/proposal/exp_gen/idea_pool.py](file://rdagent/scenarios/data_science/proposal/exp_gen/idea_pool.py#L54-L185)

## 提案选择与合并

### SOTA 选择策略

系统提供多种SOTA实验选择策略：

| 策略类 | 特点 | 适用场景 |
|--------|------|----------|
| GlobalSOTASelector | 全局最优选择 | 简单场景，计算资源充足 |
| AutoSOTAexpSelector | LLM辅助选择 | 复杂场景，需要智能决策 |
| BestValidSelector | 基于性能排序 | 需要快速筛选候选实验 |
| ValidationSelector | 验证后选择 | 对结果准确性要求极高 |

### 合并机制

```mermaid
flowchart TD
MultiTrace[多轨迹合并] --> SelectTraces[选择轨迹]
SelectTraces --> CompareExps[比较实验]
CompareExps --> GenerateHypothesis[生成合并假设]
GenerateHypothesis --> CreateTask[创建合并任务]
CreateTask --> InjectCode[注入代码]
InjectCode --> ReturnExperiment[返回合并实验]
```

**图表来源**
- [scenarios/data_science/proposal/exp_gen/merge.py](file://rdagent/scenarios/data_science/proposal/exp_gen/merge.py#L18-L122)

**章节来源**
- [scenarios/data_science/proposal/exp_gen/select/submit.py](file://rdagent/scenarios/data_science/proposal/exp_gen/select/submit.py#L30-L200)
- [scenarios/data_science/proposal/exp_gen/merge.py](file://rdagent/scenarios/data_science/proposal/exp_gen/merge.py#L18-L447)

## 多轮迭代演化

### DSTrace 跟踪机制

DSTrace类管理提案的完整演化历史：

```mermaid
classDiagram
class Trace~ASpecificScen, ASpecificKB~ {
+ASpecificScen scen
+list hist
+list dag_parent
+dict idx2loop_id
+tuple current_selection
+ASpecificKB knowledge_base
+get_sota_hypothesis_and_experiment() tuple
+is_selection_new_tree(selection) bool
+get_current_selection() tuple
+set_current_selection(selection) void
+get_parent_exps(selection) list
}
class DSTrace {
+DSExperiment sota_exp_to_submit
+dict uncommitted_experiments
+should_inject_diversity(current_selection) bool
+register_uncommitted_exp(exp, loop_id) void
+deregister_uncommitted_exp(loop_id) void
+set_sota_exp_to_submit(exp) void
+get_leaves() list
+get_sibling_exps(current_selection) list
+sync_dag_parent_and_hist(exp_and_fb, cur_loop_id) void
+retrieve_search_list(search_type, selection) list
+next_incomplete_component(search_type) COMPONENT
+has_component(component, search_list) bool
+experiment_and_feedback_list_after_init(return_type, search_type, selection, max_retrieve_num) list
+sota_experiment_fb(search_type, selection) tuple
+last_successful_exp(search_type, selection) DSExperiment
+last_exp(search_type) DSExperiment
+last_exp_fb(search_type, selection) tuple
+last_runnable_exp_fb(search_type) tuple
}
Trace <|-- DSTrace
```

**图表来源**
- [core/proposal.py](file://rdagent/core/proposal.py#L88-L292)
- [scenarios/data_science/proposal/exp_gen/base.py](file://rdagent/scenarios/data_science/proposal/exp_gen/base.py#L54-L347)

### 演化路径管理

```mermaid
graph TD
Root[根节点] --> Branch1[分支1]
Root --> Branch2[分支2]
Branch1 --> SubBranch1[子分支1]
Branch1 --> SubBranch2[子分支2]
Branch2 --> SubBranch3[子分支3]
style Root fill:#e1f5fe
style Branch1 fill:#f3e5f5
style Branch2 fill:#f3e5f5
style SubBranch1 fill:#fff3e0
style SubBranch2 fill:#fff3e0
style SubBranch3 fill:#fff3e0
```

**章节来源**
- [scenarios/data_science/proposal/exp_gen/base.py](file://rdagent/scenarios/data_science/proposal/exp_gen/base.py#L54-L347)

## 扩展指南

### 自定义提案生成器

创建自定义提案生成器的步骤：

1. **继承 ExpGen 基类**
2. **实现 gen 方法**
3. **处理异常情况**
4. **集成知识库**

```python
# 示例：自定义提案生成器
class CustomExpGen(ExpGen):
    def gen(self, trace: DSTrace, plan: DSExperimentPlan | None = None) -> DSExperiment:
        # 实现自定义逻辑
        pass
```

### 添加新的多样性策略

```python
# 示例：自定义多样性策略
class CustomDiversityStrategy(DiversityContextStrategy):
    def should_inject(self, trace: DSTrace, local_selection: tuple[int, ...]) -> bool:
        # 实现自定义逻辑
        pass
```

### 集成新的知识库

```python
# 示例：自定义知识库
class CustomKnowledgeBase(KnowledgeBase):
    def add_custom_entry(self, entry: Any) -> None:
        # 实现自定义知识库操作
        pass
```

**章节来源**
- [core/proposal.py](file://rdagent/core/proposal.py#L294-L333)
- [scenarios/data_science/proposal/exp_gen/diversity_strategy.py](file://rdagent/scenarios/data_science/proposal/exp_gen/diversity_strategy.py#L8-L68)

## 最佳实践

### 提案质量优化

1. **明确问题定义**：确保每个提案都针对具体问题
2. **合理利用知识库**：充分利用历史经验和最佳实践
3. **多样性保证**：避免过度依赖单一策略
4. **渐进式改进**：从简单策略开始，逐步增加复杂度

### 性能优化建议

1. **缓存机制**：合理使用API调用缓存
2. **异步处理**：对于耗时操作使用异步模式
3. **资源管理**：控制并发数量和内存使用
4. **错误处理**：实现完善的异常处理机制

### 调试和监控

1. **日志记录**：详细记录提案生成过程
2. **指标跟踪**：监控提案质量和成功率
3. **可视化**：使用图表展示演化路径
4. **回滚机制**：提供失败时的恢复选项

### 集成注意事项

1. **配置管理**：合理设置各种参数阈值
2. **版本兼容**：确保向后兼容性
3. **测试覆盖**：编写充分的单元测试
4. **文档维护**：及时更新API文档

通过遵循这些最佳实践，可以最大化Proposal系统的效能，实现高质量的实验提案生成和优化。