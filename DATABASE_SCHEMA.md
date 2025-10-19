# 数据库结构 — AutoSaaS Radar

## Supabase PostgreSQL 表结构

### 主表：tools
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

-- 索引
CREATE INDEX idx_tools_category ON tools(category);
CREATE INDEX idx_tools_date ON tools(date);
CREATE INDEX idx_tools_trend ON tools(trend_signal);
CREATE INDEX idx_tools_votes ON tools(votes DESC);
```

### 分类表：categories (可选)
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#6366f1',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 初始数据
INSERT INTO categories (name, description, color) VALUES
('Video', '视频编辑、生成相关工具', '#ef4444'),
('Text', '文本处理、写作相关工具', '#10b981'),
('Productivity', '生产力、效率工具', '#f59e0b'),
('Marketing', '营销、推广工具', '#8b5cf6'),
('Education', '教育、学习工具', '#06b6d4'),
('Audio', '音频、音乐相关工具', '#ec4899'),
('Other', '其他类别工具', '#6b7280');
```

### 数据源表：data_sources (用于追踪)
```sql
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    url TEXT,
    type TEXT, -- 'rss', 'api', 'scraper'
    last_fetched TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 初始数据源
INSERT INTO data_sources (name, url, type) VALUES
('ProductHunt', 'https://www.producthunt.com/feed', 'rss'),
('Futurepedia', 'https://www.futurepedia.io/new', 'rss'),
('Reddit r/SaaS', 'https://reddit.com/r/SaaS', 'scraper'),
('Reddit r/SideProject', 'https://reddit.com/r/SideProject', 'scraper'),
('Hacker News', 'https://hacker-news.firebaseio.com/v0', 'api');
```

### 分析日志表：analysis_logs
```sql
CREATE TABLE analysis_logs (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP DEFAULT NOW(),
    tools_analyzed INT,
    tokens_used INT,
    cost_usd DECIMAL(10, 4),
    status TEXT, -- 'success', 'failed', 'partial'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 视图定义

### 最新工具视图
```sql
CREATE VIEW latest_tools AS
SELECT
    t.*,
    c.color as category_color,
    c.description as category_description
FROM tools t
LEFT JOIN categories c ON t.category = c.name
ORDER BY t.date DESC
LIMIT 50;
```

### 趋势统计视图
```sql
CREATE VIEW trend_stats AS
SELECT
    category,
    trend_signal,
    COUNT(*) as count,
    AVG(votes) as avg_votes,
    MAX(date) as latest_date
FROM tools
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY category, trend_signal
ORDER BY count DESC;
```

## RLS (Row Level Security) 策略
```sql
-- 启用 RLS
ALTER TABLE tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_logs ENABLE ROW LEVEL SECURITY;

-- 允许匿名读取（因为是公开数据）
CREATE POLICY "Allow public read access" ON tools
    FOR SELECT USING (true);

-- 允许服务端写入（用于自动更新）
CREATE POLICY "Allow service insert" ON tools
    FOR INSERT WITH CHECK (true);

-- 允许服务端更新
CREATE POLICY "Allow service update" ON tools
    FOR UPDATE USING (true);
```

## 数据保留策略
```sql
-- 自动删除 30 天前的数据（可选）
CREATE OR REPLACE FUNCTION cleanup_old_tools()
RETURNS void AS $$
BEGIN
    DELETE FROM tools
    WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- 创建定时任务（需要 pg_cron 扩展）
-- SELECT cron.schedule('cleanup-old-tools', '0 2 * * *', 'SELECT cleanup_old_tools();');
```

## 查询示例

### 获取今日 Top 5 工具
```sql
SELECT * FROM tools
WHERE DATE(date) = CURRENT_DATE
ORDER BY votes DESC
LIMIT 5;
```

### 按分类获取趋势工具
```sql
SELECT * FROM tools
WHERE category = 'Productivity'
  AND trend_signal = 'Rising'
  AND date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY votes DESC;
```

### 获取 Micro SaaS 点子统计
```sql
SELECT
    category,
    COUNT(*) as total_ideas,
    array_agg(DISTINCT jsonb_array_elements_text(micro_saas_ideas)) as all_ideas
FROM tools
WHERE micro_saas_ideas IS NOT NULL
GROUP BY category;
```

## 备份策略
```sql
-- 导出数据
COPY tools TO 'tools_backup.csv' WITH CSV HEADER;

-- 导入数据
COPY tools FROM 'tools_backup.csv' WITH CSV HEADER;
```

---

*所有数据库操作必须严格遵循此结构设计！*