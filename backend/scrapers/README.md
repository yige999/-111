# RSS 抓取模块 - 窗口2

## 📋 模块概述

这是窗口2开发的RSS抓取模块，专门用于从ProductHunt和Futurepedia等平台抓取最新的AI工具信息。

## 🚀 功能特性

### ✅ 已完成功能

1. **专用抓取器**
   - `ProductHuntScraper` - ProductHunt RSS专用抓取
   - `FuturepediaScraper` - Futurepedia RSS专用抓取

2. **智能数据清洗**
   - 自动HTML标签清理
   - 工具名称标准化
   - 分类自动识别
   - 投票数提取和验证
   - URL标准化和去重

3. **错误处理机制**
   - 网络超时处理
   - 重试机制（指数退避）
   - 异常捕获和日志记录
   - 数据验证

4. **统一管理器**
   - 并行抓取多个RSS源
   - 源状态监控
   - 批量数据处理

## 📁 文件结构

```
backend/scrapers/
├── __init__.py                    # 模块接口
├── producthunt_scraper.py         # ProductHunt专用抓取器
├── futurepedia_scraper.py         # Futurepedia专用抓取器
├── data_cleaner.py                # 数据清洗模块
├── rss_manager.py                 # 统一RSS管理器
├── test_rss.py                    # 测试脚本
└── README.md                      # 本文档
```

## 🛠 使用方法

### 1. 单个源抓取

```python
from scrapers import fetch_producthunt_tools, fetch_futurepedia_tools

# 抓取ProductHunt工具
ph_tools = await fetch_producthunt_tools(limit=50)

# 抓取Futurepedia工具
fp_tools = await fetch_futurepedia_tools(limit=50)
```

### 2. 统一抓取

```python
from scrapers import fetch_ai_tools_from_rss

# 抓取所有支持的RSS源
result = await fetch_ai_tools_from_rss(limit_per_source=50)

print(f"总工具数: {result['total_tools']}")
print(f"清洗后: {result['cleaned_count']}")
```

### 3. 指定源抓取

```python
# 只抓取特定源
result = await fetch_ai_tools_from_rss(
    sources=['producthunt', 'futurepedia'],
    limit_per_source=30
)
```

### 4. 数据清洗

```python
from scrapers import clean_and_validate_tools
from models import RawTool

# 清洗原始数据
cleaned_tools = clean_and_validate_tools(raw_tools)
```

## 📊 数据格式

### RawTool 模型

```python
class RawTool(BaseModel):
    tool_name: str        # 工具名称
    description: str      # 工具描述
    votes: int           # 投票数
    link: str            # 工具链接
    date: datetime       # 发布日期
    category: str        # 工具分类
```

### 抓取结果格式

```python
{
    'success': bool,           # 是否成功
    'total_tools': int,        # 总工具数
    'cleaned_count': int,      # 清洗后工具数
    'sources': dict,           # 各源详细结果
    'cleaned_tools': list,     # 清洗后的工具列表
    'errors': list,           # 错误信息
    'fetch_time': str         # 抓取时间
}
```

## 🔧 配置选项

### RSSManager 配置

- `max_retries`: 最大重试次数（默认3次）
- `timeout`: 超时时间（默认30秒）

### 数据清洗配置

- 工具名称长度限制：100字符
- 描述长度限制：500字符
- 最大投票数限制：10000
- 支持的分类：Video, Text, Productivity, Marketing, Education, Audio, Image, Code

## 🚨 错误处理

模块包含完善的错误处理机制：

1. **网络错误** - 自动重试 + 指数退避
2. **解析错误** - 跳过无效条目 + 记录日志
3. **数据验证** - 过滤无效数据 + 格式标准化
4. **源监控** - 跟踪每个源的状态和成功率

## 🧪 测试

运行测试脚本：

```bash
cd backend
python scrapers/test_rss.py
```

测试包括：
- 单个RSS源抓取测试
- 统一管理器测试
- 数据清洗功能测试
- 错误处理测试

## 📈 性能特性

- **并行抓取**: 多个RSS源同时抓取
- **内存优化**: 流式处理大数据集
- **缓存机制**: 避免重复抓取
- **限流控制**: 尊重RSS源的限制

## 🔄 API 兼容性

本模块遵循项目的 `API_CONTRACT.md` 规范：

- 数据格式统一
- 错误处理标准化
- 接口文档完整
- 向后兼容

## 🎯 窗口2状态

**开发状态**: ✅ 完成
**测试状态**: ✅ 通过
**文档状态**: ✅ 完整
**交付状态**: ✅ 已交付

## 📞 联系方式

如有问题或建议，请在项目Issues中记录。

---

*窗口2: RSS 抓取模块 - 2024-01-15 完成*