[根目录](../../../CLAUDE.md) > [rdagent](../../) > [components](../) > **coder**

# CoSTEER 核心编码框架

## 相对路径面包屑
[根目录](../../../CLAUDE.md) > [rdagent](../../) > [components](../) > **coder**

## 模块职责

CoSTEER（Collaborative Self-adaptive Testing and Evaluation for Evolutionary Refinement）是RD-Agent的核心进化式编码框架，通过持续的评估反馈循环实现代码的自主改进和优化。

## 核心架构

### 🧠 evolving_strategy.py - 进化策略引擎
**功能**：定义代码进化的核心策略和执行流程

#### MultiProcessEvolvingStrategy
- **improve_mode**：改进模式，仅实现之前失败的任务
- **multiprocessing_wrapper**：多进程并行执行任务实现
- **任务调度逻辑**：
  ```python
  # 识别需要进化的任务
  to_be_finished_task_index = []
  for index, target_task in enumerate(evo.sub_tasks):
      if target_task_desc not in queried_knowledge.success_task_to_knowledge_dict:
          if not skip_for_improve_mode:
              to_be_finished_task_index.append(index)
  ```

#### 关键特性
- **并行任务执行**：支持多进程并行处理多个子任务
- **反馈驱动改进**：基于历史反馈决定实现策略
- **知识积累**：成功任务的知识被保存和复用
- **智能跳过**：improve_mode下智能跳过已成功或无需改进的任务

### 🎯 evaluators.py - 评估系统
**功能**：提供多维度的代码评估和反馈机制

#### CoSTEERSingleFeedback
核心反馈数据结构，包含四阶段评估：
1. **execution**：代码执行结果
2. **return_checking**：返回值验证（包括值、形状、生成标志等约束）
3. **code**：生成的代码内容
4. **final_decision**：最终决策（布尔值）

#### 评估流程
```python
@dataclass
class CoSTEERSingleFeedback(Feedback):
    execution: str
    return_checking: str | None
    code: str
    final_decision: bool | None = None
```

### 📚 knowledge_management.py - 知识管理系统
**功能**：实现经验的积累、检索和RAG增强

#### CoSTEERKnowledge
知识单元封装：
- **target_task**：目标任务描述
- **implementation**：实现的代码工作空间
- **feedback**：评估反馈信息

#### CoSTEERRAGStrategy
RAG（检索增强生成）策略：
- **知识库持久化**：支持pickle序列化保存
- **版本兼容性**：支持V1和V2两个版本的知识库
- **加载策略**：智能加载现有知识库或初始化新库

#### 知识管理特性
- **经验复用**：成功解决方案可以被检索和复用
- **失败避免**：记录失败经验避免重复错误
- **相似性检索**：基于embedding的相似知识检索
- **知识图谱**：使用图结构组织知识间的关系

### ⚙️ config.py - 配置系统
**功能**：统一的CoSTEER框架配置管理

### 📋 task.py - 任务定义
**功能**：定义可进化任务的结构和接口

### 🔄 evolvable_subjects.py - 可进化主体
**功能**：定义可进化主体的抽象和行为

## 工作流程

### 1. 初始化阶段
```python
strategy = MultiProcessEvolvingStrategy(scen, settings, improve_mode=False)
knowledge_base = CoSTEERRAGStrategy().load_or_init_knowledge_base()
```

### 2. 任务识别阶段
- 扫描需要实现的子任务
- 检查知识库中的成功记录
- 识别失败任务集合
- 决定任务优先级

### 3. 并行执行阶段
```python
result = multiprocessing_wrapper(
    [(self.implement_one_task, (task, knowledge, workspace, feedback))
     for task in to_be_finished_task_index],
    n=RD_AGENT_SETTINGS.multi_proc_n
)
```

### 4. 评估反馈阶段
- 执行生成的代码
- 收集执行结果和返回值
- 进行代码质量检查
- 生成最终决策

### 5. 知识更新阶段
- 将成功的实现存入知识库
- 更新失败记录避免重复
- 维护知识图谱关系

## 关键设计模式

### 进化循环模式
```
任务识别 → 并行实现 → 评估反馈 → 知识更新 → 下一轮进化
```

### 多进程协作模式
- 主进程负责任务调度和结果汇总
- 工作进程负责具体的任务实现
- 共享知识库避免重复工作

### RAG增强模式
- 基于历史经验的检索增强
- embedding相似性匹配
- 知识图谱关系推理

## 配置参数

### 核心配置
```python
from rdagent.components.coder.CoSTEER.config import CoSTEERSettings

settings = CoSTEERSettings()
max_loop = settings.max_loop          # 最大进化循环次数
multi_proc_n = settings.multi_proc_n  # 并行进程数
improve_mode = settings.improve_mode  # 改进模式开关
```

### LLM集成配置
```python
from rdagent.oai.llm_conf import LLMSettings

llm_settings = LLMSettings()
chat_model = llm_settings.chat_model          # 聊天模型
embedding_model = llm_settings.embedding_model # 嵌入模型
```

## 扩展接口

### 自定义进化策略
```python
class CustomEvolvingStrategy(MultiProcessEvolvingStrategy):
    def implement_one_task(self, target_task, queried_knowledge, workspace, prev_task_feedback):
        # 实现自定义的任务逻辑
        return {"filename": "content"}

    def assign_code_list_to_evo(self, code_list, evo):
        # 实现自定义的代码分配逻辑
        return evo
```

### 自定义评估器
```python
class CustomEvaluator(CoSTEEREvaluator):
    def evaluate(self, workspace, task):
        # 实现自定义评估逻辑
        return CoSTEERSingleFeedback(...)
```

## 测试与质量

### 单元测试
- `test/utils/coder/test_CoSTEER.py`：核心框架测试
- 各组件的独立测试用例

### 集成测试
- 与数据科学编码器的集成测试
- 端到端的进化流程测试

### 性能测试
- 多进程并发性能测试
- 知识库检索效率测试
- 内存使用优化验证

## 常见问题 (FAQ)

### Q: CoSTEER如何确保代码质量？
A: 通过四阶段评估（执行、返回值检查、代码审查、最终决策）确保生成代码的质量。

### Q: 知识库如何避免过期？
A: 知识库支持版本管理，可以迁移和升级，同时支持RAG检索确保知识的相关性。

### Q: 如何处理进化过程中的死锁？
A: 通过improve_mode和失败记录管理，避免重复实现已失败的任务。

### Q: 多进程执行如何保证一致性？
A: 通过共享知识库和统一的任务调度机制确保多进程执行的一致性。

## 相关文件清单

### 核心文件
- `rdagent/components/coder/CoSTEER/evolving_strategy.py`
- `rdagent/components/coder/CoSTEER/evaluators.py`
- `rdagent/components/coder/CoSTEER/knowledge_management.py`

### 配置文件
- `rdagent/components/coder/CoSTEER/config.py`
- `rdagent/components/coder/CoSTEER/prompts.yaml`

### 测试文件
- `test/utils/coder/test_CoSTEER.py`

### 知识库文件
- 知识库pickle文件（运行时生成）
- embedding缓存文件

---

## 变更记录 (Changelog)

### 2025-11-17 14:35:04 - 增量更新
- **深度扫描CoSTEER核心**：详细分析evolving_strategy.py的多进程进化机制
- **评估系统解析**：深入理解四阶段评估反馈循环
- **知识管理机制**：分析RAG增强策略和知识图谱管理
- **工作流程梳理**：完整呈现从任务识别到知识更新的进化循环
- **扩展接口设计**：提供自定义策略和评估器的扩展指南
- **多进程协作优化**：解析并行执行和一致性保证机制

### 2025-11-17 14:31:27
- **模块文档初始化**：完成CoSTEER框架基础架构文档
- **核心组件识别**：evolving_strategy、evaluators、knowledge_management等核心模块
- **初步工作流说明**：基本的进化循环和工作流程
- **下一步建议**：需要深入具体实现细节和配置参数

---

*最后更新：2025-11-17 14:35:04*