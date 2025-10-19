-- AutoSaaS Radar 数据库索引创建脚本
-- 执行顺序: 01_create_tables.sql -> 02_create_indexes.sql -> 03_create_views.sql -> 04_insert_initial_data.sql

-- ============================================
-- tools 表索引
-- ============================================

-- 主键索引（通常自动创建，但显式声明更清晰）
CREATE INDEX IF NOT EXISTS idx_tools_id ON tools(id);

-- 分类索引（用于按分类查询）
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category);

-- 日期索引（用于按时间范围查询）
CREATE INDEX IF NOT EXISTS idx_tools_date ON tools(date);

-- 趋势信号索引（用于按趋势筛选）
CREATE INDEX IF NOT EXISTS idx_tools_trend_signal ON tools(trend_signal);

-- 投票数索引（用于排序和热门工具查询）
CREATE INDEX IF NOT EXISTS idx_tools_votes ON tools(votes DESC);

-- 工具名称索引（用于搜索）
CREATE INDEX IF NOT EXISTS idx_tools_tool_name ON tools(tool_name);

-- 复合索引：分类+日期（用于特定分类的时间范围查询）
CREATE INDEX IF NOT EXISTS idx_tools_category_date ON tools(category, date DESC);

-- 复合索引：趋势+投票数（用于趋势工具排序）
CREATE INDEX IF NOT EXISTS idx_tools_trend_votes ON tools(trend_signal, votes DESC);

-- 复合索引：日期+投票数（用于最新热门工具）
CREATE INDEX IF NOT EXISTS idx_tools_date_votes ON tools(date DESC, votes DESC);

-- JSONB索引：用于搜索 micro_saas_ideas
CREATE INDEX IF NOT EXISTS idx_tools_saas_ideas_gin ON tools USING gin(micro_saas_ideas);

-- 部分索引：只为有痛点的记录创建索引
CREATE INDEX IF NOT EXISTS idx_tools_pain_point ON tools(pain_point) WHERE pain_point IS NOT NULL;

-- ============================================
-- categories 表索引
-- ============================================

-- 唯一索引（name字段已有唯一约束，但创建索引可以提高查询性能）
CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_name ON categories(name);

-- ============================================
-- data_sources 表索引
-- ============================================

-- 类型索引（用于按类型筛选数据源）
CREATE INDEX IF NOT EXISTS idx_data_sources_type ON data_sources(type);

-- 活跃状态索引（用于筛选活跃数据源）
CREATE INDEX IF NOT EXISTS idx_data_sources_is_active ON data_sources(is_active);

-- 最后抓取时间索引（用于检查需要更新的数据源）
CREATE INDEX IF NOT EXISTS idx_data_sources_last_fetched ON data_sources(last_fetched);

-- ============================================
-- analysis_logs 表索引
-- ============================================

-- 日期索引（用于按时间范围查询分析日志）
CREATE INDEX IF NOT EXISTS idx_analysis_logs_date ON analysis_logs(date);

-- 状态索引（用于按状态筛选）
CREATE INDEX IF NOT EXISTS idx_analysis_logs_status ON analysis_logs(status);

-- 复合索引：日期+状态（用于特定时间范围的状态统计）
CREATE INDEX IF NOT EXISTS idx_analysis_logs_date_status ON analysis_logs(date, status);

-- ============================================
-- system_settings 表索引
-- ============================================

-- 唯一索引（key字段已有唯一约束）
CREATE UNIQUE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);

-- 公开状态索引（用于筛选公开的配置项）
CREATE INDEX IF NOT EXISTS idx_system_settings_is_public ON system_settings(is_public);

-- ============================================
-- api_usage_stats 表索引
-- ============================================

-- 日期索引（用于按时间范围统计）
CREATE INDEX IF NOT EXISTS idx_api_usage_stats_date ON api_usage_stats(date);

-- 端点索引（用于按API端点统计）
CREATE INDEX IF NOT EXISTS idx_api_usage_stats_endpoint ON api_usage_stats(endpoint);

-- 状态码索引（用于按响应状态码统计）
CREATE INDEX IF NOT EXISTS idx_api_usage_stats_status_code ON api_usage_stats(status_code);

-- 复合索引：日期+端点（用于特定端点的时间范围统计）
CREATE INDEX IF NOT EXISTS idx_api_usage_stats_date_endpoint ON api_usage_stats(date, endpoint);

-- 响应时间索引（用于性能分析）
CREATE INDEX IF NOT EXISTS idx_api_usage_stats_response_time ON api_usage_stats(response_time);

-- ============================================
-- 创建统计信息更新函数
-- ============================================

-- 更新表统计信息
CREATE OR REPLACE FUNCTION update_table_statistics()
RETURNS void AS $$
BEGIN
    -- 更新主要表的统计信息
    ANALYZE tools;
    ANALYZE categories;
    ANALYZE data_sources;
    ANALYZE analysis_logs;
    ANALYZE system_settings;
    ANALYZE api_usage_stats;
END;
$$ LANGUAGE plpgsql;

-- 创建定期更新统计信息的计划任务（需要 pg_cron 扩展）
-- SELECT cron.schedule('update-statistics', '0 */6 * * *', 'SELECT update_table_statistics();');

-- ============================================
-- 索引创建完成
-- ============================================

-- 创建索引使用情况监控视图
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

COMMENT ON VIEW index_usage_stats IS '索引使用统计视图，用于监控索引的使用情况';

-- 创建未使用索引的监控视图
CREATE OR REPLACE VIEW unused_indexes AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexname NOT LIKE '%_pkey'
ORDER BY schemaname, tablename, indexname;

COMMENT ON VIEW unused_indexes IS '未使用索引监控视图，用于识别可能不需要的索引';