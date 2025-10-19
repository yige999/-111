-- AutoSaaS Radar 初始数据插入脚本
-- 执行顺序: 01_create_tables.sql -> 02_create_indexes.sql -> 03_create_views.sql -> 04_insert_initial_data.sql

-- ============================================
-- 1. 插入分类数据
-- ============================================
INSERT INTO categories (name, description, color, icon) VALUES
('Video', '视频编辑、生成、处理相关AI工具', '#ef4444', 'video'),
('Text', '文本生成、写作、翻译相关AI工具', '#10b981', 'document'),
('Productivity', '生产力、效率、自动化AI工具', '#f59e0b', 'zap'),
('Marketing', '营销、推广、销售相关AI工具', '#8b5cf6', 'megaphone'),
('Education', '教育、学习、培训相关AI工具', '#06b6d4', 'academic-cap'),
('Audio', '音频生成、编辑、处理相关AI工具', '#ec4899', 'music-note'),
('Other', '其他类别AI工具', '#6b7280', 'cube')
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 2. 插入数据源配置
-- ============================================
INSERT INTO data_sources (name, url, type, config, is_active) VALUES
('ProductHunt', 'https://www.producthunt.com/feed', 'rss',
 '{"update_frequency": "hourly", "limit": 50, "headers": {"User-Agent": "AutoSaaS-Radar/1.0"}}',
 true),
('Futurepedia', 'https://www.futurepedia.io/feed', 'rss',
 '{"update_frequency": "hourly", "limit": 30, "headers": {"User-Agent": "AutoSaaS-Radar/1.0"}}',
 true),
('Hacker News', 'https://hacker-news.firebaseio.com/v0', 'api',
 '{"update_frequency": "hourly", "limit": 20, "api_version": "v0"}',
 true),
('Reddit r/SaaS', 'https://www.reddit.com/r/SaaS', 'scraper',
 '{"update_frequency": "6hours", "limit": 25, "subreddit": "SaaS"}',
 false),
('Reddit r/SideProject', 'https://www.reddit.com/r/SideProject', 'scraper',
 '{"update_frequency": "6hours", "limit": 25, "subreddit": "SideProject"}',
 false)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 3. 插入系统配置
-- ============================================
INSERT INTO system_settings (key, value, description, data_type, is_public) VALUES
-- 系统基础配置
('system_status', 'running', '系统运行状态', 'string', true),
('system_version', '1.0.0', '系统版本号', 'string', true),
('last_data_update', NULL, '最后数据更新时间', 'timestamp', true),

-- 数据收集配置
('data_collection_enabled', 'true', '是否启用数据收集', 'boolean', false),
('data_source_limit', '50', '每个数据源的抓取限制', 'integer', false),
('collection_interval_hours', '1', '数据收集间隔（小时）', 'integer', false),

-- GPT分析配置
('gpt_analysis_enabled', 'true', '是否启用GPT分析', 'boolean', false),
('gpt_model', 'gpt-4o', 'GPT模型名称', 'string', false),
('analysis_batch_size', '10', '分析批次大小', 'integer', false),
('max_tokens_per_request', '4000', '每次请求的最大token数', 'integer', false),

-- 缓存配置
('cache_ttl_seconds', '3600', '缓存过期时间（秒）', 'integer', false),
('enable_redis_cache', 'false', '是否启用Redis缓存', 'boolean', false),

-- 通知配置
('notification_enabled', 'false', '是否启用通知', 'boolean', false),
('notification_email', NULL, '通知邮箱', 'string', false),
('notification_webhook', NULL, '通知webhook地址', 'string', false),

-- 数据保留配置
('data_retention_days', '30', '数据保留天数', 'integer', false),
('enable_auto_cleanup', 'false', '是否启用自动清理', 'boolean', false),

-- API限制配置
('api_rate_limit_per_minute', '100', 'API每分钟请求限制', 'integer', false),
('enable_api_logging', 'true', '是否启用API日志', 'boolean', false),

-- 前端显示配置
('default_page_size', '20', '默认分页大小', 'integer', true),
('max_page_size', '100', '最大分页大小', 'integer', true),
('enable_trending_calculations', 'true', '是否启用趋势计算', 'boolean', false),

-- 开发配置
('debug_mode', 'false', '调试模式', 'boolean', false),
('log_level', 'INFO', '日志级别', 'string', false)
ON CONFLICT (key) DO NOTHING;

-- ============================================
-- 4. 插入示例数据（可选，用于测试）
-- ============================================
INSERT INTO tools (
    tool_name, description, category, votes, link, trend_signal, pain_point, micro_saas_ideas, date
) VALUES
('AI Resume Builder', '使用AI技术自动生成专业简历，支持多种模板和行业定制', 'Productivity', 156,
 'https://example.com/ai-resume-builder', 'Rising',
 '求职者花费大量时间制作简历，难以针对不同职位进行优化',
 '["Resume Tailor Assistant", "Job Description Analyzer", "LinkedIn Profile Optimizer"]',
 NOW() - INTERVAL '2 hours'),

('Video Summarizer', '自动分析长视频内容，生成关键信息摘要和时间戳', 'Video', 89,
 'https://example.com/video-summarizer', 'Rising',
 '用户需要快速了解长视频内容，但没有时间观看完整视频',
 '["Meeting Recorder", "Educational Video Summarizer", "Content Repurposing Tool"]',
 NOW() - INTERVAL '4 hours'),

('Social Media Post Generator', '基于产品信息和目标受众，自动生成社交媒体营销文案', 'Marketing', 134,
 'https://example.com/social-post-generator', 'Stable',
 '营销人员缺乏时间创作多样化的社交媒体内容，难以保持更新频率',
 '["Content Calendar Assistant", "Brand Voice Analyzer", "Multi-Platform Publisher"]',
 NOW() - INTERVAL '6 hours'),

('Code Documentation Helper', '自动读取代码并生成详细的技术文档和API说明', 'Productivity', 67,
 'https://example.com/code-doc-helper', 'Rising',
 '开发者讨厌写文档，项目文档经常过时或不完整',
 '["API Reference Generator", "Code Review Assistant", "Tutorial Creator"]',
 NOW() - INTERVAL '8 hours'),

('Language Learning Tutor', '个性化的AI语言学习助手，提供实时对话和语法纠正', 'Education', 201,
 'https://example.com/language-tutor', 'Stable',
 '语言学习者缺乏练习机会，传统学习方式成本高且时间不灵活',
 '["Business English Coach", "Pronunciation Analyzer", "Vocabulary Builder"]',
 NOW() - INTERVAL '1 day'),

('Podcast Audio Enhancer', '自动优化播客音频质量，去除背景噪音和平衡音量', 'Audio', 45,
 'https://example.com/podcast-enhancer', 'Stable',
 '播客制作者缺乏专业音频编辑技能，后期处理耗时且复杂',
 '["Voice Isolation Tool", "Background Music Remover", "Audio Level Normalizer"]',
 NOW() - INTERVAL '1 day'),

('Email Marketing Analyzer', '分析邮件营销活动效果，提供优化建议和A/B测试方案', 'Marketing', 78,
 'https://example.com/email-analyzer', 'Declining',
 '营销人员难以准确衡量邮件活动效果，优化决策缺乏数据支持',
 '["Subject Line Tester", "Send Time Optimizer", "Engagement Predictor"]',
 NOW() - INTERVAL '2 days')
ON CONFLICT DO NOTHING;

-- ============================================
-- 5. 插入示例分析日志
-- ============================================
INSERT INTO analysis_logs (
    tools_analyzed, tokens_used, cost_usd, status, processing_time, source_count
) VALUES
(7, 2450, 0.0245, 'success', 12.5, 3),
(5, 1850, 0.0185, 'success', 9.8, 2),
(8, 3100, 0.0310, 'success', 15.2, 3)
ON CONFLICT DO NOTHING;

-- ============================================
-- 6. 创建示例API使用统计
-- ============================================
INSERT INTO api_usage_stats (
    endpoint, method, status_code, response_time, user_agent, request_size, response_size
) VALUES
('/api/tools/latest', 'GET', 200, 45.2, 'Mozilla/5.0', 0, 2048),
('/api/tools/category/Productivity', 'GET', 200, 67.8, 'Mozilla/5.0', 0, 1536),
('/api/tools/trending', 'GET', 200, 52.1, 'Mozilla/5.0', 0, 3072),
('/api/stats', 'GET', 200, 23.4, 'Mozilla/5.0', 0, 1024)
ON CONFLICT DO NOTHING;

-- ============================================
-- 7. 设置初始数据更新时间
-- ============================================
UPDATE system_settings
SET value = NOW()
WHERE key = 'last_data_update'
AND value IS NULL;

-- ============================================
-- 数据插入完成
-- ============================================

-- 创建数据验证函数
CREATE OR REPLACE FUNCTION validate_initial_data()
RETURNS TABLE(
    table_name TEXT,
    record_count BIGINT,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'categories'::TEXT, COUNT(*)::BIGINT,
           CASE WHEN COUNT(*) >= 7 THEN 'OK' ELSE 'WARNING' END::TEXT
    FROM categories

    UNION ALL

    SELECT 'data_sources'::TEXT, COUNT(*)::BIGINT,
           CASE WHEN COUNT(*) >= 3 THEN 'OK' ELSE 'WARNING' END::TEXT
    FROM data_sources

    UNION ALL

    SELECT 'system_settings'::TEXT, COUNT(*)::BIGINT,
           CASE WHEN COUNT(*) >= 15 THEN 'OK' ELSE 'WARNING' END::TEXT
    FROM system_settings

    UNION ALL

    SELECT 'tools'::TEXT, COUNT(*)::BIGINT,
           CASE WHEN COUNT(*) >= 5 THEN 'OK' ELSE 'WARNING' END::TEXT
    FROM tools;
END;
$$ LANGUAGE plpgsql;

-- 运行数据验证
-- SELECT * FROM validate_initial_data();

COMMENT ON FUNCTION validate_initial_data() IS '验证初始数据是否正确插入的函数';