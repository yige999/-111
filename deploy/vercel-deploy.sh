#!/bin/bash

# AutoSaaS Radar - Vercel 部署脚本
# 窗口10：部署自动化

echo "🚀 开始 AutoSaaS Radar Vercel 部署..."

# 检查 Vercel CLI 是否安装
if ! command -v vercel &> /dev/null; then
    echo "📦 安装 Vercel CLI..."
    npm install -g vercel
fi

# 设置环境变量
echo "⚙️ 设置环境变量..."
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_KEY
vercel env add OPENAI_API_KEY

# 部署到 Vercel
echo "🚀 部署到 Vercel..."
vercel --prod

echo "✅ 部署完成！"
echo "🌐 前端URL: https://your-app.vercel.app"
echo "📊 仪表盘: https://your-app.vercel.app/dashboard"