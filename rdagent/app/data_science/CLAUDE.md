[根目录](../../../CLAUDE.md) > [rdagent](../../) > [app](../) > **data_science**

# 数据科学应用模块

## 相对路径面包屑
[根目录](../../../CLAUDE.md) > [rdagent](../../) > [app](../) > **data_science**

## 模块职责

数据科学应用模块是RD-Agent的核心应用场景之一，为通用数据科学任务提供端到端的自动化支持。该模块集成了完整的数据科学工作流，从数据加载到模型部署，支持灵活的配置和多种执行模式。

## 核心架构

### 📊 conf.py - 配置系统
**功能**：提供数据科学场景的完整配置管理，基于Pydantic的数据验证和环境变量集成。

#### 主要配置类别

**基础配置**：
- `scen`: 场景类选择（KaggleScen/DataScienceScen）
- `planner`: 实验规划器配置
- `hypothesis_gen`: 假设生成器配置
- `interactor`: 交互器配置

**工作流配置**：
- `consecutive_errors`: 连续错误阈值（默认5）
- `coding_fail_reanalyze_threshold`: 编码失败重分析阈值（默认3）

**超时配置**：
- `debug_recommend_timeout`: 调试推荐超时（600秒）
- `debug_timeout`: 调试超时（600秒）
- `full_recommend_timeout`: 完整数据推荐超时（3600秒）
- `full_timeout`: 完整数据超时（3600秒）

**高级功能配置**：
- `enable_model_dump`: 模型转储启用
- `enable_doc_dev`: 文档开发启用
- `enable_mcp_documentation_search`: MCP文档搜索启用
- `enable_notebook_conversion`: Notebook转换启用

#### 多轨迹配置
- `max_trace_num`: 最大轨迹数量（默认1）
- `scheduler_temperature`: 调度器温度参数
- `scheduler_c_puct`: MCTS调度器探索常数
- `enable_score_reward`: 启用基于分数的奖励

#### 多样性配置
- `enable_inject_diverse`: 启用多样性注入
- `enable_cross_trace_diversity`: 启用跨轨迹多样性
- `diversity_injection_strategy`: 多样性注入策略
- `enable_multi_version_exp_gen`: 启用多版本实验生成

#### 知识库配置
- `enable_knowledge_base`: 启用知识库（默认False）
- `knowledge_base_version`: 知识库版本（"v1"）
- `knowledge_base_path`: 知识库路径
- `idea_pool_json_path`: 创意池JSON路径

### 🔄 loop.py - 主循环控制
**功能**：数据科学实验的主要执行逻辑和工作流控制。

#### 主要函数
```python
def main(
    path: Optional[str] = None,
    checkout: Annotated[bool, typer.Option("--checkout/--no-checkout", "-c/-C")] = True,
    checkout_path: Optional[str] = None,
    step_n: Optional[int] = None,
    loop_n: Optional[int] = None,
    timeout: Optional[str] = None,
    competition="bms-molecular-translation",
    replace_timer=True,
    exp_gen_cls: Optional[str] = None,
):
```

#### 功能特性
- **参数化执行**：支持多种CLI参数配置
- **恢复机制**：支持从中断点恢复执行
- **竞赛支持**：内置多种竞赛模板
- **调试模式**：支持详细的调试输出

## 配置使用指南

### 环境变量配置
数据科学场景支持通过环境变量进行配置，所有配置项都以`DS_`为前缀：

```bash
# 基础配置
DS_SCEN="rdagent.scenarios.data_science.scen.KaggleScen"
DS_MAX_LOOP=10
DS_TIMEOUT=3600

# 知识库配置
DS_ENABLE_KNOWLEDGE_BASE=true
DS_KNOWLEDGE_BASE_PATH="./knowledge"
DS_KNOWLEDGE_BASE_VERSION="v1"

# 多轨迹配置
DS_MAX_TRACE_NUM=3
DS_SCHEDULER_TEMPERATURE=1.5
DS_ENABLE_CROSS_TRACE_DIVERSITY=true

# 多样性配置
DS_ENABLE_INJECT_DIVERSE=true
DS_DIVERSITY_INJECTION_STRATEGY="rdagent.scenarios.data_science.proposal.exp_gen.diversity_strategy.InjectUntilSOTAGainedStrategy"
```

### 配置文件使用
```python
from rdagent.app.data_science.conf import DS_RD_SETTING

# 访问配置
max_loop = DS_RD_SETTING.max_loop
timeout = DS_RD_SETTING.full_timeout
knowledge_enabled = DS_RD_SETTING.enable_knowledge_base
```

## 对外接口

### CLI接口
```bash
# 基础数据科学任务
rdagent data-science --competition playground-series-s4e9

# 带配置的数据科学任务
rdagent data-science \
  --competition spaceship-titanic \
  --max-loop 20 \
  --timeout 7200 \
  --enable-knowledge-base

# 恢复执行
rdagent data-science --path ./workspace/experiment_123

# 调试模式
rdagent data-science --debug --competition playground-series-s4e9
```

### Python API接口
```python
from rdagent.app.data_science.loop import main
from rdagent.app.data_science.conf import DS_RD_SETTING

# 直接调用
main(
    competition="playground-series-s4e9",
    loop_n=5,
    timeout="2h"
)

# 配置修改
DS_RD_SETTING.enable_knowledge_base = True
DS_RD_SETTING.knowledge_base_path = "./my_knowledge"
```

## 工作流程

### 1. 初始化阶段
- 环境变量加载和配置解析
- 工作空间创建和初始化
- 数据加载和预处理

### 2. 实验生成阶段
- 假设生成和提案创建
- 多轨迹并行实验设计
- 多样性注入和创意探索

### 3. 执行阶段
- 代码生成和验证
- 模型训练和评估
- 结果收集和分析

### 4. 反馈阶段
- 性能评估和反馈生成
- 知识提取和积累
- 下一轮实验规划

### 5. 迭代优化
- 基于反馈的策略调整
- SOTA模型追踪和集成
- 最终结果输出

## 高级功能

### 知识库增强
- **功能**：自动积累和组织实验经验
- **配置**：`DS_ENABLE_KNOWLEDGE_BASE=true`
- **存储**：支持本地和远程知识库
- **版本管理**：支持知识库版本控制

### 多轨迹并行
- **功能**：同时运行多个实验轨迹
- **调度器**：支持轮询、概率、MCTS等调度策略
- **多样性**：跨轨迹多样性注入
- **合并策略**：智能轨迹合并和集成

### MCP文档搜索
- **功能**：集成MCP文档搜索进行错误解决
- **配置**：需要`MCP_ENABLED=true`和`MCP_CONTEXT7_ENABLED=true`
- **用途**：自动搜索相关文档解决编码错误

### Notebook集成
- **功能**：支持Jupyter Notebook转换
- **配置**：`DS_ENABLE_NOTEBOOK_CONVERSION=true`
- **输出**：自动生成可复现的Notebook

## 性能优化

### 超时管理
- 分层超时控制（调试/推荐/完整数据）
- 智能超时调整
- 资源使用监控

### 并行执行
- 多进程任务执行
- GPU资源管理
- 内存使用优化

### 缓存策略
- 模型结果缓存
- 数据预处理缓存
- 知识库查询缓存

## 故障排除

### 常见问题
1. **配置错误**：检查环境变量和配置文件格式
2. **超时问题**：调整超时配置或优化数据处理
3. **内存不足**：启用缓存优化或减少并行度
4. **知识库错误**：检查知识库路径和权限

### 调试技巧
```bash
# 启用详细日志
rdagent data-science --debug --log-level DEBUG

# 检查配置
python -c "from rdagent.app.data_science.conf import DS_RD_SETTING; print(DS_RD_SETTING.model_dump())"

# 测试环境
rdagent health-check
```

## 扩展开发

### 自定义配置
```python
class CustomDataScienceSetting(DataScienceBasePropSetting):
    custom_param: str = "default_value"
    custom_feature: bool = False
```

### 自定义组件
```python
# 自定义假设生成器
class CustomHypothesisGen:
    def generate(self, context):
        # 自定义生成逻辑
        pass
```

### 插件集成
- 支持自定义数据加载器
- 支持自定义评估器
- 支持自定义输出格式

---

## 变更记录 (Changelog)

### 2025-12-06 - 配置系统增强
- **丰富的配置选项**：新增大量可配置参数，支持细粒度控制
- **多轨迹支持**：完善多轨迹并行执行配置
- **多样性策略**：新增多种多样性注入策略配置
- **知识库集成**：完整的知识库配置和管理
- **环境变量支持**：全面的环境变量配置系统
- **性能优化配置**：超时、缓存、并行等性能相关配置
- **调试功能增强**：新增调试模式和诊断工具

### 2025-11-17 - 模块初始化
- **基础架构建立**：数据科学应用模块框架搭建
- **配置系统设计**：基于Pydantic的配置管理系统
- **CLI接口实现**：完整的命令行接口和参数支持
- **工作流控制**：主循环控制和执行逻辑实现

---

*最后更新：2025-12-06*