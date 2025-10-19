# AutoSaaS Radar Backend

Python 后端模块，负责数据抓取、AI分析和API服务。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的API密钥
```

### 3. 启动服务

```bash
python run.py
```

或使用uvicorn：

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问API文档

启动后访问 http://localhost:8000/docs 查看交互式API文档。

## 📁 项目结构

```
backend/
├── app.py                 # FastAPI应用入口
├── config.py              # 配置管理
├── models.py              # 数据模型
├── run.py                 # 启动脚本
├── requirements.txt       # 依赖列表
├── .env.example          # 环境变量模板
├── scrapers/             # 数据抓取模块
│   ├── __init__.py
│   ├── rss_scraper.py    # RSS抓取器
│   ├── reddit_scraper.py # Reddit抓取器
│   └── hackernews_scraper.py # HN抓取器
├── analyzers/            # AI分析模块
│   ├── __init__.py
│   └── gpt_analyzer.py   # GPT分析器
├── database/             # 数据库模块
│   ├── __init__.py
│   └── supabase_client.py # Supabase客户端
├── utils/                # 工具模块
│   ├── __init__.py
│   ├── logger.py         # 日志工具
│   └── exceptions.py     # 异常定义
└── tests/                # 测试模块
    ├── __init__.py
    ├── test_scrapers.py  # 抓取器测试
    ├── test_analyzers.py # 分析器测试
    └── test_database.py  # 数据库测试
```

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API密钥 | ✅ |
| `OPENAI_MODEL` | OpenAI模型名称 | ❌ |
| `SUPABASE_URL` | Supabase项目URL | ✅ |
| `SUPABASE_KEY` | Supabase API密钥 | ✅ |
| `RSS_FEEDS` | RSS源列表 | ❌ |
| `REDDIT_CLIENT_ID` | Reddit客户端ID | ❌ |
| `REDDIT_CLIENT_SECRET` | Reddit客户端密钥 | ❌ |

### 数据源配置

系统支持以下数据源：

1. **RSS Feeds**: ProductHunt, Futurepedia等
2. **Reddit**: r/SaaS, r/SideProject等
3. **Hacker News**: 最新Show HN帖子

## 🧪 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_scrapers.py

# 运行带覆盖率的测试
pytest --cov=. tests/

# 运行异步测试
pytest -m asyncio
```

## 📡 API接口

### 核心接口

- `GET /api/tools/latest` - 获取最新工具
- `GET /api/tools/category/{category}` - 按分类获取工具
- `GET /api/tools/trending` - 获取趋势工具
- `GET /api/tools/date/{date}` - 按日期获取工具
- `POST /api/tools/refresh` - 手动刷新数据
- `GET /api/categories` - 获取分类列表
- `GET /api/stats` - 获取统计信息

### 系统接口

- `GET /health` - 健康检查
- `GET /docs` - API文档
- `GET /` - 根路径信息

## 🔄 工作流程

1. **数据抓取**: 定时抓取各大平台AI工具信息
2. **AI分析**: 使用GPT-4o分析工具，提取痛点和SaaS点子
3. **数据存储**: 将分析结果存储到Supabase数据库
4. **API服务**: 提供RESTful API供前端调用

## 📊 数据格式

### 原始工具数据

```json
{
  "tool_name": "AI Resume Builder",
  "description": "Build perfect resumes with AI",
  "votes": 150,
  "link": "https://example.com",
  "date": "2024-01-15T10:00:00Z",
  "category": ""
}
```

### 分析后数据

```json
{
  "tool_name": "AI Resume Builder",
  "category": "Productivity",
  "trend_signal": "Rising",
  "pain_point": "ATS系统优化困难",
  "micro_saas_ideas": ["简历定制工具", "ATS评分检查器"]
}
```

## 🔍 监控和日志

- 日志文件: `logs/autosaas_YYYYMMDD.log`
- 日志级别: DEBUG, INFO, WARNING, ERROR
- 支持彩色控制台输出
- 自动异常捕获和记录

## 🛠 开发指南

### 添加新的数据源

1. 在 `scrapers/` 目录下创建新的抓取器
2. 实现 `fetch_*` 方法
3. 返回 `RawTool` 对象列表
4. 在 `app.py` 中集成新的抓取器

### 添加新的分析器

1. 在 `analyzers/` 目录下创建新的分析器
2. 实现 `analyze_tools` 方法
3. 返回 `AnalyzedTool` 对象列表
4. 在配置中启用新的分析器

### 数据库操作

使用 `SupabaseDB` 类进行数据库操作：

```python
from database import db

# 获取最新工具
tools = await db.get_latest_tools(limit=50)

# 插入工具
success = await db.insert_tools(analyzed_tools)
```

## 🚨 错误处理

系统包含完整的错误处理机制：

- `ScrapingError`: 数据抓取错误
- `AnalysisError`: AI分析错误
- `DatabaseError`: 数据库操作错误
- `APIError`: API调用错误

## 📈 性能优化

- 异步并发抓取
- 数据库连接池
- 批量数据插入
- 智能去重机制
- GPT API调用优化

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 编写测试
4. 提交PR
5. 等待Review

## 📄 许可证

MIT License