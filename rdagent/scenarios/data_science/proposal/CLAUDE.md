[根目录](../../../CLAUDE.md) > [rdagent](../../) > [scenarios](../) > [data_science](../) > **proposal**

# 数据科学提案生成系统

## 相对路径面包屑
[根目录](../../../CLAUDE.md) > [rdagent](../../) > [scenarios](../) > [data_science](../) > **proposal**

## 模块职责

数据科学提案生成系统是RD-Agent的核心智能决策引擎，负责基于历史经验、当前反馈和新颖性策略自动生成高质量的实验提案，指导机器学习实验的进化方向。

## 核心架构

### 🧭 exp_gen/ - 实验生成引擎
**功能**：实现智能化的实验提案生成和管理

#### base.py - 基础抽象类
**DSHypothesis（数据科学假设）**：
核心假设数据结构，包含：
- **component**：目标组件类型（DataLoadSpec、FeatureEng、Model、Ensemble、Workflow）
- **hypothesis**：具体的改进假设描述
- **problem_name/desc**：目标问题描述
- **problem_label**：问题分类（SCENARIO_PROBLEM / FEEDBACK_PROBLEM）
- **concise_***：各类简洁摘要信息

**DSTrace（数据科学追踪）**：
实验追踪管理器，负责：
- **hist**：历史实验记录
- **sota_exp_to_submit**：全局最佳实验
- **uncommitted_experiments**：未提交的实验管理
- **should_inject_diversity()**：多样性注入策略判断

#### proposal.py - 提案生成核心
**组件元数据定义**：
```python
_COMPONENT_META = {
    "DataLoadSpec": {
        "target_name": "Data loader and specification generation",
        "spec_file": "spec/data_loader.md",
        "task_class": DataLoaderTask,
    },
    "FeatureEng": {
        "target_name": "Feature engineering",
        "task_class": FeatureTask,
    },
    "Model": {
        "target_name": "Model",
        "task_class": ModelTask,
    },
    # ... 其他组件
}
```

**提案生成流程**：
1. **组件选择**：基于当前进度和反馈选择下一个要优化的组件
2. **假设生成**：结合RAG知识生成改进假设
3. **多样性检查**：根据多样性策略决定是否注入新思路
4. **提案验证**：确保提案的可行性和合理性

#### idea_pool.py - 创意池管理
**DSIdea（数据科学创意）**：
创意单元数据结构：
```python
{
    "idea": "简洁的创意概念标签",
    "method": "通用可实现的方法描述",
    "context": "具体的实现示例",
    "hypothesis": {
        "scenario_problem": "解决的场景问题",
        "feedback_problem": "数据特征分析"
    }
}
```

**DSKnowledgeBase（数据科学知识库）**：
- **UndirectedGraph**：基于图结构的创意关联管理
- **used_idea_id_set**：已使用创意追踪
- **知识持久化**：支持创意池的保存和加载
- **相似性检索**：基于embedding的创意相似性匹配

#### diversity_strategy.py - 多样性策略
**功能**：确保实验探索的多样性，避免局部最优

**多样性注入条件**：
- 历史实验收敛性分析
- 当前选择的多样性评估
- 跨轨迹多样性考虑
- 时间窗口内的多样性平衡

#### planner/ - 实验规划器
**DSExperimentPlan**：
实验规划和调度管理：
- **任务分解**：将复杂实验分解为可执行的子任务
- **资源分配**：合理分配计算资源和时间
- **依赖管理**：处理实验间的依赖关系
- **进度跟踪**：监控实验执行进度

#### select/ - 选择策略
**submit.py - 提交选择器**：
**BestValidSelector**：
- **验证集性能**：基于验证集结果选择最佳模型
- **稳定性评估**：考虑模型性能的稳定性
- **过拟合检测**：避免选择过拟合的模型
- **集成策略**：支持多模型集成选择

**expand.py - 扩展选择器**：
- **候选生成**：生成扩展实验的候选集合
- **多样性平衡**：在性能和多样性间寻找平衡
- **新颖性评估**：评估新实验的新颖程度

#### trace_scheduler.py - 追踪调度器
**功能**：管理实验追踪的调度和优化

**调度策略**：
- **优先级调度**：基于实验价值和紧急性
- **资源调度**：优化计算资源的使用效率
- **时间调度**：合理安排实验执行顺序
- **反馈调度**：基于实时反馈调整调度策略

#### router/ - 路由器
**功能**：智能路由提案到合适的执行器

**路由策略**：
- **组件匹配**：根据提案类型路由到对应组件
- **负载均衡**：在多个执行器间平衡负载
- **错误处理**：路由失败的重试和降级
- **性能监控**：监控路由性能和成功率

#### utils.py - 工具函数
**功能**：提供提案生成的通用工具

**工具集合**：
- **包信息获取**：get_packages() - 获取可用的ML包
- **数据验证**：提案数据的格式验证
- **相似性计算**：提案相似度计算
- **格式转换**：不同格式间的转换

## 工作流程

### 1. 初始化阶段
```python
# 初始化追踪器
trace = DSTrace(scenario, knowledge_base)

# 初始化创意池
idea_pool = DSKnowledgeBase(idea_pool_json_path="ideas.json")

# 初始化提案生成器
proposal_gen = DSProposalV2ExpGen(scenario)
```

### 2. 提案生成阶段
```python
# 检查是否需要多样性注入
if trace.should_inject_diversity():
    # 从创意池获取多样化创意
    diverse_ideas = idea_pool.get_diverse_ideas(count=5)

# 生成实验提案
hypothesis = proposal_gen.generate_hypothesis(
    trace=trace,
    target_component="Model",
    feedback=current_feedback
)
```

### 3. 实验执行阶段
```python
# 创建实验
experiment = DSExperiment(
    hypothesis=hypothesis,
    workspace=workspace,
    component=component
)

# 执行实验
result = experiment.execute()
feedback = evaluator.evaluate(result)
```

### 4. 知识更新阶段
```python
# 更新追踪记录
trace.update(experiment, feedback)

# 更新创意池
if feedback.success:
    idea_pool.add_successful_idea(experiment.hypothesis)

# 更新知识库
knowledge_base.update_with_feedback(experiment, feedback)
```

### 5. 选择与提交阶段
```python
# 选择最佳实验进行提交
best_exp = BestValidSelector.select(trace.submitted_experiments)

# 提交到外部系统
submission = external_system.submit(best_exp)
```

## 关键算法

### 多样性注入算法
```python
def should_inject_diversity(self, current_selection):
    # 计算当前选择的收敛性
    convergence = calculate_convergence(current_selection)

    # 检查时间窗口内的多样性
    diversity_score = calculate_diversity_score(time_window)

    # 综合决策
    return convergence > threshold and diversity_score < min_diversity
```

### 提案生成算法
```python
def generate_hypothesis(self, trace, target_component, feedback):
    # RAG检索相关知识
    relevant_knowledge = knowledge_base.retrieve_similar(
        query=feedback.description,
        component=target_component
    )

    # 生成基础假设
    base_hypothesis = llm_generate_hypothesis(
        context=relevant_knowledge,
        feedback=feedback,
        component_spec=COMPONENT_META[target_component]
    )

    # 多样性增强
    if should_inject_diversity():
        enhanced_hypothesis = diversity_enhance(
            base_hypothesis,
            idea_pool.get_random_ideas()
        )

    return enhanced_hypothesis
```

### 最佳选择算法
```python
def select_best_experiment(self, experiments):
    valid_exps = [exp for exp in experiments if exp.is_valid()]

    # 多维度评分
    scores = []
    for exp in valid_exps:
        score = (
            exp.validation_score * 0.6 +           # 验证集性能
            exp.stability_score * 0.2 +            # 稳定性
            exp.novelty_score * 0.1 +              # 新颖性
            exp.diversity_bonus * 0.1              # 多样性奖励
        )
        scores.append((exp, score))

    # 返回最高分实验
    return max(scores, key=lambda x: x[1])[0]
```

## 配置参数

### 核心配置
```python
from rdagent.app.data_science.conf import DS_RD_SETTING

# 多样性配置
enable_cross_trace_diversity = DS_RD_SETTING.enable_cross_trace_diversity
diversity_injection_strategy = DS_RD_SETTING.diversity_injection_strategy

# 提案生成配置
max_hypotheses_per_round = DS_RD_SETTING.max_hypotheses_per_round
knowledge_retrieval_top_k = DS_RD_SETTING.knowledge_retrieval_top_k

# 选择策略配置
selection_strategy = DS_RD_SETTING.selection_strategy
stability_threshold = DS_RD_SETTING.stability_threshold
```

### 组件配置
```python
# 各组件的权重配置
component_weights = {
    "DataLoadSpec": 1.0,
    "FeatureEng": 2.0,    # 特征工程通常更重要
    "Model": 3.0,         # 模型选择最关键
    "Ensemble": 1.5,
    "Workflow": 1.0
}
```

## 扩展接口

### 自定义提案生成器
```python
class CustomProposalGen(DSProposalV2ExpGen):
    def generate_hypothesis(self, trace, target_component, feedback):
        # 实现自定义提案生成逻辑
        custom_knowledge = self.retrieve_custom_knowledge(target_component)
        return self.custom_generation_logic(custom_knowledge, feedback)
```

### 自定义多样性策略
```python
class CustomDiversityStrategy:
    def should_inject(self, trace, current_selection):
        # 实现自定义多样性判断逻辑
        return self.custom_diversity_metric(trace, current_selection)
```

### 自定义选择器
```python
class CustomSelector:
    def select(self, experiments):
        # 实现自定义实验选择逻辑
        return self.custom_selection_algorithm(experiments)
```

## 测试与质量

### 单元测试
- **提案生成测试**：验证提案生成的质量和多样性
- **创意池测试**：测试创意管理和检索功能
- **选择器测试**：验证选择策略的有效性

### 集成测试
- **端到端流程测试**：完整提案到实验的流程
- **多组件协作测试**：不同组件间的协作效果
- **知识库集成测试**：知识积累和检索的效果

### 性能测试
- **大规模提案生成性能**：测试大量提案生成的效率
- **知识库检索性能**：测试大规模知识检索的速度
- **内存使用优化**：优化提案系统的内存占用

## 常见问题 (FAQ)

### Q: 如何平衡探索和利用？
A: 通过多样性注入策略和最佳选择算法的平衡，系统在探索新思路和利用已有知识间找到平衡点。

### Q: 提案质量如何保证？
A: 通过RAG知识检索、多阶段验证和历史反馈学习确保提案质量。

### Q: 如何处理冷启动问题？
A: 系统提供预设的创意池和模板，在缺乏历史经验时仍能生成有效提案。

### Q: 多样性如何量化？
A: 基于embedding距离、组件分布和时序多样性等多个维度综合评估。

## 相关文件清单

### 核心文件
- `rdagent/scenarios/data_science/proposal/exp_gen/base.py`
- `rdagent/scenarios/data_science/proposal/exp_gen/proposal.py`
- `rdagent/scenarios/data_science/proposal/exp_gen/idea_pool.py`

### 策略文件
- `rdagent/scenarios/data_science/proposal/exp_gen/diversity_strategy.py`
- `rdagent/scenarios/data_science/proposal/exp_gen/select/`
- `rdagent/scenarios/data_science/proposal/exp_gen/planner/`

### 配置文件
- `rdagent/app/data_science/conf.py`
- `rdagent/scenarios/data_science/prompts.yaml`

### 测试文件
- `test/scenarios/data_science/test_proposal.py`（如果存在）

---

## 变更记录 (Changelog)

### 2025-11-17 14:35:04 - 增量更新
- **提案生成深度分析**：详细解析DSHypothesis和提案生成机制
- **创意池管理系统**：深入理解DSIdea和DSKnowledgeBase的知识管理
- **多样性策略解析**：分析多样性注入算法和平衡策略
- **工作流程完善**：完整呈现从提案到实验到选择的循环
- **关键算法梳理**：详细说明多样性注入、提案生成、最佳选择等核心算法
- **扩展接口设计**：提供自定义提案生成器和策略的扩展指南

### 2025-11-17 14:31:27
- **模块文档初始化**：完成提案生成系统基础架构文档
- **核心组件识别**：exp_gen、idea_pool、diversity_strategy等核心模块
- **基础工作流说明**：提案生成的基本流程和机制
- **下一步建议**：需要深入提案生成算法和多样性策略的具体实现

---

*最后更新：2025-11-17 14:35:04*