-- AutoSaaS Radar 数据库视图创建脚本
-- 执行顺序: 01_create_tables.sql -> 02_create_indexes.sql -> 03_create_views.sql -> 04_insert_initial_data.sql

-- ============================================
-- 1. 最新工具视图
-- ============================================
CREATE OR REPLACE VIEW latest_tools AS
SELECT
    t.*,
    c.color as category_color,
    c.description as category_description,
    c.icon as category_icon
FROM tools t
LEFT JOIN categories c ON t.category = c.name
ORDER BY t.date DESC, t.votes DESC;

COMMENT ON VIEW latest_tools IS '最新工具视图，包含分类信息和颜色';

-- ============================================
-- 2. 热门工具视图
-- ============================================
CREATE OR REPLACE VIEW popular_tools AS
SELECT
    t.*,
    c.color as category_color,
    c.description as category_description,
    c.icon as category_icon,
    -- 计算热度分数
    (t.votes *
        CASE
            WHEN t.trend_signal = 'Rising' THEN 1.5
            WHEN t.trend_signal = 'Stable' THEN 1.0
            WHEN t.trend_signal = 'Declining' THEN 0.5
            ELSE 1.0
        END
    ) as popularity_score
FROM tools t
LEFT JOIN categories c ON t.category = c.name
WHERE t.date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY popularity_score DESC, t.votes DESC;

COMMENT ON VIEW popular_tools IS '热门工具视图，按热度分数排序';

-- ============================================
-- 3. 趋势统计视图
-- ============================================
CREATE OR REPLACE VIEW trend_stats AS
SELECT
    t.category,
    t.trend_signal,
    COUNT(*) as count,
    AVG(t.votes) as avg_votes,
    MAX(t.votes) as max_votes,
    MIN(t.votes) as min_votes,
    MAX(t.date) as latest_date,
    MIN(t.date) as earliest_date,
    c.color as category_color
FROM tools t
LEFT JOIN categories c ON t.category = c.name
WHERE t.date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY t.category, t.trend_signal, c.color
ORDER BY count DESC, avg_votes DESC;

COMMENT ON VIEW trend_stats IS '趋势统计视图，显示最近7天各分类的趋势分布';

-- ============================================
-- 4. 分类汇总视图
-- ============================================
CREATE OR REPLACE VIEW category_summary AS
SELECT
    c.name as category,
    c.description,
    c.color,
    c.icon,
    COUNT(t.id) as total_tools,
    COUNT(CASE WHEN t.date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_tools,
    COUNT(CASE WHEN t.trend_signal = 'Rising' THEN 1 END) as rising_tools,
    COUNT(CASE WHEN t.trend_signal = 'Stable' THEN 1 END) as stable_tools,
    COUNT(CASE WHEN t.trend_signal = 'Declining' THEN 1 END) as declining_tools,
    AVG(t.votes) as avg_votes,
    MAX(t.votes) as max_votes,
    MAX(t.date) as latest_tool_date,
    -- 计算增长率（最近7天 vs 之前7天）
    (
        SELECT COUNT(*)
        FROM tools t2
        WHERE t2.category = c.name
        AND t2.date >= CURRENT_DATE - INTERVAL '7 days'
    ) - (
        SELECT COUNT(*)
        FROM tools t3
        WHERE t3.category = c.name
        AND t3.date >= CURRENT_DATE - INTERVAL '14 days'
        AND t3.date < CURRENT_DATE - INTERVAL '7 days'
    ) as growth_change
FROM categories c
LEFT JOIN tools t ON c.name = t.category
GROUP BY c.id, c.name, c.description, c.color, c.icon
ORDER BY total_tools DESC;

COMMENT ON VIEW category_summary IS '分类汇总视图，包含各分类的详细统计信息';

-- ============================================
-- 5. 每日统计视图
-- ============================================
CREATE OR REPLACE VIEW daily_stats AS
SELECT
    DATE(t.date) as date,
    COUNT(*) as total_tools,
    COUNT(DISTINCT t.category) as categories_count,
    SUM(t.votes) as total_votes,
    AVG(t.votes) as avg_votes,
    COUNT(CASE WHEN t.trend_signal = 'Rising' THEN 1 END) as rising_count,
    COUNT(CASE WHEN t.trend_signal = 'Stable' THEN 1 END) as stable_count,
    COUNT(CASE WHEN t.trend_signal = 'Declining' THEN 1 END) as declining_count,
    -- 计算当天的热门分类
    (
        SELECT t2.category
        FROM tools t2
        WHERE DATE(t2.date) = DATE(t.date)
        GROUP BY t2.category
        ORDER BY COUNT(*) DESC, SUM(t2.votes) DESC
        LIMIT 1
    ) as top_category
FROM tools t
GROUP BY DATE(t.date)
ORDER BY date DESC;

COMMENT ON VIEW daily_stats IS '每日统计视图，显示每天的工具收集情况';

-- ============================================
-- 6. Micro SaaS 点子汇总视图
-- ============================================
CREATE OR REPLACE VIEW saas_ideas_summary AS
SELECT
    t.category,
    c.color,
    COUNT(*) as total_tools_with_ideas,
    COUNT(DISTINCT jsonb_array_elements_text(t.micro_saas_ideas)) as unique_ideas,
    array_agg(DISTINCT jsonb_array_elements_text(t.micro_saas_ideas)) as all_ideas,
    -- 统计最常见的点子
    (
        SELECT idea
        FROM (
            SELECT
                jsonb_array_elements_text(t2.micro_saas_ideas) as idea,
                COUNT(*) as count
            FROM tools t2
            WHERE t2.category = t.category
            AND t2.micro_saas_ideas IS NOT NULL
            GROUP BY jsonb_array_elements_text(t2.micro_saas_ideas)
            ORDER BY count DESC
            LIMIT 5
        ) top_ideas
    ) as top_ideas
FROM tools t
LEFT JOIN categories c ON t.category = c.name
WHERE t.micro_saas_ideas IS NOT NULL
  AND jsonb_array_length(t.micro_saas_ideas) > 0
GROUP BY t.category, c.color
ORDER BY unique_ideas DESC;

COMMENT ON VIEW saas_ideas_summary IS 'Micro SaaS点子汇总视图，统计各分类的点子情况';

-- ============================================
-- 7. 痛点汇总视图
-- ============================================
CREATE OR REPLACE VIEW pain_points_summary AS
SELECT
    t.category,
    c.color,
    COUNT(*) as total_tools_with_pain_points,
    COUNT(DISTINCT t.pain_point) as unique_pain_points,
    array_agg(DISTINCT t.pain_point) as all_pain_points,
    -- 最常见的痛点
    (
        SELECT pain_point
        FROM (
            SELECT
                t2.pain_point,
                COUNT(*) as count
            FROM tools t2
            WHERE t2.category = t.category
            AND t2.pain_point IS NOT NULL
            GROUP BY t2.pain_point
            ORDER BY count DESC
            LIMIT 5
        ) top_pain_points
    ) as top_pain_points
FROM tools t
LEFT JOIN categories c ON t.category = c.name
WHERE t.pain_point IS NOT NULL
  AND t.pain_point != ''
GROUP BY t.category, c.color
ORDER BY unique_pain_points DESC;

COMMENT ON VIEW pain_points_summary IS '用户痛点汇总视图，统计各分类的痛点情况';

-- ============================================
-- 8. 数据源状态视图
-- ============================================
CREATE OR REPLACE VIEW data_source_status AS
SELECT
    ds.*,
    -- 计算成功率
    CASE
        WHEN ds.fetch_count > 0 THEN
            ROUND((ds.fetch_count - ds.error_count)::numeric / ds.fetch_count * 100, 2)
        ELSE 0
    END as success_rate,
    -- 计算距离上次抓取的时间
    EXTRACT(EPOCH FROM (NOW() - ds.last_fetched)) / 3600 as hours_since_last_fetch,
    -- 判断是否需要更新
    CASE
        WHEN ds.last_fetched IS NULL THEN true
        WHEN EXTRACT(EPOCH FROM (NOW() - ds.last_fetched)) / 3600 > 24 THEN true
        ELSE false
    END as needs_update
FROM data_sources ds
WHERE ds.is_active = true
ORDER BY success_rate DESC, last_fetched DESC;

COMMENT ON VIEW data_source_status IS '数据源状态视图，显示各数据源的运行状态';

-- ============================================
-- 9. 系统概览视图
-- ============================================
CREATE OR REPLACE VIEW system_overview AS
SELECT
    -- 工具统计
    (SELECT COUNT(*) FROM tools) as total_tools,
    (SELECT COUNT(*) FROM tools WHERE DATE(date) = CURRENT_DATE) as today_tools,
    (SELECT COUNT(*) FROM tools WHERE date >= CURRENT_DATE - INTERVAL '7 days') as week_tools,

    -- 分类统计
    (SELECT COUNT(*) FROM categories) as total_categories,
    (SELECT COUNT(DISTINCT category) FROM tools WHERE category IS NOT NULL) as active_categories,

    -- 最新分析统计
    (SELECT COUNT(*) FROM analysis_logs WHERE DATE(date) = CURRENT_DATE) as today_analysis_runs,
    (SELECT SUM(tools_analyzed) FROM analysis_logs WHERE DATE(date) = CURRENT_DATE) as today_tools_analyzed,

    -- 数据源状态
    (SELECT COUNT(*) FROM data_sources WHERE is_active = true) as active_data_sources,
    (SELECT COUNT(*) FROM data_sources WHERE needs_update = true) as data_sources_need_update,

    -- 系统状态
    (SELECT value FROM system_settings WHERE key = 'system_status') as system_status,
    (SELECT value FROM system_settings WHERE key = 'last_data_update') as last_data_update,

    NOW() as current_time;

COMMENT ON VIEW system_overview IS '系统概览视图，显示整体运行状态和关键指标';

-- ============================================
-- 视图创建完成
-- ============================================

-- 创建视图刷新函数（用于物化视图，如果需要的话）
CREATE OR REPLACE FUNCTION refresh_views()
RETURNS void AS $$
BEGIN
    -- 这里可以添加物化视图的刷新逻辑
    -- 目前使用普通视图，不需要刷新

    -- 更新统计信息
    PERFORM update_table_statistics();
END;
$$ LANGUAGE plpgsql;