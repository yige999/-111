#!/bin/bash

# AutoSaaS Radar - 后端部署脚本
# 窗口10：部署自动化

echo "🚀 开始后端服务部署..."

# 进入后端目录
cd ../backend

# 安装依赖
echo "📦 安装 Python 依赖..."
pip install -r requirements.txt

# 使用 Railway 部署 (替代方案)
if ! command -v railway &> /dev/null; then
    echo "📦 安装 Railway CLI..."
    npm install -g @railway/cli
fi

echo "🚀 部署到 Railway..."
railway login
railway init
railway up

echo "✅ 后端部署完成！"
echo "🔗 API URL: https://your-backend.railway.app"