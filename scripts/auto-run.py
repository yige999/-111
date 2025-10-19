#!/usr/bin/env python3
"""
AutoSaaS Radar - 自动化调度脚本
窗口10：部署自动化

功能：
1. 定时执行数据抓取
2. AI分析处理
3. 数据库更新
4. 错误处理和重试
"""

import os
import sys
import json
import logging
import schedule
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto-run.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AutoScheduler:
    def __init__(self):
        self.config_file = project_root / "config" / "deploy-config.json"
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info("配置文件加载成功")
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            self.config = self.get_default_config()

    def get_default_config(self):
        """获取默认配置"""
        return {
            "automation": {
                "schedule": "0 9 * * *",
                "retryAttempts": 3,
                "timeout": 300
            }
        }

    def run_data_scraper(self):
        """运行数据抓取"""
        logger.info("🔍 开始数据抓取...")
        try:
            # 导入抓取模块
            from backend.scrapers.rss_scraper import RSScraper
            from backend.scrapers.social_scraper import SocialScraper

            # RSS抓取
            rss_scraper = RSScraper()
            rss_data = rss_scraper.scrape_all()
            logger.info(f"RSS抓取完成，获得 {len(rss_data)} 条数据")

            # 社媒抓取
            social_scraper = SocialScraper()
            social_data = social_scraper.scrape_all()
            logger.info(f"社媒抓取完成，获得 {len(social_data)} 条数据")

            return rss_data + social_data

        except Exception as e:
            logger.error(f"数据抓取失败: {e}")
            return []

    def run_ai_analysis(self, raw_data):
        """运行AI分析"""
        logger.info("🤖 开始AI分析...")
        try:
            from backend.analyzer.gpt_analyzer import GPTAnalyzer

            analyzer = GPTAnalyzer()
            analyzed_data = analyzer.analyze_tools(raw_data)
            logger.info(f"AI分析完成，处理 {len(analyzed_data)} 个工具")

            return analyzed_data

        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return []

    def run_database_update(self, analyzed_data):
        """运行数据库更新"""
        logger.info("💾 开始数据库更新...")
        try:
            from backend.database.supabase_client import SupabaseClient

            db_client = SupabaseClient()
            inserted_count = db_client.batch_insert_tools(analyzed_data)
            logger.info(f"数据库更新完成，插入 {inserted_count} 条记录")

            return inserted_count

        except Exception as e:
            logger.error(f"数据库更新失败: {e}")
            return 0

    def run_full_pipeline(self):
        """运行完整的自动化流程"""
        logger.info("🚀 开始完整的自动化流程...")
        start_time = datetime.now()

        try:
            # 1. 数据抓取
            raw_data = self.run_data_scraper()
            if not raw_data:
                logger.warning("没有抓取到数据，流程终止")
                return

            # 2. AI分析
            analyzed_data = self.run_ai_analysis(raw_data)
            if not analyzed_data:
                logger.warning("AI分析失败，流程终止")
                return

            # 3. 数据库更新
            inserted_count = self.run_database_update(analyzed_data)

            # 4. 发送通知
            self.send_completion_notification(inserted_count)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"✅ 自动化流程完成！耗时: {duration:.2f}秒，新增记录: {inserted_count}")

        except Exception as e:
            logger.error(f"自动化流程失败: {e}")
            self.send_error_notification(str(e))

    def send_completion_notification(self, count):
        """发送完成通知"""
        try:
            # 这里可以添加邮件或Telegram通知
            logger.info(f"📢 自动化任务完成，新增 {count} 个AI工具分析")
        except Exception as e:
            logger.error(f"通知发送失败: {e}")

    def send_error_notification(self, error_msg):
        """发送错误通知"""
        try:
            # 这里可以添加错误通知
            logger.error(f"🚨 自动化任务失败: {error_msg}")
        except Exception as e:
            logger.error(f"错误通知发送失败: {e}")

    def setup_scheduler(self):
        """设置定时调度"""
        schedule_str = self.config.get("automation", {}).get("schedule", "0 9 * * *")

        # 简单的定时实现
        if schedule_str == "0 9 * * *":  # 每天上午9点
            schedule.every().day.at("09:00").do(self.run_full_pipeline)
        elif schedule_str == "*/30 * * * *":  # 每30分钟（测试用）
            schedule.every(30).minutes.do(self.run_full_pipeline)
        else:
            # 默认每小时运行一次
            schedule.every().hour.do(self.run_full_pipeline)

        logger.info(f"定时调度已设置: {schedule_str}")

    def run_scheduler(self):
        """运行调度器"""
        logger.info("🕐 调度器启动，等待执行时间...")

        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次

def main():
    """主函数"""
    # 创建日志目录
    os.makedirs("logs", exist_ok=True)

    # 初始化调度器
    scheduler = AutoScheduler()

    if len(sys.argv) > 1 and sys.argv[1] == "--run-now":
        # 立即执行一次
        scheduler.run_full_pipeline()
    else:
        # 设置定时调度
        scheduler.setup_scheduler()
        scheduler.run_scheduler()

if __name__ == "__main__":
    main()