-- AutoSaaS Radar 数据库表创建脚本
-- 执行顺序: 01_create_tables.sql -> 02_create_indexes.sql -> 03_create_views.sql -> 04_insert_initial_data.sql

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- 1. 主表：tools (工具数据)
-- ============================================
CREATE TABLE IF NOT EXISTS tools (
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
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 添加约束
ALTER TABLE tools ADD CONSTRAINT chk_category
    CHECK (category IN ('Video', 'Text', 'Productivity', 'Marketing', 'Education', 'Audio', 'Other'));

ALTER TABLE tools ADD CONSTRAINT chk_trend_signal
    CHECK (trend_signal IN ('Rising', 'Stable', 'Declining'));

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tools_updated_at
    BEFORE UPDATE ON tools
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 2. 分类表：categories
-- ============================================
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#6366f1',
    icon TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建更新时间触发器
CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 3. 数据源表：data_sources
-- ============================================
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    url TEXT,
    type TEXT, -- 'rss', 'api', 'scraper'
    last_fetched TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    fetch_count INT DEFAULT 0,
    error_count INT DEFAULT 0,
    last_error TEXT,
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 添加约束
ALTER TABLE data_sources ADD CONSTRAINT chk_source_type
    CHECK (type IN ('rss', 'api', 'scraper'));

-- 创建更新时间触发器
CREATE TRIGGER update_data_sources_updated_at
    BEFORE UPDATE ON data_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4. 分析日志表：analysis_logs
-- ============================================
CREATE TABLE IF NOT EXISTS analysis_logs (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP DEFAULT NOW(),
    tools_analyzed INT DEFAULT 0,
    tokens_used INT DEFAULT 0,
    cost_usd DECIMAL(10, 4) DEFAULT 0,
    status TEXT DEFAULT 'success', -- 'success', 'failed', 'partial'
    error_message TEXT,
    processing_time DECIMAL(10, 3), -- 处理时间（秒）
    source_count INT DEFAULT 0, -- 数据源数量
    created_at TIMESTAMP DEFAULT NOW()
);

-- 添加约束
ALTER TABLE analysis_logs ADD CONSTRAINT chk_analysis_status
    CHECK (status IN ('success', 'failed', 'partial'));

-- ============================================
-- 5. 系统配置表：system_settings
-- ============================================
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    data_type TEXT DEFAULT 'string', -- 'string', 'integer', 'boolean', 'json'
    is_public BOOLEAN DEFAULT FALSE, -- 是否可以通过API公开访问
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 添加约束
ALTER TABLE system_settings ADD CONSTRAINT chk_setting_type
    CHECK (data_type IN ('string', 'integer', 'boolean', 'json'));

-- 创建更新时间触发器
CREATE TRIGGER update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. API使用统计表：api_usage_stats
-- ============================================
CREATE TABLE IF NOT EXISTS api_usage_stats (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP DEFAULT NOW(),
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INT NOT NULL,
    response_time DECIMAL(10, 3), -- 响应时间（毫秒）
    user_agent TEXT,
    ip_address INET,
    request_size INT DEFAULT 0,
    response_size INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 添加约束
ALTER TABLE api_usage_stats ADD CONSTRAINT chk_endpoint_length
    CHECK (length(endpoint) <= 255);

ALTER TABLE api_usage_stats ADD CONSTRAINT chk_method
    CHECK (method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH'));

-- ============================================
-- 表创建完成
-- ============================================

-- 创建时间分区函数（用于大数据量表）
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, start_date DATE)
RETURNS void AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    end_date := start_date + interval '1 month';

    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
                    FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE tools IS 'AI工具数据主表，存储从各个数据源抓取并分析后的工具信息';
COMMENT ON TABLE categories IS '工具分类表，定义工具的分类和元数据';
COMMENT ON TABLE data_sources IS '数据源配置表，管理各个数据抓取源';
COMMENT ON TABLE analysis_logs IS '分析日志表，记录GPT分析的执行情况和统计信息';
COMMENT ON TABLE system_settings IS '系统配置表，存储可动态调整的系统参数';
COMMENT ON TABLE api_usage_stats IS 'API使用统计表，用于监控和分析API使用情况';