# 组件系统API

<cite>
**本文档中引用的文件**
- [CoSTEER/__init__.py](file://rdagent\components\coder\CoSTEER\__init__.py)
- [CoSTEER/config.py](file://rdagent\components\coder\CoSTEER\config.py)
- [CoSTEER/evaluators.py](file://rdagent\components\coder\CoSTEER\evaluators.py)
- [CoSTEER/evolvable_subjects.py](file://rdagent\components\coder\CoSTEER\evolvable_subjects.py)
- [CoSTEER/task.py](file://rdagent\components\coder\CoSTEER\task.py)
- [factor_coder/__init__.py](file://rdagent\components\coder\factor_coder\__init__.py)
- [model_coder/__init__.py](file://rdagent\components\coder\model_coder\__init__.py)
- [runner/__init__.py](file://rdagent\components\runner\__init__.py)
- [proposal/__init__.py](file://rdagent\components\proposal\__init__.py)
- [knowledge_management/vector_base.py](file://rdagent\components\knowledge_management\vector_base.py)
- [knowledge_management/graph.py](file://rdagent\components\knowledge_management\graph.py)
- [data_science/pipeline/__init__.py](file://rdagent\components\coder\data_science\pipeline\__init__.py)
- [data_science/model/__init__.py](file://rdagent\components\coder\data_science\model\__init__.py)
- [data_science/feature/__init__.py](file://rdagent\components\coder\data_science\feature\__init__.py)
- [data_science/ensemble/__init__.py](file://rdagent\components\coder\data_science\ensemble\__init__.py)
</cite>

## 目录
1. [引言](#引言)
2. [Coder组件族](#coder组件族)
3. [Runner组件](#runner组件)
4. [Proposal组件](#proposal组件)
5. [KnowledgeManagement组件](#knowledgemanagement组件)
6. [组件间依赖关系与数据交换](#组件间依赖关系与数据交换)
7. [实际调用示例](#实际调用示例)
8. [结论](#结论)

## 引言
本文档详细说明了RD-Agent系统中components包内所有可复用组件的公共接口。重点介绍基于CoSTEER框架的Coder组件族（包括数据科学Coder、因子Coder、模型Coder）的代码生成流程、配置选项与扩展点；Runner组件的执行环境管理与结果捕获机制；Proposal组件的创意生成策略与多样性控制；以及KnowledgeManagement组件的向量数据库与图谱存储接口。文档为每个组件提供基类定义、抽象方法要求、默认实现和配置参数说明，并包含实际调用示例，展示如何在不同场景下组合使用这些组件。

## Coder组件族

### CoSTEER框架
CoSTEER框架是所有Coder组件的基础，提供了一个基于反馈的迭代式代码生成和演化框架。它继承自`Developer`基类，并实现了`develop`方法来驱动代码的演化过程。

```mermaid
classDiagram
class CoSTEER {
+settings : CoSTEERSettings
+max_loop : int
+knowledge_base_path : Path
+new_knowledge_base_path : Path
+with_knowledge : bool
+knowledge_self_gen : bool
+evolving_strategy : EvolvingStrategy
+evaluator : RAGEvaluator
+evolving_version : int
+rag : CoSTEERRAGStrategyV1|CoSTEERRAGStrategyV2
+get_develop_max_seconds() int | None
+_get_last_fb() CoSTEERMultiFeedback
+should_use_new_evo(base_fb : CoSTEERMultiFeedback | None, new_fb : CoSTEERMultiFeedback) bool
+develop(exp : Experiment) Experiment
+_exp_postprocess_by_feedback(evo : Experiment, feedback : CoSTEERMultiFeedback) Experiment
}
class Developer {
<<abstract>>
+develop(exp : Experiment) Experiment
}
CoSTEER --|> Developer
```

**图源**
- [CoSTEER/__init__.py](file://rdagent\components\coder\CoSTEER\__init__.py#L25-L176)

**节源**
- [CoSTEER/__init__.py](file://rdagent\components\coder\CoSTEER\__init__.py#L25-L176)

### 配置选项
CoSTEER框架的配置通过`CoSTEERSettings`类管理，支持环境变量前缀"CoSTEER_"。主要配置参数包括：

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| coder_use_cache | bool | False | 是否使用缓存 |
| max_loop | int | 10 | 任务实现的最大循环次数 |
| fail_task_trial_limit | int | 20 | 失败任务的重试限制 |
| knowledge_base_path | str | None | 知识库路径 |
| new_knowledge_base_path | str | None | 新知识库路径 |
| enable_filelock | bool | False | 是否启用文件锁 |
| filelock_path | str | None | 文件锁路径 |

```mermaid
classDiagram
class CoSTEERSettings {
+coder_use_cache : bool
+max_loop : int
+fail_task_trial_limit : int
+v1_query_former_trace_limit : int
+v1_query_similar_success_limit : int
+v2_query_component_limit : int
+v2_query_error_limit : int
+v2_query_former_trace_limit : int
+v2_add_fail_attempt_to_latest_successful_execution : bool
+v2_error_summary : bool
+v2_knowledge_sampler : float
+knowledge_base_path : str | None
+new_knowledge_base_path : str | None
+enable_filelock : bool
+filelock_path : str | None
+max_seconds_multiplier : int
}
class ExtendedBaseSettings {
<<abstract>>
}
CoSTEERSettings --|> ExtendedBaseSettings
```

**图源**
- [CoSTEER/config.py](file://rdagent\components\coder\CoSTEER\config.py#L4-L42)

**节源**
- [CoSTEER/config.py](file://rdagent\components\coder\CoSTEER\config.py#L4-L42)

### 代码生成流程
CoSTEER框架的代码生成流程基于反馈驱动的演化策略。`develop`方法是核心入口，它通过`RAGEvoAgent`执行多步演化，每一步都由`evolving_strategy`生成新代码，并由`evaluator`评估结果。

```mermaid
sequenceDiagram
participant Developer as "Developer"
participant CoSTEER as "CoSTEER"
participant EvolveAgent as "RAGEvoAgent"
participant Strategy as "EvolvingStrategy"
participant Evaluator as "RAGEvaluator"
Developer->>CoSTEER : develop(exp)
CoSTEER->>CoSTEER : 初始化中间项
CoSTEER->>EvolveAgent : 创建RAGEvoAgent实例
loop 演化循环
EvolveAgent->>Strategy : implement_one_task()
Strategy-->>EvolveAgent : 返回代码
EvolveAgent->>Evaluator : 评估代码
Evaluator-->>EvolveAgent : 返回反馈
EvolveAgent->>CoSTEER : 更新演化轨迹
alt 达到最大时间限制
CoSTEER->>CoSTEER : 停止演化
break
end
end
CoSTEER->>CoSTEER : 回退到最佳解决方案
CoSTEER->>CoSTEER : 后处理反馈
CoSTEER-->>Developer : 返回演化后的实验
```

**图源**
- [CoSTEER/__init__.py](file://rdagent\components\coder\CoSTEER\__init__.py#L75-L176)

**节源**
- [CoSTEER/__init__.py](file://rdagent\components\coder\CoSTEER\__init__.py#L75-L176)

### 扩展点
CoSTEER框架提供了多个扩展点，允许子类自定义行为：

1. `get_develop_max_seconds()`：获取开发任务的最大秒数
2. `should_use_new_evo()`：决定是否使用新的演化反馈
3. `_exp_postprocess_by_feedback()`：根据反馈对实验进行后处理

### 数据科学Coder
数据科学Coder组件族包括数据加载、特征工程、模型构建和集成学习等子组件，均基于CoSTEER框架实现。

```mermaid
classDiagram
class DSCoSTEER {
<<abstract>>
}
class PipelineCoSTEER {
+__init__(scen : Scenario, *args, **kwargs)
}
class ModelCoSTEER {
+__init__(scen : Scenario, *args, **kwargs)
}
class FeatureCoSTEER {
+__init__(scen : Scenario, *args, **kwargs)
}
class EnsembleCoSTEER {
+__init__(scen : Scenario, *args, **kwargs)
}
PipelineCoSTEER --|> DSCoSTEER
ModelCoSTEER --|> DSCoSTEER
FeatureCoSTEER --|> DSCoSTEER
EnsembleCoSTEER --|> DSCoSTEER
```

**图源**
- [data_science/pipeline/__init__.py](file://rdagent\components\coder\data_science\pipeline\__init__.py#L100-L165)
- [data_science/model/__init__.py](file://rdagent\components\coder\data_science\model\__init__.py#L150-L173)
- [data_science/feature/__init__.py](file://rdagent\components\coder\data_science\feature\__init__.py#L117-L140)
- [data_science/ensemble/__init__.py](file://rdagent\components\coder\data_science\ensemble\__init__.py#L141-L164)

**节源**
- [data_science/pipeline/__init__.py](file://rdagent\components\coder\data_science\pipeline\__init__.py#L100-L165)
- [data_science/model/__init__.py](file://rdagent\components\coder\data_science\model\__init__.py#L150-L173)
- [data_science/feature/__init__.py](file://rdagent\components\coder\data_science\feature\__init__.py#L117-L140)
- [data_science/ensemble/__init__.py](file://rdagent\components\coder\data_science\ensemble\__init__.py#L141-L164)

### 因子Coder
因子Coder组件`FactorCoSTEER`专门用于因子生成和优化，继承自`CoSTEER`基类。

```mermaid
classDiagram
class FactorCoSTEER {
+__init__(scen : Scenario, *args, **kwargs)
+develop(exp : Experiment) Experiment
}
CoSTEER --> FactorCoSTEER
```

**图源**
- [factor_coder/__init__.py](file://rdagent\components\coder\factor_coder\__init__.py#L10-L32)

**节源**
- [factor_coder/__init__.py](file://rdagent\components\coder\factor_coder\__init__.py#L10-L32)

### 模型Coder
模型Coder组件`ModelCoSTEER`专门用于模型生成和优化，继承自`CoSTEER`基类。

```mermaid
classDiagram
class ModelCoSTEER {
+__init__(scen : Scenario, *args, **kwargs)
}
CoSTEER --> ModelCoSTEER
```

**图源**
- [model_coder/__init__.py](file://rdagent\components\coder\model_coder\__init__.py#L10-L21)

**节源**
- [model_coder/__init__.py](file://rdagent\components\coder\model_coder\__init__.py#L10-L21)

## Runner组件

### 执行环境管理
Runner组件`CachedRunner`负责管理代码执行环境和结果缓存，继承自`Developer`基类。

```mermaid
classDiagram
class CachedRunner {
+get_cache_key(exp : Experiment) str
+assign_cached_result(exp : Experiment, cached_res : Experiment) Experiment
}
class Developer {
<<abstract>>
+develop(exp : Experiment) Experiment
}
CachedRunner --|> Developer
```

**图源**
- [runner/__init__.py](file://rdagent\components\runner\__init__.py#L4-L20)

**节源**
- [runner/__init__.py](file://rdagent\components\runner\__init__.py#L4-L20)

### 结果捕获机制
`CachedRunner`通过`get_cache_key`方法生成实验的缓存键，该键基于实验任务的信息。`assign_cached_result`方法将缓存结果分配给当前实验。

```mermaid
flowchart TD
Start([开始]) --> GetTasks["获取所有任务"]
GetTasks --> CreateTaskInfo["创建任务信息列表"]
CreateTaskInfo --> JoinTaskInfo["连接任务信息"]
JoinTaskInfo --> HashTaskInfo["计算任务信息哈希"]
HashTaskInfo --> ReturnKey["返回缓存键"]
ReturnKey --> End([结束])
```

**图源**
- [runner/__init__.py](file://rdagent\components\runner\__init__.py#L6-L12)

**节源**
- [runner/__init__.py](file://rdagent\components\runner\__init__.py#L6-L12)

## Proposal组件

### 创意生成策略
Proposal组件提供基于LLM的假设生成和实验转换功能，支持因子、模型和联合场景。

```mermaid
classDiagram
class LLMHypothesisGen {
<<abstract>>
+__init__(scen : Scenario)
+prepare_context(trace : Trace) Tuple[dict, bool]
+convert_response(response : str) Hypothesis
+gen(trace : Trace, plan : ExperimentPlan | None) Hypothesis
}
class FactorHypothesisGen {
+targets : str
}
class ModelHypothesisGen {
+targets : str
}
class FactorAndModelHypothesisGen {
+targets : str
}
LLMHypothesisGen --> FactorHypothesisGen
LLMHypothesisGen --> ModelHypothesisGen
LLMHypothesisGen --> FactorAndModelHypothesisGen
```

**图源**
- [proposal/__init__.py](file://rdagent\components\proposal\__init__.py#L15-L50)

**节源**
- [proposal/__init__.py](file://rdagent\components\proposal\__init__.py#L15-L50)

### 多样性控制
`LLMHypothesis2Experiment`类负责将假设转换为具体实验，支持重试机制以确保生成质量。

```mermaid
classDiagram
class LLMHypothesis2Experiment {
<<abstract>>
+prepare_context(hypothesis : Hypothesis, trace : Trace) Tuple[dict, bool]
+convert_response(response : str, hypothesis : Hypothesis, trace : Trace) Experiment
+convert(hypothesis : Hypothesis, trace : Trace) Experiment
}
class FactorHypothesis2Experiment {
+targets : str
}
class ModelHypothesis2Experiment {
+targets : str
}
class FactorAndModelHypothesis2Experiment {
+targets : str
}
LLMHypothesis2Experiment --> FactorHypothesis2Experiment
LLMHypothesis2Experiment --> ModelHypothesis2Experiment
LLMHypothesis2Experiment --> FactorAndModelHypothesis2Experiment
```

**图源**
- [proposal/__init__.py](file://rdagent\components\proposal\__init__.py#L70-L110)

**节源**
- [proposal/__init__.py](file://rdagent\components\proposal\__init__.py#L70-L110)

## KnowledgeManagement组件

### 向量数据库
`VectorBase`和`PDVectorBase`类提供了向量存储和查询功能，基于Pandas实现。

```mermaid
classDiagram
class VectorBase {
<<abstract>>
+add(document : Document | List[Document])
+search(content : str, topk_k : int | None, similarity_threshold : float) List[Document]
}
class PDVectorBase {
+vector_df : DataFrame
+shape() tuple
+add(document : Document | List[Document])
+search(content : str, topk_k : int | None, similarity_threshold : float, constraint_labels : list[str] | None) Tuple[List[Document], List]
}
VectorBase --> PDVectorBase
```

**图源**
- [knowledge_management/vector_base.py](file://rdagent\components\knowledge_management\vector_base.py#L80-L208)

**节源**
- [knowledge_management/vector_base.py](file://rdagent\components\knowledge_management\vector_base.py#L80-L208)

### 图谱存储
`Graph`和`UndirectedGraph`类提供了知识图谱的存储和查询功能，支持语义搜索和图遍历。

```mermaid
classDiagram
class Graph {
<<abstract>>
+nodes : dict
+size() int
+get_node(node_id : str) Node | None
+add_node(**kwargs : Any) NoReturn
+get_all_nodes() list[Node]
+get_all_nodes_by_label_list(label_list : list[str]) list[Node]
+find_node(content : str, label : str) Node | None
+batch_embedding(nodes : list[Node]) list[Node]
}
class UndirectedGraph {
+vector_base : VectorBase
+add_node(node : UndirectedNode, neighbor : UndirectedNode, same_node_threshold : float) None
+add_nodes(node : UndirectedNode, neighbors : list[UndirectedNode]) None
+get_node(node_id : str) UndirectedNode
+get_node_by_content(content : str) UndirectedNode | None
+get_nodes_within_steps(start_node : UndirectedNode, steps : int, constraint_labels : list[str] | None, block : bool) list[UndirectedNode]
+get_nodes_intersection(nodes : list[UndirectedNode], steps : int, constraint_labels : list[str] | None) list[UndirectedNode]
+semantic_search(node : UndirectedNode | str, similarity_threshold : float, topk_k : int, constraint_labels : list[str] | None) list[UndirectedNode]
+clear() None
+query_by_node(node : UndirectedNode, step : int, constraint_labels : list[str] | None, constraint_node : UndirectedNode | None, constraint_distance : float, block : bool) list[UndirectedNode]
+query_by_content(content : str | list[str], topk_k : int, step : int, constraint_labels : list[str] | None, constraint_node : UndirectedNode | None, similarity_threshold : float, constraint_distance : float, block : bool) list[UndirectedNode]
+intersection(nodes1 : list[UndirectedNode], nodes2 : list[UndirectedNode]) list[UndirectedNode]
+different(nodes1 : list[UndirectedNode], nodes2 : list[UndirectedNode]) list[UndirectedNode]
+cal_distance(node1 : UndirectedNode, node2 : UndirectedNode) float
+filter_label(nodes : list[UndirectedNode], labels : list[str]) list[UndirectedNode]
}
Graph --> UndirectedGraph
```

**图源**
- [knowledge_management/graph.py](file://rdagent\components\knowledge_management\graph.py#L100-L497)

**节源**
- [knowledge_management/graph.py](file://rdagent\components\knowledge_management\graph.py#L100-L497)

## 组件间依赖关系与数据交换

### 依赖关系
各组件之间存在明确的依赖关系，形成一个完整的自动化机器学习流水线。

```mermaid
graph TD
Proposal[Proposal组件] --> |生成假设| Coder[Coder组件族]
Coder --> |生成代码| Runner[Runner组件]
Runner --> |执行结果| Knowledge[KnowledgeManagement组件]
Knowledge --> |知识检索| Coder
Coder --> |演化反馈| Proposal
```

**图源**
- [CoSTEER/__init__.py](file://rdagent\components\coder\CoSTEER\__init__.py)
- [proposal/__init__.py](file://rdagent\components\proposal\__init__.py)
- [runner/__init__.py](file://rdagent\components\runner\__init__.py)
- [knowledge_management/vector_base.py](file://rdagent\components\knowledge_management\vector_base.py)
- [knowledge_management/graph.py](file://rdagent\components\knowledge_management\graph.py)

**节源**
- [CoSTEER/__init__.py](file://rdagent\components\coder\CoSTEER\__init__.py)
- [proposal/__init__.py](file://rdagent\components\proposal\__init__.py)
- [runner/__init__.py](file://rdagent\components\runner\__init__.py)
- [knowledge_management/vector_base.py](file://rdagent\components\knowledge_management\vector_base.py)
- [knowledge_management/graph.py](file://rdagent\components\knowledge_management\graph.py)

### 数据交换格式
组件间通过标准化的数据结构进行信息交换，主要包括：

1. `Experiment`：实验对象，包含任务列表和工作空间
2. `Feedback`：反馈对象，包含执行、返回值和代码反馈
3. `Document`：文档对象，用于知识存储和检索
4. `Node`：图节点对象，用于知识图谱

## 实际调用示例

### 数据科学场景
```mermaid
sequenceDiagram
participant User as "用户"
participant Proposal as "Proposal组件"
participant Coder as "Coder组件"
participant Runner as "Runner组件"
participant Knowledge as "Knowledge组件"
User->>Proposal : 请求生成假设
Proposal->>Proposal : gen(trace)
Proposal-->>User : 返回假设
User->>Coder : 请求开发实验
Coder->>Coder : develop(exp)
Coder->>Knowledge : 检索知识
Knowledge-->>Coder : 返回相关知识
Coder->>Runner : 执行代码
Runner-->>Coder : 返回执行结果
Coder->>Coder : 处理反馈
Coder-->>User : 返回演化后的实验
```

**图源**
- [data_science/pipeline/__init__.py](file://rdagent\components\coder\data_science\pipeline\__init__.py)
- [data_science/model/__init__.py](file://rdagent\components\coder\data_science\model\__init__.py)
- [data_science/feature/__init__.py](file://rdagent\components\coder\data_science\feature\__init__.py)
- [data_science/ensemble/__init__.py](file://rdagent\components\coder\data_science\ensemble\__init__.py)

**节源**
- [data_science/pipeline/__init__.py](file://rdagent\components\coder\data_science\pipeline\__init__.py)
- [data_science/model/__init__.py](file://rdagent\components\coder\data_science\model\__init__.py)
- [data_science/feature/__init__.py](file://rdagent\components\coder\data_science\feature\__init__.py)
- [data_science/ensemble/__init__.py](file://rdagent\components\coder\data_science\ensemble\__init__.py)

### 因子分析场景
```mermaid
sequenceDiagram
participant User as "用户"
participant FactorProposal as "因子Proposal"
participant FactorCoder as "因子Coder"
participant Runner as "Runner组件"
User->>FactorProposal : 请求因子假设
FactorProposal->>FactorProposal : gen(trace)
FactorProposal-->>User : 返回因子假设
User->>FactorCoder : 开发因子实验
FactorCoder->>FactorCoder : develop(exp)
FactorCoder->>Runner : 执行因子代码
Runner-->>FactorCoder : 返回执行结果
FactorCoder->>FactorCoder : 处理反馈
FactorCoder-->>User : 返回演化后的因子实验
```

**图源**
- [factor_coder/__init__.py](file://rdagent\components\coder\factor_coder\__init__.py)

**节源**
- [factor_coder/__init__.py](file://rdagent\components\coder\factor_coder\__init__.py)

## 结论
本文档全面介绍了RD-Agent系统中components包的可复用组件API。CoSTEER框架为代码生成提供了强大的迭代演化能力，支持多种数据科学场景的定制化需求。Runner组件确保了执行环境的稳定性和结果的可复现性。Proposal组件通过LLM驱动的假设生成，实现了创意的自动化探索。KnowledgeManagement组件则通过向量数据库和知识图谱，实现了知识的有效存储和智能检索。这些组件协同工作，形成了一个完整的自动化机器学习研发流水线。