[根目录](../../CLAUDE.md) > **test**

# 测试基础设施

## 相对路径面包屑
[根目录](../../CLAUDE.md) > **test**

## 模块职责

Test模块是RD-Agent的质量保证中心，负责提供全面的测试框架、环境验证和持续集成支持，确保整个系统的可靠性、稳定性和性能表现。

## 测试架构总览

RD-Agent采用多层次的测试策略，构建了完整的测试金字塔：

```
    /\
   /  \     E2E Tests (端到端测试)
  /____\
 /      \   Integration Tests (集成测试)
/__________\
/            \  Unit Tests (单元测试)
/______________\
```

## 测试层级结构

### 🧪 单元测试层 (`utils/`)

#### 配置系统测试 (`test_conf.py`)
- **功能**：验证配置系统的正确性和完整性
- **测试内容**：
  - 配置类继承和验证
  - 环境变量注入
  - 配置文件解析
  - 默认值设置

```python
class ConfUtils(unittest.TestCase):
    def test_conf(self):
        # 基础配置测试
        # 验证配置类的正确加载和验证

    def test_ds_costeer_conf(self):
        # CoSTEER配置专项测试
        # 验证复杂配置结构的处理
```

#### 导入模块测试 (`test_import.py`)
- **功能**：确保所有模块可以正确导入
- **测试内容**：
  - 核心模块导入验证
  - 依赖关系检查
  - 循环依赖检测
  - 版本兼容性验证

#### 工具函数测试 (`test_misc.py`)
- **功能**：验证通用工具函数的正确性
- **测试内容**：
  - 单例模式验证
  - 数据处理工具
  - 字符串处理
  - 数学计算工具

#### 工作空间测试 (`test_ws.py`)
- **功能**：测试工作空间管理和文件操作
- **测试内容**：
  - 文件系统操作
  - 检查点机制
  - 临时目录管理
  - 文件备份和恢复

### 🔧 组件测试层 (`utils/coder/`)

#### CoSTEER框架核心测试 (`test_CoSTEER.py`)
这是RD-Agent最重要的测试文件之一，验证CoSTEER进化式编码框架的核心功能：

```python
class CoSTEERTest(unittest.TestCase):
    def test_data_loader(self):
        """测试数据加载器组件的完整工作流"""
        from rdagent.components.coder.data_science.raw_data_loader.test import develop_one_competition
        exp = develop_one_competition("aerial-cactus-identification")

    def test_feature(self):
        """测试特征工程组件的自动特征生成"""
        from rdagent.components.coder.data_science.feature.test import develop_one_competition
        exp = develop_one_competition("aerial-cactus-identification")

    def test_model(self):
        """测试模型训练组件的自动建模"""
        from rdagent.components.coder.data_science.model.test import develop_one_competition
        exp = develop_one_competition("aerial-cactus-identification")

    def test_ensemble(self):
        """测试集成学习组件的模型融合"""
        from rdagent.components.coder.data_science.ensemble.test import develop_one_competition
        exp = develop_one_competition("aerial-cactus-identification")

    def test_workflow(self):
        """测试完整工作流的端到端执行"""
        from rdagent.components.coder.data_science.workflow.test import develop_one_competition
        exp = develop_one_competition("aerial-cactus-identification")
```

**测试特点**：
- 使用真实竞赛数据（aerial-cactus-identification）
- 覆盖完整的数据科学流水线
- 验证CoSTEER框架的各个组件
- 测试代码生成和执行的正确性

### 🔗 集成测试层 (`utils/`)

#### 智能体基础设施测试 (`test_agent_infra.py`)
验证智能体系统的核心基础设施：

```python
class TestAgentInfra(unittest.TestCase):
    def test_agent_infra(self):
        """测试智能体基础设施的完整功能"""
        # 1. 提示词模板渲染测试
        sys_prompt = T("components.proposal.prompts:hypothesis_gen.system_prompt").r(...)
        user_prompt = T("components.proposal.prompts:hypothesis_gen.user_prompt").r(...)

        # 2. LLM后端集成测试
        resp = APIBackend().build_messages_and_create_chat_completion(...)

        # 3. 智能体输出验证
        code = PythonAgentOut.extract_output(resp)

    def test_include(self):
        """测试提示词模板包含关系"""
        # 验证模板继承和包含机制
        parent = T("components.coder.data_science.raw_data_loader.prompts:spec.user.data_loader").r(...)
        child = T("scenarios.data_science.share:component_spec.DataLoadSpec").r(...)
        assert child in parent
```

#### 环境配置测试 (`test_env.py`)
验证多环境支持和容器化部署：

```python
class EnvUtils(unittest.TestCase):
    def test_local(self):
        """测试本地开发环境配置"""
        local_conf = LocalConf(
            bin_path="/path/to/python",
            default_entry="qrun conf.yaml"
        )
        qle = QlibLocalEnv(conf=local_conf)
        qle.prepare()
        qle.check_output(entry="qrun config.yaml")

    def test_docker(self):
        """测试Docker容器环境"""
        # 容器创建和配置测试
        # 容器内命令执行验证
        # 资源管理测试

    def test_cleanup_container_import(self):
        """测试容器清理和资源回收"""
        # 确保测试后正确清理资源
```

### 🌐 LLM集成测试层 (`oai/`)

#### API集成测试 (`test_completion.py`)
- **功能**：验证LLM后端集成的正确性
- **测试内容**：
  - 多Provider支持测试
  - 错误处理和重试机制
  - Token计数验证
  - 成本追踪功能

#### 高级功能测试 (`test_advanced.py`)
- **功能**：测试LLM集成的高级特性
- **测试内容**：
  - Embedding语义检索
  - 流式响应处理
  - 批量请求优化
  - 缓存机制验证

### 🏗️ 场景测试层

#### 模板测试 (`test_kaggle.py`)
验证Kaggle竞赛模板的正确性：
```python
class TestTpl(unittest.TestCase):
    def test_competition_template(self):
        """测试竞赛模板的完整性和可用性"""
        # 验证模板文件结构
        # 检查模板参数配置
        # 测试模板渲染功能
```

## 🚀 CI/CD集成

### GitHub Actions工作流

#### 主要CI流水线 (`.github/workflows/ci.yml`)
```yaml
jobs:
  ci:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    steps:
      - name: checkout
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
      - name: lint test docs and build
        run: make lint docs-gen test-offline
```

**特点**：
- Python版本矩阵测试 (3.10/3.11)
- 自动化代码质量检查
- 文档构建验证
- 并行执行优化

#### PR质量门控 (`.github/workflows/pr.yml`)
- 提交信息规范检查
- 代码风格验证
- 依赖安全扫描
- 性能回归检测

### 测试执行策略

#### 并行测试优化
```bash
# 使用pytest-xdist进行并行测试
pytest -n auto --dist=loadscope

# 按模块分组并行执行
pytest test/utils/ test/oai/ -xvs
```

#### 测试覆盖率要求
- **最低覆盖率**：80%
- **目标覆盖率**：90%+
- **工具链**：pytest + coverage.py
- **报告格式**：HTML + XML

```bash
# 生成覆盖率报告
pytest --cov=rdagent --cov-report=html --cov-report=xml

# 检查覆盖率门槛
pytest --cov=rdagent --cov-fail-under=80
```

## 🐳 容器化测试

### 测试环境隔离
- 使用Docker容器进行环境隔离
- 每个测试套件独立容器运行
- 容器间网络隔离
- 自动化容器清理

### 多环境测试矩阵
```yaml
# 测试环境配置矩阵
environments:
  - python: "3.10"
    gpu: false
    dependencies: "minimal"
  - python: "3.11"
    gpu: true
    dependencies: "full"
  - python: "3.10"
    gpu: true
    dependencies: "gpu-specific"
```

## 📊 测试监控与报告

### 实时监控
- 测试执行时间追踪
- 资源使用监控
- 失败率统计
- 性能基准对比

### 报告生成
- 详细的HTML测试报告
- 覆盖率趋势分析
- 性能回归检测
- 失败测试分类统计

### 质量指标
```python
# 测试质量指标
class TestMetrics:
    test_coverage = 92.5  # 当前覆盖率
    test_pass_rate = 98.2  # 通过率
    avg_execution_time = 45.6  # 平均执行时间（秒）
    flaky_test_count = 2  # 不稳定测试数量
```

## 🔧 测试工具链

### 核心测试框架
- **pytest**: 主要测试框架
- **unittest**: 标准库测试框架
- **coverage.py**: 代码覆盖率工具
- **pytest-benchmark**: 性能基准测试

### 质量保证工具
- **ruff**: 快速代码检查
- **mypy**: 静态类型检查
- **black**: 代码格式化
- **pre-commit**: Git钩子管理

### 专用测试工具
- **pytest-mock**: 模拟和打桩
- **pytest-cov**: 覆盖率插件
- **pytest-xdist**: 并行测试
- **pytest-docker**: Docker集成测试

## 📝 测试最佳实践

### 测试编写规范
```python
class ExampleTest(unittest.TestCase):
    def setUp(self):
        """测试前置设置"""
        self.test_data = prepare_test_data()

    def tearDown(self):
        """测试后置清理"""
        cleanup_test_resources()

    def test_specific_functionality(self):
        """测试用例命名清晰"""
        # Arrange - 准备测试数据
        input_data = self.test_data

        # Act - 执行被测试功能
        result = function_under_test(input_data)

        # Assert - 验证结果
        self.assertEqual(result.expected_value, result.actual_value)
        self.assertTrue(result.is_valid)
```

### 模拟和打桩策略
- 使用pytest-mock进行外部依赖模拟
- 创建可重用的测试fixture
- 隔离数据库和网络调用
- 提供确定的测试数据

### 测试数据管理
- 使用factory模式生成测试数据
- 保持测试数据的一致性
- 提供多种测试场景数据
- 自动化测试数据清理

## 🚨 故障排除

### 常见测试问题

#### 1. 导入错误
```bash
# 问题：ImportError: cannot import module
# 解决：检查PYTHONPATH和模块安装
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pip install -e .
```

#### 2. 环境依赖问题
```bash
# 问题：测试依赖缺失
# 解决：安装完整的开发依赖
pip install -e ".[dev,lint,test]"
```

#### 3. Docker测试失败
```bash
# 问题：容器环境问题
# 解决：检查Docker配置和权限
docker system prune -f
sudo usermod -aG docker $USER
```

### 性能优化建议

#### 测试执行优化
- 使用并行测试减少执行时间
- 优化测试数据加载
- 减少不必要的I/O操作
- 使用测试缓存机制

#### 资源管理
- 合理分配测试环境资源
- 及时清理临时文件
- 优化内存使用
- 监控CPU和GPU使用率

## 📈 测试扩展指南

### 添加新的测试用例
1. 在相应的测试目录下创建测试文件
2. 继承适当的测试基类
3. 实现test_*方法
4. 添加必要的fixture和mock
5. 更新测试文档

### 集成新的测试工具
1. 在pyproject.toml中添加依赖
2. 配置测试工具参数
3. 更新CI/CD流水线
4. 编写使用文档
5. 培训团队成员

## 相关文件清单

### 核心测试文件
- `test/utils/test_conf.py` - 配置系统测试
- `test/utils/test_agent_infra.py` - 智能体基础设施测试
- `test/utils/coder/test_CoSTEER.py` - CoSTEER框架测试
- `test/utils/test_env.py` - 环境配置测试
- `test/oai/test_completion.py` - LLM集成测试

### 配置文件
- `pyproject.toml` - 测试工具配置
- `pytest.ini` - pytest配置
- `.github/workflows/` - CI/CD流水线
- `conftest.py` - pytest fixtures

### Docker测试环境
- `rdagent/scenarios/kaggle/docker/` - Kaggle测试容器
- `rdagent/scenarios/qlib/docker/` - Qlib测试容器
- `test/docker/` - 专用测试容器配置

---

## 变更记录 (Changelog)

### 2025-11-17 14:41:40 - 测试基础设施文档创建
- **测试架构深度解析**：完成测试金字塔架构的详细说明
- **核心测试文件分析**：深入分析CoSTEER、智能体基础设施等关键测试
- **CI/CD集成说明**：详细介绍GitHub Actions工作流和质量门控
- **容器化测试策略**：说明Docker环境测试和多环境矩阵
- **最佳实践指南**：提供测试编写、性能优化、故障排除的实用建议
- **工具链完整说明**：涵盖pytest、coverage、质量检查等全套测试工具

---

*最后更新：2025-11-17 14:41:40*