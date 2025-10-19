#!/bin/bash

# AutoSaaS Radar - 依赖安装脚本
# 窗口10：部署自动化

echo "📦 安装 AutoSaaS Radar 依赖项..."
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查操作系统
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo -e "\n🖥️ 检测到操作系统: $OS"

# 安装Node.js依赖
echo -e "\n📦 安装前端依赖..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "安装 npm 依赖..."
    npm install
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 前端依赖安装成功${NC}"
    else
        echo -e "${RED}❌ 前端依赖安装失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️ 前端依赖已存在，跳过安装${NC}"
fi

cd ..

# 安装Python依赖
echo -e "\n🐍 安装后端依赖..."
cd backend

if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 虚拟环境创建成功${NC}"
    else
        echo -e "${RED}❌ 虚拟环境创建失败${NC}"
        exit 1
    fi
fi

# 激活虚拟环境
echo "激活虚拟环境..."
if [ "$OS" = "windows" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# 安装Python包
if [ -f "requirements.txt" ]; then
    echo "安装Python依赖包..."
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Python依赖安装成功${NC}"
    else
        echo -e "${RED}❌ Python依赖安装失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️ requirements.txt 不存在，创建基础依赖文件${NC}"
    cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
requests==2.31.0
openai==1.3.7
supabase==1.0.4
schedule==1.2.0
python-dotenv==1.0.0
beautifulsoup4==4.12.2
lxml==4.9.3
pydantic==2.5.0
EOF
    pip install -r requirements.txt
fi

cd ..

# 安装全局工具
echo -e "\n🌍 安装全局工具..."

# Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "安装 Vercel CLI..."
    npm install -g vercel
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Vercel CLI 安装成功${NC}"
    else
        echo -e "${RED}❌ Vercel CLI 安装失败${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Vercel CLI 已安装${NC}"
fi

# Railway CLI (可选)
echo "是否安装 Railway CLI? (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    if ! command -v railway &> /dev/null; then
        echo "安装 Railway CLI..."
        npm install -g @railway/cli
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Railway CLI 安装成功${NC}"
        else
            echo -e "${RED}❌ Railway CLI 安装失败${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Railway CLI 已安装${NC}"
    fi
fi

# 创建必要的目录
echo -e "\n📁 创建必要的目录..."
mkdir -p logs
mkdir -p data
mkdir -p temp

echo -e "${GREEN}✅ 目录创建完成${NC}"

# 复制环境变量文件
echo -e "\n⚙️ 设置环境变量..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ .env 文件已创建，请编辑设置您的API密钥${NC}"
    else
        echo -e "${YELLOW}⚠️ .env.example 不存在${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ .env 文件已存在${NC}"
fi

# 设置脚本执行权限
echo -e "\n🔐 设置脚本执行权限..."
chmod +x scripts/*.sh
chmod +x deploy/*.sh
echo -e "${GREEN}✅ 脚本权限设置完成${NC}"

# 依赖检查
echo -e "\n🔍 依赖检查..."

echo "检查Node.js版本..."
node --version
npm --version

echo "检查Python版本..."
python3 --version
pip --version

echo "检查全局工具..."
vercel --version 2>/dev/null || echo "Vercel CLI 未安装"
railway --version 2>/dev/null || echo "Railway CLI 未安装"

echo -e "\n=================================="
echo -e "${GREEN}🎉 依赖安装完成！${NC}"
echo -e "\n📝 下一步操作:"
echo "1. 编辑 .env 文件，设置您的API密钥"
echo "2. 运行 'scripts/quick-test.sh' 验证安装"
echo "3. 运行 'scripts/health-check.py' 检查系统状态"
echo "4. 使用 'deploy/vercel-deploy.sh' 部署前端"
echo "5. 使用 'deploy/backend-deploy.sh' 部署后端"
echo -e "\n🚀 开始您的 AutoSaaS Radar 之旅吧！"