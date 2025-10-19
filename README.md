# AutoSaaS Radar — 全自动 AI SaaS 趋势雷达

## 🎯 项目简介
全自动自用的 AI SaaS 趋势雷达，自动发现新上线 AI 工具/微 SaaS 机会，提炼用户痛点，并生成可复制点子。

**核心价值**：每天自动显示热门 AI 工具 + 提炼用户痛点 + 生成可做的 Micro SaaS 点子 + 极简可视化仪表盘

## 🚀 功能特性
- ✅ 每日自动抓取各大平台 AI 工具
- ✅ AI 分析用户痛点，生成 Micro SaaS 点子
- ✅ 趋势信号判断（Rising/Stable/Declining）
- ✅ 简洁仪表盘展示
- ✅ 按类别筛选和导出
- ✅ 完全全自动运行

## 📁 项目结构
```
AutoSaaS-Radar/
├── README.md              # 项目说明
├── COLLABORATION.md       # 多窗口协作指南
├── API_CONTRACT.md        # API 接口契约
├── DATABASE_SCHEMA.md     # 数据库结构
├── PROGRESS.md           # 开发进度
├── ISSUES.md             # 问题记录
├── backend/              # Python 后端模块
├── frontend/             # Next.js 前端仪表盘
├── database/             # 数据库脚本
├── config/               # 配置文件
├── scripts/              # 自动化脚本
└── deploy/               # 部署配置
```

## 🛠 技术栈
- **后端**: Python + FastAPI + OpenAI GPT-4o
- **前端**: Next.js + TailwindCSS
- **数据库**: Supabase (PostgreSQL)
- **部署**: Vercel + Cloudflare
- **自动化**: Cron Job + Make

## 🔄 工作流程
1. **数据抓取** (09:00 AM): ProductHunt, Futurepedia, Reddit, Hacker News
2. **AI 分析** (09:15 AM): GPT-4o 分类 + 提炼痛点 + 生成点子
3. **数据存储** (09:20 AM): 存入 Supabase 数据库
4. **前端展示** (09:25 AM): Next.js 仪表盘自动更新
5. **可选推送** (09:30 AM): 邮件/Telegram 推送

## 🎨 页面预览
- **Home Dashboard**: 今日 Top 5 工具 + Micro SaaS 点子
- **Explore**: 按类别筛选历史趋势
- **Trend Insights**: 每周趋势报告，痛点摘要

## 🚀 快速开始
```bash
# 1. 克隆项目
git clone <repo-url>
cd AutoSaaS-Radar

# 2. 设置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 启动后端
cd backend
pip install -r requirements.txt
python main.py

# 4. 启动前端
cd ../frontend
npm install
npm run dev

# 5. 设置数据库
cd ../database
# 运行 migration 脚本
```

## 🤖 多窗口开发
此项目支持 4 个 VSCode 窗口并行开发：
- **窗口1**: Python 后端开发
- **窗口2**: Next.js 前端开发
- **窗口3**: 数据库和配置
- **窗口4**: 自动化和部署

详细协作指南请查看 [COLLABORATION.md](./COLLABORATION.md)

## 📊 数据格式
工具数据包含：
- 工具名称、描述、类别
- 趋势信号（Rising/Stable/Declining）
- 用户痛点
- 可复制的 Micro SaaS 点子
- 原始链接和投票数

## 🎯 目标用户
独立开发者 / Micro SaaS 爱好者，希望：
- 发现最新的 AI 工具趋势
- 获得经过分析的创业点子
- 节省趋势研究时间
- 快速找到可复制的商业模式

## 📄 许可证
MIT License

---

**开发状态**: 🟡 框架搭建完成，各模块开发中

*最后更新: 2024-01-15*