# API 契约 — AutoSaaS Radar

## 数据格式标准

### 1. 工具数据格式（原始抓取）
```json
{
  "tool_name": "AI Resume Optimizer",
  "description": "Optimize resumes for ATS systems",
  "votes": 120,
  "link": "https://producthunt.com/posts/ai-resume-optimizer",
  "date": "2024-01-15T09:00:00Z",
  "category": ""
}
```

### 2. 分析后数据格式（存储到数据库）
```json
{
  "tool_name": "AI Resume Optimizer",
  "description": "Optimize resumes for ATS systems",
  "category": "Productivity",
  "votes": 120,
  "link": "https://producthunt.com/posts/ai-resume-optimizer",
  "trend_signal": "Rising",
  "pain_point": "ATS系统识别不准确，简历匹配度低",
  "micro_saas_ideas": [
    "Recruiter Resume Parser",
    "Resume Tailor Tool"
  ],
  "date": "2024-01-15T09:15:00Z"
}
```

### 3. 前端展示数据格式
```json
{
  "id": 1,
  "tool_name": "AI Resume Optimizer",
  "category": "Productivity",
  "trend_signal": "Rising",
  "pain_point": "ATS系统识别不准确，简历匹配度低",
  "micro_saas_ideas": [
    "Recruiter Resume Parser",
    "Resume Tailor Tool"
  ],
  "link": "https://producthunt.com/posts/ai-resume-optimizer",
  "votes": 120,
  "created_at": "2024-01-15T09:15:00Z"
}
```

## API 接口定义

### 后端 Python API（FastAPI）
```
GET  /api/tools/latest          # 获取最新工具（限制数量）
GET  /api/tools/category/{cat}  # 按分类获取
GET  /api/tools/trending        # 获取趋势工具
GET  /api/tools/date/{date}     # 按日期获取
POST /api/tools/refresh         # 手动刷新数据
```

### 前端 Next.js API Routes
```
GET  /api/tools                # 从 Supabase 获取数据
GET  /api/tools/categories     # 获取所有分类
GET  /api/tools/stats          # 获取统计信息
```

## 分类枚举
```javascript
const CATEGORIES = [
  "Video",
  "Text",
  "Productivity",
  "Marketing",
  "Education",
  "Audio",
  "Other"
];
```

## 趋势信号枚举
```javascript
const TREND_SIGNALS = [
  "Rising",    // 上升趋势
  "Stable",    // 稳定
  "Declining"  // 下降趋势
];
```

## 数据库字段映射
```sql
CREATE TABLE tools (
    id SERIAL PRIMARY KEY,
    tool_name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    votes INT DEFAULT 0,
    link TEXT,
    trend_signal TEXT,
    pain_point TEXT,
    micro_saas_ideas JSONB,
    date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## GPT 分析 Prompt 模板
```
你是一个AI趋势分析系统。
输入是一组最新抓取的AI工具，包括名称、描述、点赞数。
请输出JSON数组：
1. 分类工具类型（Video/Text/Productivity/Marketing/Education/Audio/Other）
2. 提炼用户痛点
3. 为每个痛点生成1~3个可独立开发的Micro SaaS点子
4. 判断趋势信号（Rising / Stable / Declining）

输入数据: {tools_data}

输出格式:
{
  "analyzed_tools": [
    {
      "tool_name": "工具名称",
      "category": "类别",
      "trend_signal": "Rising",
      "pain_point": "用户痛点",
      "micro_saas_ideas": ["点子1", "点子2"]
    }
  ]
}
```

## 环境变量配置
```env
# OpenAI API
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# 数据源配置
RSS_FEEDS=https://www.producthunt.com/feed,https://www.futurepedia.io/new
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret

# 调度配置
CRON_SCHEDULE=0 9 * * *
DATA_SOURCE_LIMIT=50
```

---

*所有窗口必须严格按照此契约开发，确保数据格式一致！*