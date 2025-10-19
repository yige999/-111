#!/usr/bin/env python3
"""
AutoSaaS Radar - 健康检查脚本
窗口10：部署自动化

检查项目各组件状态：
1. 数据库连接
2. API响应
3. 前端页面
4. 最新数据
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self):
        self.status = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }

    def check_database_connection(self):
        """检查数据库连接"""
        logger.info("🔍 检查数据库连接...")
        try:
            from backend.database.supabase_client import SupabaseClient

            db_client = SupabaseClient()
            # 尝试获取一条数据
            result = db_client.client.table('tools').select('id').limit(1).execute()

            if result.data:
                self.status["checks"]["database"] = {
                    "status": "healthy",
                    "message": "数据库连接正常",
                    "response_time": "fast"
                }
                logger.info("✅ 数据库连接正常")
            else:
                self.status["checks"]["database"] = {
                    "status": "warning",
                    "message": "数据库连接成功但无数据"
                }
                logger.warning("⚠️ 数据库连接成功但无数据")

        except Exception as e:
            self.status["checks"]["database"] = {
                "status": "error",
                "message": f"数据库连接失败: {str(e)}"
            }
            logger.error(f"❌ 数据库连接失败: {e}")

    def check_api_endpoints(self):
        """检查API端点"""
        logger.info("🔍 检查API端点...")
        api_base = os.getenv("API_HOST", "localhost") + ":" + os.getenv("API_PORT", "8000")

        endpoints = [
            "/api/tools/latest",
            "/api/tools/categories",
            "/api/tools/stats"
        ]

        api_status = {"status": "healthy", "endpoints": {}}

        for endpoint in endpoints:
            try:
                url = f"http://{api_base}{endpoint}"
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    api_status["endpoints"][endpoint] = {
                        "status": "healthy",
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    }
                    logger.info(f"✅ {endpoint} - {response.status_code}")
                else:
                    api_status["endpoints"][endpoint] = {
                        "status": "error",
                        "status_code": response.status_code,
                        "message": response.text
                    }
                    logger.error(f"❌ {endpoint} - {response.status_code}")
                    api_status["status"] = "error"

            except Exception as e:
                api_status["endpoints"][endpoint] = {
                    "status": "error",
                    "message": str(e)
                }
                logger.error(f"❌ {endpoint} - 连接失败: {e}")
                api_status["status"] = "error"

        self.status["checks"]["api"] = api_status

    def check_latest_data(self):
        """检查最新数据"""
        logger.info("🔍 检查最新数据...")
        try:
            from backend.database.supabase_client import SupabaseClient

            db_client = SupabaseClient()

            # 检查今天是否有新数据
            today = datetime.now().date()
            result = db_client.client.table('tools').select('id, created_at')\
                .gte('created_at', today.isoformat())\
                .execute()

            today_count = len(result.data)

            # 检查最近7天的数据
            week_ago = (datetime.now() - timedelta(days=7)).date()
            week_result = db_client.client.table('tools').select('id, created_at')\
                .gte('created_at', week_ago.isoformat())\
                .execute()

            week_count = len(week_result.data)

            data_status = {
                "today_count": today_count,
                "week_count": week_count,
                "last_updated": None
            }

            if week_result.data:
                # 获取最新数据时间
                latest = max(week_result.data, key=lambda x: x['created_at'])
                data_status["last_updated"] = latest['created_at']

            if today_count > 0:
                data_status["status"] = "healthy"
                data_status["message"] = f"今天有 {today_count} 条新数据"
                logger.info(f"✅ 今天有 {today_count} 条新数据")
            elif week_count > 0:
                data_status["status"] = "warning"
                data_status["message"] = f"今天无新数据，本周有 {week_count} 条数据"
                logger.warning(f"⚠️ 今天无新数据，本周有 {week_count} 条数据")
            else:
                data_status["status"] = "error"
                data_status["message"] = "最近一周无数据"
                logger.error("❌ 最近一周无数据")

            self.status["checks"]["data"] = data_status

        except Exception as e:
            self.status["checks"]["data"] = {
                "status": "error",
                "message": f"数据检查失败: {str(e)}"
            }
            logger.error(f"❌ 数据检查失败: {e}")

    def check_dependencies(self):
        """检查依赖项"""
        logger.info("🔍 检查依赖项...")

        deps_status = {"status": "healthy", "dependencies": {}}

        # 检查Python包
        required_packages = [
            "requests",
            "openai",
            "supabase",
            "schedule",
            "fastapi"
        ]

        for package in required_packages:
            try:
                __import__(package)
                deps_status["dependencies"][package] = "installed"
                logger.info(f"✅ {package} - 已安装")
            except ImportError:
                deps_status["dependencies"][package] = "missing"
                deps_status["status"] = "error"
                logger.error(f"❌ {package} - 未安装")

        # 检查环境变量
        required_env_vars = [
            "OPENAI_API_KEY",
            "SUPABASE_URL",
            "SUPABASE_KEY"
        ]

        for env_var in required_env_vars:
            if os.getenv(env_var):
                deps_status["dependencies"][env_var] = "set"
                logger.info(f"✅ {env_var} - 已设置")
            else:
                deps_status["dependencies"][env_var] = "missing"
                deps_status["status"] = "error"
                logger.error(f"❌ {env_var} - 未设置")

        self.status["checks"]["dependencies"] = deps_status

    def run_all_checks(self):
        """运行所有健康检查"""
        logger.info("🏥 开始健康检查...")

        self.check_database_connection()
        self.check_api_endpoints()
        self.check_latest_data()
        self.check_dependencies()

        # 计算整体状态
        all_statuses = [check.get("status", "unknown") for check in self.status["checks"].values()]

        if "error" in all_statuses:
            overall_status = "error"
        elif "warning" in all_statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        self.status["overall_status"] = overall_status

        return self.status

    def save_report(self, filename=None):
        """保存健康检查报告"""
        if not filename:
            filename = f"logs/health-check-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        os.makedirs("logs", exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 健康检查报告已保存: {filename}")
        return filename

def main():
    """主函数"""
    checker = HealthChecker()

    # 运行所有检查
    status = checker.run_all_checks()

    # 保存报告
    report_file = checker.save_report()

    # 输出总结
    print("\n" + "="*50)
    print(f"🏥 AutoSaaS Radar 健康检查完成")
    print(f"📊 整体状态: {status['overall_status'].upper()}")
    print(f"📝 详细报告: {report_file}")
    print("="*50)

    # 根据状态设置退出码
    if status['overall_status'] == 'error':
        sys.exit(1)
    elif status['overall_status'] == 'warning':
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()