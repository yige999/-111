-- AutoSaaS Radar RLS (行级安全策略) 设置脚本
-- 执行顺序: 04_insert_initial_data.sql -> 05_setup_rls.sql

-- ============================================
-- 1. 启用 RLS
-- ============================================

-- 为主要表启用行级安全
ALTER TABLE tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage_stats ENABLE ROW LEVEL SECURITY;

-- 注意：categories, data_sources, system_settings 表通常不需要RLS
-- 因为它们是系统配置表，需要公开访问

-- ============================================
-- 2. 创建 RLS 策略 - tools 表
-- ============================================

-- 允许所有人读取工具数据（公开数据）
DROP POLICY IF EXISTS "Allow public read access to tools" ON tools;
CREATE POLICY "Allow public read access to tools"
    ON tools FOR SELECT
    USING (true);

-- 允许服务端插入工具数据
DROP POLICY IF EXISTS "Allow service insert to tools" ON tools;
CREATE POLICY "Allow service insert to tools"
    ON tools FOR INSERT
    WITH CHECK (true);

-- 允许服务端更新工具数据
DROP POLICY IF EXISTS "Allow service update to tools" ON tools;
CREATE POLICY "Allow service update to tools"
    ON tools FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- （可选）允许服务端删除工具数据
DROP POLICY IF EXISTS "Allow service delete to tools" ON tools;
CREATE POLICY "Allow service delete to tools"
    ON tools FOR DELETE
    USING (true);

-- ============================================
-- 3. 创建 RLS 策略 - analysis_logs 表
-- ============================================

-- 允许认证用户读取分析日志
DROP POLICY IF EXISTS "Allow authenticated read access to analysis_logs" ON analysis_logs;
CREATE POLICY "Allow authenticated read access to analysis_logs"
    ON analysis_logs FOR SELECT
    USING (
        auth.role() = 'authenticated'
        OR auth.role() = 'service_role'
    );

-- 允许服务端插入分析日志
DROP POLICY IF EXISTS "Allow service insert to analysis_logs" ON analysis_logs;
CREATE POLICY "Allow service insert to analysis_logs"
    ON analysis_logs FOR INSERT
    WITH CHECK (true);

-- 允许服务端更新分析日志
DROP POLICY IF EXISTS "Allow service update to analysis_logs" ON analysis_logs;
CREATE POLICY "Allow service update to analysis_logs"
    ON analysis_logs FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- ============================================
-- 4. 创建 RLS 策略 - api_usage_stats 表
-- ============================================

-- 允许认证用户读取API统计（管理员功能）
DROP POLICY IF EXISTS "Allow authenticated read access to api_usage_stats" ON api_usage_stats;
CREATE POLICY "Allow authenticated read access to api_usage_stats"
    ON api_usage_stats FOR SELECT
    USING (
        auth.role() = 'authenticated'
        OR auth.role() = 'service_role'
    );

-- 允许匿名插入API统计数据（用于日志记录）
DROP POLICY IF EXISTS "Allow anonymous insert to api_usage_stats" ON api_usage_stats;
CREATE POLICY "Allow anonymous insert to api_usage_stats"
    ON api_usage_stats FOR INSERT
    WITH CHECK (true);

-- ============================================
-- 5. 创建自定义函数用于访问控制
-- ============================================

-- 检查用户是否为管理员
CREATE OR REPLACE FUNCTION is_admin()
RETURNS boolean AS $$
BEGIN
    RETURN auth.role() = 'service_role' OR auth.role() = 'authenticated';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 检查是否为内部服务请求
CREATE OR REPLACE FUNCTION is_service_request()
RETURNS boolean AS $$
BEGIN
    RETURN auth.role() = 'service_role';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 获取当前用户ID（如果有）
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS uuid AS $$
BEGIN
    RETURN auth.uid();
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 6. 创建数据访问审计日志
-- ============================================

-- 创建访问日志表
CREATE TABLE IF NOT EXISTS access_logs (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL, -- 'SELECT', 'INSERT', 'UPDATE', 'DELETE'
    user_id uuid,
    user_role TEXT,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    record_id TEXT,
    additional_info JSONB
);

-- 创建访问日志触发器函数
CREATE OR REPLACE FUNCTION log_data_access()
RETURNS TRIGGER AS $$
DECLARE
    user_uuid uuid;
    user_role_text TEXT;
BEGIN
    -- 获取用户信息
    user_uuid := get_current_user_id();
    user_role_text := auth.role();

    -- 记录访问日志
    INSERT INTO access_logs (
        table_name,
        operation,
        user_id,
        user_role,
        ip_address,
        record_id,
        additional_info
    ) VALUES (
        TG_TABLE_NAME,
        TG_OP,
        user_uuid,
        user_role_text,
        inet_client_addr(),
        CASE
            WHEN TG_OP = 'INSERT' THEN NEW.id::TEXT
            WHEN TG_OP = 'UPDATE' THEN NEW.id::TEXT
            WHEN TG_OP = 'DELETE' THEN OLD.id::TEXT
            ELSE NULL
        END,
        CASE
            WHEN TG_OP = 'INSERT' THEN jsonb_build_object('new_data', row_to_json(NEW))
            WHEN TG_OP = 'UPDATE' THEN jsonb_build_object('old_data', row_to_json(OLD), 'new_data', row_to_json(NEW))
            WHEN TG_OP = 'DELETE' THEN jsonb_build_object('old_data', row_to_json(OLD))
            ELSE NULL
        END
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 为敏感表创建审计触发器
-- 注意：tools表数据量大，可能不需要完整审计
-- analysis_logs表审计
DROP TRIGGER IF EXISTS audit_analysis_logs ON analysis_logs;
CREATE TRIGGER audit_analysis_logs
    AFTER INSERT OR UPDATE OR DELETE ON analysis_logs
    FOR EACH ROW EXECUTE FUNCTION log_data_access();

-- api_usage_stats表审计
DROP TRIGGER IF EXISTS audit_api_usage_stats ON api_usage_stats;
CREATE TRIGGER audit_api_usage_stats
    AFTER INSERT OR UPDATE OR DELETE ON api_usage_stats
    FOR EACH ROW EXECUTE FUNCTION log_data_access();

-- ============================================
-- 7. 创建数据清理策略
-- ============================================

-- 自动清理旧的访问日志
CREATE OR REPLACE FUNCTION cleanup_old_access_logs()
RETURNS void AS $$
BEGIN
    -- 删除30天前的访问日志
    DELETE FROM access_logs
    WHERE timestamp < NOW() - INTERVAL '30 days';

    -- 记录清理操作
    INSERT INTO access_logs (
        table_name,
        operation,
        user_id,
        user_role,
        additional_info
    ) VALUES (
        'access_logs',
        'CLEANUP',
        get_current_user_id(),
        auth.role(),
        jsonb_build_object('cleaned_records', ROW_COUNT)
    );
END;
$$ LANGUAGE plpgsql;

-- 创建定期清理任务（需要 pg_cron 扩展）
-- SELECT cron.schedule('cleanup-access-logs', '0 2 * * *', 'SELECT cleanup_old_access_logs();');

-- ============================================
-- 8. 创建数据权限检查函数
-- ============================================

-- 检查用户是否有权限访问特定数据
CREATE OR REPLACE FUNCTION check_data_access(
    p_table_name TEXT,
    p_operation TEXT,
    p_record_id INTEGER DEFAULT NULL
)
RETURNS boolean AS $$
DECLARE
    has_access boolean := false;
BEGIN
    -- 服务角色拥有所有权限
    IF is_service_request() THEN
        RETURN true;
    END IF;

    -- 根据表名和操作类型检查权限
    CASE p_table_name
        WHEN 'tools' THEN
            IF p_operation IN ('SELECT') THEN
                has_access := true; -- 公开读取
            ELSIF p_operation IN ('INSERT', 'UPDATE', 'DELETE') THEN
                has_access := is_service_request(); -- 仅服务可写
            END IF;

        WHEN 'analysis_logs' THEN
            IF p_operation IN ('SELECT') THEN
                has_access := is_admin(); -- 仅管理员可读
            ELSIF p_operation IN ('INSERT', 'UPDATE') THEN
                has_access := is_service_request(); -- 仅服务可写
            END IF;

        WHEN 'api_usage_stats' THEN
            IF p_operation IN ('SELECT') THEN
                has_access := is_admin(); -- 仅管理员可读
            ELSIF p_operation = 'INSERT' THEN
                has_access := true; -- 匿名可插入（用于日志）
            END IF;

        ELSE
            has_access := is_admin(); -- 其他表仅管理员可访问
    END CASE;

    -- 记录权限检查日志
    INSERT INTO access_logs (
        table_name,
        operation,
        user_id,
        user_role,
        record_id,
        additional_info
    ) VALUES (
        p_table_name,
        'PERMISSION_CHECK',
        get_current_user_id(),
        auth.role(),
        p_record_id::TEXT,
        jsonb_build_object('access_granted', has_access)
    );

    RETURN has_access;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 9. 创建安全监控视图
-- ============================================

-- 创建安全监控视图
CREATE OR REPLACE VIEW security_dashboard AS
SELECT
    -- 访问统计
    (SELECT COUNT(*) FROM access_logs WHERE DATE(timestamp) = CURRENT_DATE) as today_access_count,
    (SELECT COUNT(*) FROM access_logs WHERE DATE(timestamp) = CURRENT_DATE AND user_role = 'anonymous') as today_anonymous_access,
    (SELECT COUNT(*) FROM access_logs WHERE DATE(timestamp) = CURRENT_DATE AND user_role = 'authenticated') as today_authenticated_access,

    -- 操作统计
    (SELECT jsonb_agg(operation_stats) FROM (
        SELECT operation, COUNT(*) as count
        FROM access_logs
        WHERE DATE(timestamp) = CURRENT_DATE
        GROUP BY operation
    ) operation_stats) as operation_stats,

    -- 表访问统计
    (SELECT jsonb_agg(table_stats) FROM (
        SELECT table_name, COUNT(*) as count
        FROM access_logs
        WHERE DATE(timestamp) = CURRENT_DATE
        GROUP BY table_name
    ) table_stats) as table_access_stats,

    -- 最近的活动
    (SELECT jsonb_agg(recent_activities) FROM (
        SELECT table_name, operation, user_role, timestamp
        FROM access_logs
        ORDER BY timestamp DESC
        LIMIT 10
    ) recent_activities) as recent_activities,

    NOW() as last_updated;

COMMENT ON VIEW security_dashboard IS '安全监控仪表板，显示访问统计和活动日志';

-- ============================================
-- RLS 设置完成
-- ============================================

-- 创建 RLS 状态检查函数
CREATE OR REPLACE FUNCTION check_rls_status()
RETURNS TABLE(
    table_name TEXT,
    rls_enabled boolean,
    policy_count bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname||'.'||tablename as table_name,
        rowsecurity as rls_enabled,
        (SELECT COUNT(*) FROM pg_policies WHERE tablename = t.tablename) as policy_count
    FROM pg_tables t
    WHERE tablename IN ('tools', 'analysis_logs', 'api_usage_stats')
    ORDER BY tablename;
END;
$$ LANGUAGE plpgsql;

-- 运行RLS状态检查
-- SELECT * FROM check_rls_status();