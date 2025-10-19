#!/usr/bin/env python3
"""
每日扫描脚本 - 自动抓取和分析AI工具数据
用法: python daily_scan.py [--dry-run] [--force]
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.core.config import settings
from app.services.data_collector import DataCollector
from app.services.gpt_analyzer import GPTAnalyzer
from app.database.connection import DatabaseManager
from app.models.analysis import AnalysisLog

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "logs" / "daily_scan.log")
    ]
)

logger = logging.getLogger(__name__)


class DailyScanner:
    """每日扫描器"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.data_collector = DataCollector()
        self.gpt_analyzer = GPTAnalyzer()

    async def run_scan(self, dry_run: bool = False, force: bool = False) -> bool:
        """运行每日扫描"""
        start_time = datetime.now()
        logger.info(f"开始每日扫描任务 - {start_time}")

        try:
            # 初始化数据库连接
            await self.db_manager.initialize()
            logger.info("数据库连接成功")

            # 检查是否需要运行（避免重复）
            if not force and not dry_run:
                if await self._already_scanned_today():
                    logger.info("今日已执行扫描，跳过")
                    return True

            # 1. 收集数据
            logger.info("开始收集数据...")
            raw_tools = await self._collect_data()
            if not raw_tools:
                logger.warning("未收集到任何数据")
                return False

            logger.info(f"收集到 {len(raw_tools)} 个工具")

            # 2. 分析数据
            logger.info("开始分析数据...")
            analyzed_tools = await self._analyze_data(raw_tools)
            if not analyzed_tools:
                logger.warning("分析结果为空")
                return False

            logger.info(f"分析了 {len(analyzed_tools)} 个工具")

            # 3. 保存数据
            if not dry_run:
                logger.info("开始保存数据...")
                saved_count = await self._save_data(analyzed_tools)
                logger.info(f"保存了 {saved_count} 个工具到数据库")

                # 4. 记录分析日志
                await self._log_analysis(
                    tools_collected=len(raw_tools),
                    tools_analyzed=len(analyzed_tools),
                    tools_saved=saved_count,
                    status="success"
                )
            else:
                logger.info("[DRY RUN] 跳过数据保存")

            # 5. 生成报告
            await self._generate_report(raw_tools, analyzed_tools, dry_run)

            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"扫描任务完成 - 耗时: {duration}")

            return True

        except Exception as e:
            logger.error(f"扫描任务失败: {e}", exc_info=True)

            # 记录错误日志
            if not dry_run:
                await self._log_analysis(
                    tools_collected=0,
                    tools_analyzed=0,
                    tools_saved=0,
                    status="failed",
                    error_message=str(e)
                )

            return False

        finally:
            # 清理资源
            await self.db_manager.close()

    async def _collect_data(self):
        """收集数据"""
        try:
            async with self.data_collector:
                return await self.data_collector.collect_all_sources()
        except Exception as e:
            logger.error(f"数据收集失败: {e}")
            raise

    async def _analyze_data(self, raw_tools):
        """分析数据"""
        try:
            # 估算成本
            cost_info = await self.gpt_analyzer.get_analysis_cost(len(raw_tools))
            logger.info(f"预估分析成本: ${cost_info['estimated_cost_usd']:.4f}")

            # 执行分析
            return await self.gpt_analyzer.analyze_tools(raw_tools)
        except Exception as e:
            logger.error(f"数据分析失败: {e}")
            raise

    async def _save_data(self, analyzed_tools):
        """保存数据到数据库"""
        try:
            saved_count = 0
            for tool in analyzed_tools:
                success = await self.db_manager.save_tool(tool)
                if success:
                    saved_count += 1
            return saved_count
        except Exception as e:
            logger.error(f"数据保存失败: {e}")
            raise

    async def _log_analysis(self, tools_collected: int, tools_analyzed: int,
                          tools_saved: int, status: str, error_message: str = None):
        """记录分析日志"""
        try:
            log_entry = AnalysisLog(
                date=datetime.now(),
                tools_collected=tools_collected,
                tools_analyzed=tools_analyzed,
                tools_saved=tools_saved,
                status=status,
                error_message=error_message
            )
            await self.db_manager.save_analysis_log(log_entry)
        except Exception as e:
            logger.error(f"记录分析日志失败: {e}")

    async def _already_scanned_today(self) -> bool:
        """检查今日是否已扫描"""
        try:
            today = datetime.now().date()
            log = await self.db_manager.get_latest_analysis_log()

            if log and log.date.date() == today:
                return log.status == "success"
            return False
        except Exception as e:
            logger.warning(f"检查扫描状态失败: {e}")
            return False

    async def _generate_report(self, raw_tools, analyzed_tools, dry_run: bool):
        """生成扫描报告"""
        try:
            # 统计数据
            categories = {}
            trends = {}
            sources = {}

            for tool in analyzed_tools:
                # 统计分类
                category = tool.category.value
                categories[category] = categories.get(category, 0) + 1

                # 统计趋势
                trend = tool.trend_signal.value
                trends[trend] = trends.get(trend, 0) + 1

            for tool in raw_tools:
                # 统计数据源
                source = tool.source
                sources[source] = sources.get(source, 0) + 1

            report = {
                "timestamp": datetime.now().isoformat(),
                "dry_run": dry_run,
                "summary": {
                    "tools_collected": len(raw_tools),
                    "tools_analyzed": len(analyzed_tools),
                    "categories": categories,
                    "trends": trends,
                    "sources": sources
                },
                "top_tools": [
                    {
                        "name": tool.tool_name,
                        "category": tool.category.value,
                        "trend": tool.trend_signal.value,
                        "pain_point": tool.pain_point,
                        "ideas": tool.micro_saas_ideas
                    }
                    for tool in analyzed_tools[:5]  # Top 5
                ]
            }

            # 保存报告
            reports_dir = project_root / "reports"
            reports_dir.mkdir(exist_ok=True)

            report_file = reports_dir / f"scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"扫描报告已保存: {report_file}")

            # 输出摘要
            logger.info("=== 扫描摘要 ===")
            logger.info(f"收集工具: {len(raw_tools)}")
            logger.info(f"分析工具: {len(analyzed_tools)}")
            logger.info(f"分类分布: {categories}")
            logger.info(f"趋势分布: {trends}")
            logger.info(f"数据源分布: {sources}")

        except Exception as e:
            logger.error(f"生成报告失败: {e}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="每日扫描脚本")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不保存数据")
    parser.add_argument("--force", action="store_true", help="强制运行，忽略重复检查")

    args = parser.parse_args()

    # 创建日志目录
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # 运行扫描
    scanner = DailyScanner()
    success = await scanner.run_scan(dry_run=args.dry_run, force=args.force)

    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())