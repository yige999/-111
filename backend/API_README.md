# AutoSaaS Radar API 文档

## 🚀 快速开始

### 启动服务
```bash
cd backend
pip install -r requirements.txt
python main.py
```

服务将在 `http://localhost:8000` 启动

### API文档
启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 测试API
```bash
python test_api.py
```

## 📚 API接口

### 基础信息
- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **认证**: 无需认证（公开数据）

### 健康检查接口

#### 简单健康检查
```http
GET /api/health/simple
```
**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "service": "AutoSaaS Radar API"
}
```

#### 完整健康检查
```http
GET /api/health
```
**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "service": "AutoSaaS Radar API",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "message": "数据库连接正常",
      "last_check": "2024-01-15T10:00:00Z",
      "response_time_ms": 15.2
    }
  }
}
```

#### 就绪检查
```http
GET /api/ready
```

#### 存活检查
```http
GET /api/live
```

#### 版本信息
```http
GET /api/version
```

### 工具数据接口

#### 获取最新工具
```http
GET /api/tools/latest?limit=10&offset=0
```
**参数:**
- `limit` (可选): 返回数量限制，默认10，最大100
- `offset` (可选): 偏移量，默认0

**响应示例:**
```json
[
  {
    "id": 1,
    "tool_name": "AI Resume Optimizer",
    "description": "Optimize resumes for ATS systems",
    "category": "Productivity",
    "votes": 120,
    "link": "https://producthunt.com/posts/ai-resume-optimizer",
    "trend_signal": "Rising",
    "pain_point": "ATS系统识别不准确",
    "micro_saas_ideas": ["Resume Parser", "Job Matcher"],
    "date": "2024-01-15T09:00:00Z",
    "created_at": "2024-01-15T09:15:00Z"
  }
]
```

#### 按分类获取工具
```http
GET /api/tools/category/{category}?limit=20&days=30
```
**参数:**
- `category`: 分类名称 (Video, Text, Productivity, Marketing, Education, Audio, Other)
- `limit` (可选): 返回数量限制，默认20
- `days` (可选): 统计天数，默认30，最大365

#### 获取趋势工具
```http
GET /api/tools/trending?days=7&category=Productivity&min_votes=10&limit=20
```
**参数:**
- `days` (可选): 统计天数，默认7，最大30
- `category` (可选): 筛选分类
- `min_votes` (可选): 最小投票数，默认10
- `limit` (可选): 返回数量限制，默认20

#### 按日期获取工具
```http
GET /api/tools/date/{date}
```
**参数:**
- `date`: 日期格式 YYYY-MM-DD

#### 搜索工具
```http
GET /api/tools/search?query=AI&category=Productivity&limit=20
```
**参数:**
- `query`: 搜索关键词 (必需)
- `category` (可选): 筛选分类
- `limit` (可选): 返回数量限制，默认20

#### 手动刷新数据
```http
POST /api/tools/refresh?force=false
```
**参数:**
- `force` (可选): 强制刷新，忽略时间限制

**响应示例:**
```json
{
  "success": true,
  "message": "数据刷新任务已启动，正在后台执行"
}
```

#### 获取统计信息
```http
GET /api/tools/stats?days=7
```
**参数:**
- `days`: 统计天数，默认7，最大30

**响应示例:**
```json
{
  "total_tools": 150,
  "total_votes": 2500,
  "average_votes": 16.7,
  "category_stats": {
    "Productivity": {
      "count": 45,
      "total_votes": 800,
      "trends": {"Rising": 20, "Stable": 15, "Declining": 10}
    }
  },
  "trend_stats": {"Rising": 60, "Stable": 70, "Declining": 20},
  "period_start": "2024-01-08T00:00:00Z",
  "period_end": "2024-01-15T10:00:00Z"
}
```

## 🏷️ 数据分类

### 工具分类 (Category)
- `Video`: 视频编辑、生成相关工具
- `Text`: 文本处理、写作相关工具
- `Productivity`: 生产力、效率工具
- `Marketing`: 营销、推广工具
- `Education`: 教育、学习工具
- `Audio`: 音频、音乐相关工具
- `Other`: 其他类别工具

### 趋势信号 (Trend Signal)
- `Rising`: 上升趋势
- `Stable`: 稳定
- `Declining`: 下降趋势

## 🚨 错误处理

### 标准错误响应格式
```json
{
  "error": "错误类型",
  "message": "错误描述",
  "details": {},
  "timestamp": "2024-01-15T10:00:00Z",
  "path": "/api/tools/latest"
}
```

### 常见错误码
- `400`: 请求参数错误
- `404`: 资源不存在
- `422`: 请求参数验证失败
- `429`: 请求过于频繁
- `500`: 服务器内部错误

## 🔧 开发说明

### 中间件
- **请求日志**: 记录所有API请求和响应
- **安全头**: 添加安全相关HTTP头
- **速率限制**: 每分钟100次请求限制

### 依赖注入
使用FastAPI的依赖注入系统管理:
- 数据库连接
- 数据收集器
- GPT分析器

### 响应头
- `X-Request-ID`: 请求唯一标识
- `X-Process-Time`: 请求处理时间（毫秒）

## 🧪 测试

### 运行测试
```bash
python test_api.py
```

### 测试覆盖
- 基础连通性测试
- 健康检查接口
- 所有工具数据接口
- 错误处理测试

## 📝 更新日志

### v1.0.0 (2024-01-15)
- ✅ 初始版本发布
- ✅ 完整的工具数据API
- ✅ 健康检查和监控接口
- ✅ 搜索和筛选功能
- ✅ 统计和分析接口
- ✅ 错误处理和日志系统
- ✅ 安全中间件和速率限制