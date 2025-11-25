#!/bin/bash

# RD-Agent 部署脚本

set -e

echo "🚀 开始部署 RD-Agent..."

# 检查环境
if [ "$CI" = true ]; then
    echo "📦 CI/CD环境检测到"
else
    echo "🔧 本地开发环境"
fi

# 构建Docker镜像
echo "🐳 构建Docker镜像..."
docker build -t rdagent:latest .

# 推送镜像到仓库
echo "📤 推送Docker镜像到Docker Hub..."
docker push rdagent:latest

# 部署到生产环境
if [ "$DEPLOY_PROD" = true ]; then
    echo "🌐 部署到生产环境..."
    # 这里可以添加生产环境的部署命令
    # docker run -d --env-file .env.prod -p 8000:8000 rdagent:latest
else
    echo "🧪 部署完成！"
fi

echo "✅ RD-Agent 部署完成！"