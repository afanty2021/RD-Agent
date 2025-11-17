[根目录](../../../CLAUDE.md) > [rdagent](../) > **scenarios**

# Scenarios 场景实现层

## 相对路径面包屑
[根目录](../../../CLAUDE.md) > [rdagent](../) > **scenarios**

## 模块职责

Scenarios层是RD-Agent的具体应用场景实现层，负责将底层的组件和框架应用到具体的机器学习任务场景中。每个场景都封装了特定领域的工作流、评估标准和最佳实践。

## 场景结构

### 🎯 data_science/ - 通用数据科学场景
**功能**：为通用数据科学任务提供端到端的自动化支持
- **loop.py**：主工作循环控制
- **experiment/**：实验管理和执行
- **proposal/**：实验提案生成和调度
- **dev/**：开发工具和反馈机制
- **example/**：示例任务和数据集

**适用任务**：
- 通用机器学习竞赛
- 数据分析和建模
- 特征工程和模型选择
- 集成学习和流水线优化

### 🏆 kaggle/ - Kaggle竞赛场景
**功能**：专门针对Kaggle竞赛优化的场景实现
- **experiment/**：Kaggle实验框架
- **developer/**：Kaggle专用开发者工具
- **docker/**：Kaggle环境容器化
- **templates/**：竞赛模板库

**特性**：
- 多种竞赛类型模板（表格、图像、时序等）
- 自动提交和排名追踪
- 专用的特征工程策略
- 针对Kaggle评估指标的优化

### 💰 qlib/ - 量化交易场景
**功能**：集成微软Qlib框架的量化交易场景
- **factor_experiment/**：因子实验和管理
- **model_experiment/**：量化模型实验
- **experiment/**：回测和评估框架

**特性**：
- 量化因子自动挖掘
- 多因子模型构建
- 回测和风险分析
- 交易成本建模

### 🤖 general_model/ - 通用模型场景
**功能**：从文档和描述中提取并实现模型
- **scenario.py**：场景定义和配置
- **prompts.yaml**：模型提取提示词

**特性**：
- 论文和文档解析
- 模型架构自动实现
- 代码生成和验证
- 多框架支持（PyTorch、TensorFlow等）

## 入口与启动

### 场景启动方式
```python
# 数据科学场景
from rdagent.scenarios.data_science.loop import DataScienceRDLoop

loop = DataScienceRDLoop()
loop.run()

# Kaggle场景
from rdagent.scenarios.kaggle.experiment import KaggleExperiment

exp = KaggleExperiment(competition="spaceship-titanic")
exp.run()

# Qlib量化场景
from rdagent.scenarios.qlib.factor_experiment import QlibFactorExperiment

exp = QlibFactorExperiment()
exp.run()
```

### CLI集成
场景通过顶层CLI接口暴露：
```bash
# 启动数据科学场景
rdagent data-science --competition playground-series-s4e9

# 启动Kaggle场景
rdagent kaggle --competition spaceship-titanic

# 启动量化交易场景
rdagent quant factor
rdagent quant model
```

## 对外接口

### 数据科学场景接口
- **DataScienceRDLoop**：主工作循环
- **DSExperiment**：实验管理
- **DSProposalV2ExpGen**：提案生成器
- **DSTrace**：实验追踪

### Kaggle场景接口
- **KaggleExperiment**：Kaggle实验框架
- **KaggleDeveloper**：开发工具集
- **KaggleTemplate**：竞赛模板

### Qlib场景接口
- **QlibFactorExperiment**：因子实验
- **QlibModelExperiment**：模型实验
- **QlibRunner**：Qlib执行器

### 通用模型场景接口
- **GeneralModelScenario**：场景定义
- **ModelExtractor**：模型提取器

## 关键依赖与配置

### 外部依赖
- **Qlib**：量化投资框架（qlib场景）
- **Kaggle API**：竞赛数据下载（kaggle场景）
- **ML框架**：scikit-learn、PyTorch、XGBoost等
- **数据科学工具**：pandas、numpy、matplotlib等

### 内部依赖
- **rdagent.components.coder**：编码系统
- **rdagent.components.agent**：智能体框架
- **rdagent.core**：核心抽象类
- **rdagent.oai**：LLM集成

### 场景配置
每个场景都有独立的配置系统：
```python
# 数据科学场景配置
from rdagent.app.data_science.conf import DS_RD_SETTING

# Kaggle场景配置
from rdagent.app.kaggle.conf import KAGGLE_SETTING

# Qlib场景配置
from rdagent.app.qlib_rd_loop.conf import QLIB_SETTING
```

## 实验工作流

### 数据科学工作流
1. **数据加载**：自动识别和加载数据
2. **特征工程**：生成和选择特征
3. **模型训练**：多模型训练和调优
4. **集成学习**：模型集成和优化
5. **结果评估**：多维度性能评估
6. **实验迭代**：基于反馈的改进循环

### Kaggle竞赛工作流
1. **竞赛分析**：理解任务和评估指标
2. **模板选择**：选择合适的竞赛模板
3. **数据预处理**：针对性的数据清洗
4. **模型开发**：多模型并行开发
5. **提交优化**：基于排行榜反馈调优
6. **集成策略**：最终模型集成

### 量化交易工作流
1. **市场数据获取**：历史和实时数据
2. **因子挖掘**：量化因子生成和测试
3. **因子筛选**：基于统计和回测筛选
4. **模型构建**：多因子模型开发
5. **回测验证**：历史回测和风险分析
6. **实盘模拟**：模拟交易和性能追踪

## 测试与质量

### 测试策略
- **单元测试**：各场景组件的独立测试
- **集成测试**：场景间的协作测试
- **模板测试**：竞赛模板的有效性测试
- **回测测试**：量化场景的回测验证

### 质量保证
- **场景文档**：详细的场景使用说明
- **示例代码**：可运行的示例任务
- **最佳实践**：场景特定的最佳实践指南
- **性能基准**：场景性能基准测试

### 测试运行
```bash
# 场景测试
pytest rdagent/scenarios/data_science/test_eval.py

# Kaggle模板测试
pytest rdagent/scenarios/kaggle/experiment/test_*.py

# Qlib集成测试
test/utils/test_env.py  # Docker环境测试
```

## 扩展指南

### 添加新场景
1. 创建场景目录：`rdagent/scenarios/new_scenario/`
2. 实现基础场景类：继承`Scenario`基类
3. 配置入口：在CLI中添加对应命令
4. 编写测试：确保场景正确工作

### 扩展现有场景
1. 添加新的模板或策略
2. 实现新的评估器或工具
3. 更新配置系统支持新参数
4. 添加相应的测试用例

## 常见问题 (FAQ)

### Q: 如何选择合适的场景？
A: 根据任务类型选择：数据科学任务用data_science，Kaggle竞赛用kaggle，量化投资用qlib。

### Q: 场景间的区别是什么？
A: 主要区别在于工作流、评估标准和专用工具。每个场景都针对特定领域进行了优化。

### Q: 可以自定义场景吗？
A: 可以，参考现有场景实现，创建继承自`Scenario`基类的新场景。

### Q: 如何在多个场景间共享代码？
A: 将共享逻辑放在components层，场景只包含特定的业务逻辑。

## 相关文件清单

### 核心场景文件
- `rdagent/scenarios/data_science/loop.py`
- `rdagent/scenarios/kaggle/experiment/scenario.py`
- `rdagent/scenarios/general_model/scenario.py`

### 配置和提示词
- `rdagent/scenarios/data_science/prompts.yaml`
- `rdagent/scenarios/general_model/prompts.yaml`
- `rdagent/scenarios/data_science/share.yaml`

### 示例和模板
- `rdagent/scenarios/kaggle/experiment/templates/`
- `rdagent/scenarios/data_science/example/`

### Docker配置
- `rdagent/scenarios/kaggle/docker/`
- `rdagent/scenarios/data_science/sing_docker/`

---

## 变更记录 (Changelog)

### 2025-11-17 14:31:27
- **场景文档初始化**：完成scenarios层整体架构文档
- **四大核心场景识别**：data_science、kaggle、qlib、general_model
- **工作流梳理**：各场景的核心工作流和特点清晰
- **扩展指南制定**：新场景添加和现有场景扩展的指导
- **测试策略说明**：场景测试和质量保证流程
- **下一步建议**：需要深入data_science场景的proposal机制和实验管理

---

*最后更新：2025-11-17 14:31:27*