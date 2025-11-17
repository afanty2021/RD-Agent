[根目录](../CLAUDE.md) > **deployment**

# 部署配置中心

## 相对路径面包屑
[根目录](../CLAUDE.md) > **deployment**

## 模块职责

Deployment模块负责RD-Agent的完整部署解决方案，包括容器化配置、CI/CD流水线、环境管理和生产环境部署策略，确保系统在不同环境中的可靠运行。

## 部署架构总览

RD-Agent采用多层次的部署架构，支持从开发到生产的全生命周期管理：

```
┌─────────────────────────────────────────────────────────────┐
│                    开发环境 (Development)                      │
├─────────────────────────────────────────────────────────────┤
│                    测试环境 (Testing)                         │
├─────────────────────────────────────────────────────────────┤
│                    预生产环境 (Staging)                       │
├─────────────────────────────────────────────────────────────┤
│                    生产环境 (Production)                      │
└─────────────────────────────────────────────────────────────┘
```

## 🐳 容器化部署架构

### 场景专用容器策略

RD-Agent为不同的应用场景提供专门的容器化解决方案：

#### 1. Kaggle数据科学容器 (`rdagent/scenarios/kaggle/docker/`)

**DS_docker容器** - 通用数据科学环境
```dockerfile
FROM gcr.io/kaggle-gpu-images/python:latest

RUN apt-get clean && apt-get update && apt-get install -y \
    curl \
    vim \
    git \
    build-essential \
    strace \
    && rm -rf /var/lib/apt/lists/*

# 预装优化的机器学习环境
# GPU加速支持
# 常用数据科学库
```

**特性**：
- 基于Kaggle官方GPU镜像
- 预装常用数据科学工具
- GPU加速支持
- 优化的库依赖配置

**kaggle_docker容器** - 竞赛专用环境
- 针对Kaggle竞赛优化的环境
- 竞赛特定依赖预装
- 自动化提交工具集成

**mle_bench_docker容器** - MLE-bench基准环境
- 标准化的基准测试环境
- 性能监控工具集成
- 结果收集和分析工具

#### 2. Qlib量化交易容器 (`rdagent/scenarios/qlib/docker/`)

```dockerfile
FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime

# 安装系统依赖
RUN apt-get clean && apt-get update && apt-get install -y \
    curl \
    vim \
    git \
    build-essential \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# 克隆和安装Qlib
RUN git clone https://github.com/microsoft/qlib.git
WORKDIR /workspace/qlib
RUN git fetch && git reset 3e72593b8c985f01979bebcf646658002ac43b00 --hard
RUN python -m pip install --upgrade cython
RUN python -m pip install -e .

# 安装量化交易专用库
RUN pip install catboost xgboost scipy==1.11.4 tables
```

**特性**：
- 基于PyTorch官方GPU镜像
- 预装Qlib量化框架
- 金融数据处理工具
- 量化模型专用依赖

#### 3. 数据科学专用容器 (`rdagent/scenarios/data_science/sing_docker/`)
- 通用数据科学环境
- 多种机器学习框架支持
- 优化的数据处理工具

### 容器管理策略

#### 多环境容器矩阵
```yaml
# 容器环境配置矩阵
containers:
  development:
    base_image: python:3.10-slim
    gpu_support: false
    debugging_tools: true

  testing:
    base_image: python:3.11-slim
    gpu_support: false
    test_frameworks: true

  production:
    base_image: python:3.11-slim
    gpu_support: true
    security_hardening: true

  kaggle_gpu:
    base_image: gcr.io/kaggle-gpu-images/python:latest
    gpu_support: true
    kaggle_tools: true
```

#### 容器编排配置
```yaml
# docker-compose.yml示例
version: '3.8'
services:
  rdagent-main:
    build: .
    environment:
      - PYTHONPATH=/app
      - CUDA_VISIBLE_DEVICES=0
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "19899:19899"

  rdagent-worker:
    build: .
    command: python -m rdagent.worker
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## 🚀 CI/CD流水线

### GitHub Actions工作流

#### 主要CI流水线 (`.github/workflows/ci.yml`)
```yaml
concurrency:
  cancel-in-progress: true
  group: ${{ github.workflow }}-${{ github.ref }}

jobs:
  ci:
    if: ${{ !cancelled() && !failure() }}
    needs: dependabot
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']

    steps:
      - name: checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          submodules: recursive

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          cache: pip
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: make dev

      - name: Run tests and checks
        run: make lint docs-gen test-offline
```

**流水线特性**：
- 多Python版本并行测试
- 智能缓存策略
- 自动取消过时运行
- 依赖管理自动化

#### PR质量门控 (`.github/workflows/pr.yml`)
```yaml
name: Lint pull request title

on:
  pull_request:
    types: [opened, synchronize, reopened, edited]

jobs:
  lint-title:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '16'

      - name: Install commitlint
        run: npm install --save-dev @commitlint/{config-conventional,cli}

      - name: Validate PR Title
        env:
          BODY: ${{ github.event.pull_request.title }}
        run: |
          echo "$BODY" | npx commitlint --config .commitlintrc.js
```

#### 文档预览流水线 (`.github/workflows/readthedocs-preview.yml`)
- 自动文档构建
- 预览环境部署
- 文档链接生成

### 部署策略

#### 蓝绿部署
```yaml
# 蓝绿部署配置
blue_green_deployment:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0

  health_check:
    path: /health
    port: 19899
    initial_delay_seconds: 30
    period_seconds: 10

  traffic_switch:
    type: weighted
    initial_weight: 10
    increment: 20
    threshold: 95
```

#### 金丝雀部署
```yaml
# 金丝雀发布策略
canary_deployment:
  stages:
    - weight: 5
      duration: 5m
      metrics:
        - success_rate > 99%
        - response_time < 200ms

    - weight: 25
      duration: 15m
      metrics:
        - error_rate < 0.1%

    - weight: 100
      duration: 30m
      auto_promote: true
```

## 🔧 环境配置管理

### 环境变量策略
```bash
# 环境变量分类管理
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://localhost/rdagent_dev

# .env.production
DEBUG=false
LOG_LEVEL=INFO
REDIS_URL=${REDIS_PROD_URL}
DATABASE_URL=${DATABASE_PROD_URL}
SSL_CERT_PATH=/etc/ssl/certs/rdagent.crt
```

### 配置文件管理
```python
# 分层配置系统
class DeploymentConfig:
    # 基础配置
    base_config = "config/base.yaml"

    # 环境特定配置
    env_configs = {
        "development": "config/dev.yaml",
        "testing": "config/test.yaml",
        "production": "config/prod.yaml"
    }

    # 敏感配置（从环境变量或密钥管理服务获取）
    sensitive_configs = [
        "database_url",
        "redis_url",
        "llm_api_keys",
        "ssl_certificates"
    ]
```

## 🔒 安全配置

### 容器安全最佳实践
```dockerfile
# 安全强化配置示例
FROM python:3.11-slim as base

# 创建非root用户
RUN groupadd -r rdagent && useradd -r -g rdagent rdagent

# 安装安全更新
RUN apt-get update && apt-get upgrade -y && apt-get clean

# 设置安全的文件权限
COPY --chown=rdagent:rdagent . /app
WORKDIR /app

# 切换到非root用户
USER rdagent

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:19899/health')" \
  || exit 1
```

### 网络安全配置
```yaml
# 网络策略配置
network_policies:
  ingress:
    - from:
        - ipBlock:
            cidr: 10.0.0.0/8
      ports:
        - protocol: TCP
          port: 19899

  egress:
    - to: []
      ports:
        - protocol: TCP
          port: 443  # HTTPS
        - protocol: TCP
          port: 80   # HTTP
```

## 📊 监控与日志

### 应用监控配置
```python
# 监控指标配置
monitoring_config = {
    "metrics": {
        "system": ["cpu_usage", "memory_usage", "disk_usage"],
        "application": ["request_count", "response_time", "error_rate"],
        "business": ["experiment_count", "model_accuracy", "task_completion"]
    },

    "alerts": {
        "cpu_usage": {"threshold": 80, "operator": "gt"},
        "memory_usage": {"threshold": 90, "operator": "gt"},
        "error_rate": {"threshold": 5, "operator": "gt"}
    },

    "dashboards": {
        "system_overview": "system_dashboard.json",
        "application_metrics": "app_dashboard.json",
        "business_metrics": "business_dashboard.json"
    }
}
```

### 日志聚合配置
```yaml
# 日志配置
logging:
  version: 1
  formatters:
    standard:
      format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    json:
      format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'

  handlers:
    console:
      class: logging.StreamHandler
      formatter: standard

    file:
      class: logging.handlers.RotatingFileHandler
      filename: /app/logs/rdagent.log
      maxBytes: 10485760  # 10MB
      backupCount: 5
      formatter: json

    elk:
      class: logstash.TCPLogstashHandler
      host: logstash.internal
      port: 5959
      version: 1
```

## 📈 性能优化

### 资源配置优化
```yaml
# Kubernetes资源配置示例
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: rdagent
    image: rdagent:latest
    resources:
      requests:
        memory: "2Gi"
        cpu: "1000m"
        nvidia.com/gpu: 1
      limits:
        memory: "8Gi"
        cpu: "4000m"
        nvidia.com/gpu: 2

    # 性能调优参数
    env:
      - name: OMP_NUM_THREADS
        value: "4"
      - name: CUDA_VISIBLE_DEVICES
        value: "0,1"
```

### 缓存策略
```python
# 多层缓存配置
cache_config = {
    "l1_cache": {
        "type": "memory",
        "size": "1GB",
        "ttl": 300  # 5分钟
    },

    "l2_cache": {
        "type": "redis",
        "host": "redis.internal",
        "port": 6379,
        "size": "10GB",
        "ttl": 3600  # 1小时
    },

    "l3_cache": {
        "type": "disk",
        "path": "/app/cache",
        "size": "100GB",
        "ttl": 86400  # 24小时
    }
}
```

## 🔄 自动扩缩容

### HPA配置
```yaml
# 水平Pod自动扩缩容
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rdagent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rdagent
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### VPA配置
```yaml
# 垂直Pod自动扩缩容
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: rdagent-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rdagent
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: rdagent
      maxAllowed:
        cpu: 8
        memory: 16Gi
      minAllowed:
        cpu: 500m
        memory: 1Gi
```

## 🛠️ 部署工具链

### 部署脚本
```bash
#!/bin/bash
# deploy.sh - 部署脚本

set -e

# 环境变量检查
check_env_vars() {
    required_vars=("ENVIRONMENT" "DATABASE_URL" "REDIS_URL")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Error: $var is not set"
            exit 1
        fi
    done
}

# 构建Docker镜像
build_image() {
    echo "Building Docker image..."
    docker build -t rdagent:${VERSION} .
    docker tag rdagent:${VERSION} rdagent:latest
}

# 部署到Kubernetes
deploy_k8s() {
    echo "Deploying to Kubernetes..."
    kubectl apply -f k8s/
    kubectl set image deployment/rdagent rdagent=rdagent:${VERSION}
    kubectl rollout status deployment/rdagent
}

# 主执行流程
main() {
    check_env_vars
    build_image
    deploy_k8s
    echo "Deployment completed successfully!"
}
```

### 配置管理工具
```python
# 部署配置管理器
class DeploymentManager:
    def __init__(self, environment):
        self.environment = environment
        self.config = self.load_config()

    def load_config(self):
        """加载环境特定配置"""
        config_file = f"config/{self.environment}.yaml"
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def validate_config(self):
        """验证配置完整性"""
        required_keys = ['database', 'redis', 'logging']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config: {key}")

    def deploy(self):
        """执行部署流程"""
        self.validate_config()
        self.build_application()
        self.deploy_infrastructure()
        self.setup_monitoring()

    def rollback(self):
        """回滚到上一个版本"""
        # 实现回滚逻辑
        pass
```

## 🚨 故障排除

### 常见部署问题

#### 1. 容器启动失败
```bash
# 问题：容器无法启动
# 排查步骤：
docker logs <container_id>
docker inspect <container_id>
kubectl describe pod <pod_name>
kubectl logs <pod_name>
```

#### 2. 网络连接问题
```bash
# 问题：服务间无法通信
# 排查步骤：
kubectl get svc
kubectl describe svc <service_name>
kubectl exec -it <pod_name> -- nslookup <service_name>
```

#### 3. 资源不足
```bash
# 问题：Pod处于Pending状态
# 排查步骤：
kubectl describe pod <pod_name> | grep -A 10 "Events"
kubectl top nodes
kubectl describe node <node_name>
```

### 监控告警
```yaml
# 告警规则配置
groups:
- name: rdagent.rules
  rules:
  - alert: HighCPUUsage
    expr: cpu_usage_percent > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"
      description: "CPU usage is above 80% for more than 5 minutes"

  - alert: HighMemoryUsage
    expr: memory_usage_percent > 90
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High memory usage detected"
      description: "Memory usage is above 90% for more than 2 minutes"
```

## 📚 最佳实践

### 部署清单
```markdown
## 部署前检查清单

- [ ] 环境变量配置正确
- [ ] 密钥和证书已更新
- [ ] 数据库迁移脚本准备就绪
- [ ] 回滚策略已制定
- [ ] 监控告警已配置
- [ ] 备份策略已确认
- [ ] 性能基准测试完成
- [ ] 安全扫描通过
```

### 版本管理
```bash
# 语义化版本控制
VERSION="v1.2.3"

# 版本标签管理
git tag -a $VERSION -m "Release version $VERSION"
git push origin $VERSION

# 构建镜像
docker build -t rdagent:$VERSION .
docker tag rdagent:$VERSION rdagent:latest
```

## 相关文件清单

### 容器配置
- `rdagent/scenarios/kaggle/docker/DS_docker/Dockerfile`
- `rdagent/scenarios/kaggle/docker/mle_bench_docker/Dockerfile`
- `rdagent/scenarios/qlib/docker/Dockerfile`
- `docker-compose.yml`

### CI/CD配置
- `.github/workflows/ci.yml`
- `.github/workflows/pr.yml`
- `.github/workflows/release.yml`
- `.github/workflows/readthedocs-preview.yml`

### 部署配置
- `k8s/deployment.yaml`
- `k8s/service.yaml`
- `k8s/configmap.yaml`
- `k8s/secret.yaml`

### 监控配置
- `monitoring/prometheus.yml`
- `monitoring/grafana/dashboards/`
- `monitoring/alertmanager.yml`

---

## 变更记录 (Changelog)

### 2025-11-17 14:41:40 - 部署配置中心文档创建
- **容器化架构完整分析**：深入解析场景专用容器策略和管理机制
- **CI/CD流水线详细说明**：涵盖GitHub Actions工作流、质量门控、部署策略
- **环境配置管理**：提供多环境配置、变量管理、安全配置的最佳实践
- **监控和性能优化**：详细介绍应用监控、日志聚合、自动扩缩容策略
- **部署工具链完整说明**：提供部署脚本、配置管理、故障排除的实用指南
- **安全强化措施**：涵盖容器安全、网络安全、密钥管理的安全最佳实践

---

*最后更新：2025-11-17 14:41:40*