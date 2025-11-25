# 🚀 RD-Agent - 机器学习工程代理

## 📋 概述

RD-Agent是一个面向机器学习工程（MLE）的自主代理系统，旨在自动化研究和开发流程。该项目在MLE-bench基准测试中表现优异，支持多种场景包括数据科学竞赛、Kaggle竞赛、量化交易和通用模型开发。

## ✨ 核心特性

- **🤖 自主进化**：基于CoSTEER框架的多进程进化策略
- **🧠 多场景支持**：数据科学、Kaggle、量化交易、通用模型
- **🔄 多LLM后端**：支持OpenAI、Azure OpenAI、Claude、本地模型
- **📊 性能监控**：实时性能指标收集和分析
- **🐳 Docker化**：完整的容器化部署方案
- **🔧 类型安全**：输入验证和命令注入防护

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Docker（推荐）
- Git

### 安装方式

#### 1. 本地开发

```bash
# 克隆仓库
git clone https://github.com/afanty2021/RD-Agent.git
cd RD-Agent

# 安装依赖
pip install -e .
```

#### 2. Docker部署

```bash
# 构建并运行
docker build -t rdagent:latest .
docker run -p 8000:8000 rdagent:latest
```

#### 3. 生产环境

```bash
# 使用部署脚本
./scripts/deploy.sh
```

## 🔧 配置说明

创建 `.env` 文件：

```bash
# API密钥
OPENAI_API_KEY=your_api_key_here

# 环境变量
PYTHONPATH=/app
RD_AGENT_ENV=development
```

## 📋 部署命令

```bash
# 开发环境
make dev

# 生产环境
make prod

# Docker环境
make docker
```

## 🛠️ 故障排除

### 常见问题

1. **端口占用**
   ```bash
   lsof -i :8000
   ```

2. **容器问题**
   ```bash
   docker logs rdagent
   ```

3. **权限问题**
   ```bash
   ls -la /app
   ```

## 📚 文档和资源

- [完整文档](https://rdagent.readthedocs.io/)
- [技术报告](https://rdagent.azurewebsites.net/)
- [演示视频](https://www.youtube.com/watch?v=JJ4JYO3HscM&list=PLALmKB0_N3i52fhUmPQiL4jsO354uopR)
- [Discord社区](https://discord.gg/ybQ97B6Jjy)

## 🤝 贡献指南

欢迎贡献代码、文档、测试用例和功能建议！

请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与项目。