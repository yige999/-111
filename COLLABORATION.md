# AutoSaaS Radar — 多窗口协作指南

## 🎯 项目目标
全自动 AI SaaS 趋势雷达，自动发现新上线AI工具/微SaaS机会，提炼用户痛点，并生成可复制点子。

## 👥 窗口分工（10窗口极速版）

### 窗口1：项目总协调 (`根目录/`)
- 项目整体协调
- 进度跟踪更新
- 问题解决协调
- 最终整合测试

**负责人**：窗口1 Claude Code
**预计时间**：30分钟全程

### 窗口2：RSS 抓取模块 (`backend/scrapers/`)
- ProductHunt RSS 抓取
- Futurepedia RSS 抓取
- 数据清洗和格式化
- 错误处理

**负责人**：窗口2 Claude Code
**预计时间**：15分钟

### 窗口3：社媒抓取模块 (`backend/scrapers/`)
- Reddit r/SaaS 抓取
- Reddit r/SideProject 抓取
- Hacker News 抓取
- API 集成

**负责人**：窗口3 Claude Code
**预计时间**：15分钟

### 窗口4：GPT 分析核心 (`backend/analyzer/`)
- OpenAI API 集成
- 分析 Prompt 开发
- 痛点提炼逻辑
- 点子生成算法

**负责人**：窗口4 Claude Code
**预计时间**：20分钟

### 窗口5：数据存储模块 (`backend/database/`)
- Supabase 连接配置
- 数据库操作封装
- 数据验证逻辑
- 批量插入优化

**负责人**：窗口5 Claude Code
**预计时间**：15分钟

### 窗口6：API 接口开发 (`backend/api/`)
- FastAPI 路由设计
- API 响应格式
- 数据查询接口
- 错误处理

**负责人**：窗口6 Claude Code
**预计时间**：15分钟

### 窗口7：前端首页 (`frontend/pages/`)
- Next.js 项目初始化
- 首页 Dashboard 开发
- Top 5 工具展示
- 基础组件

**负责人**：窗口7 Claude Code
**预计时间**：20分钟

### 窗口8：前端页面 (`frontend/pages/`)
- Explore 页面开发
- Trend Insights 页面
- 筛选和搜索功能
- 页面路由

**负责人**：窗口8 Claude Code
**预计时间**：20分钟

### 窗口9：UI 样式组件 (`frontend/components/`)
- TailwindCSS 配置
- 卡片组件设计
- 趋势标记样式
- 响应式布局

**负责人**：窗口9 Claude Code
**预计时间**：15分钟

### 窗口10：部署自动化 (`scripts/` + `deploy/`)
- Vercel 部署配置
- 环境变量设置
- 调度脚本开发
- 快速测试

**负责人**：窗口10 Claude Code
**预计时间**：15分钟

## 🔄 协作规则

### 文件所有权
- 每个窗口专注自己的目录
- 共享文件需要先声明再修改
- 避免同时修改同一个文件

### 沟通机制
1. **进度更新**：修改此文件对应模块状态
2. **API 契约**：在 `API_CONTRACT.md` 中定义接口
3. **数据格式**：在 `DATABASE_SCHEMA.md` 中定义结构
4. **问题记录**：在 `ISSUES.md` 中记录阻塞问题

### 同步频率
- 每完成一个功能模块更新进度
- 遇到依赖问题及时沟通
- 定期检查其他模块进度

## 📁 项目结构（10窗口版）
```
AutoSaaS-Radar/
├── README.md              # 项目说明
├── COLLABORATION.md       # 协作指南（本文件）
├── API_CONTRACT.md        # API 接口契约
├── DATABASE_SCHEMA.md     # 数据库结构
├── PROGRESS.md           # 各模块进度
├── ISSUES.md             # 问题记录
├── backend/              # Python 后端
│   ├── scrapers/         # 窗口2,3：抓取模块
│   ├── analyzer/         # 窗口4：GPT分析
│   ├── database/         # 窗口5：数据存储
│   └── api/              # 窗口6：API接口
├── frontend/             # Next.js 前端
│   ├── pages/            # 窗口7,8：页面开发
│   ├── components/       # 窗口9：UI组件
│   └── styles/           # 窗口9：样式文件
├── database/             # 数据库脚本
├── config/               # 配置文件
├── scripts/              # 窗口10：自动化脚本
└── deploy/               # 窗口10：部署配置
```

## 🚀 开始步骤

1. **每个窗口打开同一个项目目录**
2. **根据分工专注各自模块**
3. **及时更新进度到 PROGRESS.md**
4. **遇到协作问题查看 ISSUES.md**

## ⏰ 30分钟极速时间线
- 窗口1（总协调）：30分钟全程
- 窗口2（RSS抓取）：15分钟
- 窗口3（社媒抓取）：15分钟
- 窗口4（GPT分析）：20分钟
- 窗口5（数据存储）：15分钟
- 窗口6（API接口）：15分钟
- 窗口7（前端首页）：20分钟
- 窗口8（前端页面）：20分钟
- 窗口9（UI组件）：15分钟
- 窗口10（部署自动化）：15分钟

**并行开发总预计**：30分钟！

## 🚀 极速协作策略
1. **前10分钟**：所有窗口同时初始化项目结构
2. **10-20分钟**：核心功能并行开发
3. **20-30分钟**：集成测试和部署

## 📋 关键依赖关系
- 窗口5需要在窗口2,3,4之前完成基础配置
- 窗口7,8,9需要窗口6的API接口
- 窗口10在最后5分钟进行集成部署

---

*现在可以开启10个 VSCode 窗口，每个窗口打开此项目目录，开始30分钟极速开发！*