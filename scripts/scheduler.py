#!/usr/bin/env python3
"""
调度器脚本 - 管理定时任务调度
用法: python scheduler.py [--start] [--stop] [--status] [--daemon]
"""

import asyncio
import argparse
import json
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import schedule
import psutil

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.core.config import settings
from daily_scan import DailyScanner

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "logs" / "scheduler.log")
    ]
)

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.running = False
        self.scheduler_pid_file = project_root / "tmp" / "scheduler.pid"
        self.status_file = project_root / "tmp" / "scheduler_status.json"

        # 创建临时目录
        self.scheduler_pid_file.parent.mkdir(exist_ok=True)

        self.scanner = DailyScanner()
        self.setup_schedule()

    def setup_schedule(self):
        """设置定时任务"""
        # 每日扫描任务
        cron_parts = settings.CRON_SCHEDULE.split()
        if len(cron_parts) == 5:
            minute, hour, day, month, weekday = cron_parts

            if hour != "*" and minute != "*":
                # 每天固定时间
                schedule.every().day.at(f"{hour}:{minute}").do(self._run_daily_scan)
                logger.info(f"设置每日扫描任务: {hour}:{minute}")
            elif hour == "*" and minute != "*":
                # 每小时特定分钟
                schedule.every().hour.at(f":{minute}").do(self._run_daily_scan)
                logger.info(f"设置每小时扫描任务: 第{minute}分钟")
            else:
                # 默认每天上午9点
                schedule.every().day.at("09:00").do(self._run_daily_scan)
                logger.info("设置默认每日扫描任务: 09:00")
        else:
            # 默认设置
            schedule.every().day.at("09:00").do(self._run_daily_scan)
            logger.info("设置默认每日扫描任务: 09:00")

        # 每周日生成周报
        schedule.every().sunday.at("18:00").do(self._generate_weekly_report)
        logger.info("设置周报生成任务: 每周日 18:00")

        # 每小时清理临时文件
        schedule.every().hour.do(self._cleanup_temp_files)
        logger.info("设置临时文件清理任务: 每小时")

    def _run_daily_scan(self):
        """运行每日扫描任务"""
        logger.info("开始执行定时扫描任务")

        try:
            # 在新进程中运行扫描，避免阻塞调度器
            success = asyncio.run(self.scanner.run_scan())

            if success:
                logger.info("定时扫描任务完成")
                self._update_task_status("daily_scan", "success", datetime.now())
            else:
                logger.error("定时扫描任务失败")
                self._update_task_status("daily_scan", "failed", datetime.now())

        except Exception as e:
            logger.error(f"定时扫描任务异常: {e}")
            self._update_task_status("daily_scan", "error", datetime.now(), str(e))

    def _generate_weekly_report(self):
        """生成周报"""
        logger.info("开始生成周报")

        try:
            from .weekly_report import WeeklyReportGenerator

            generator = WeeklyReportGenerator()
            report_path = asyncio.run(generator.generate_report())

            logger.info(f"周报生成完成: {report_path}")
            self._update_task_status("weekly_report", "success", datetime.now())

        except Exception as e:
            logger.error(f"周报生成失败: {e}")
            self._update_task_status("weekly_report", "error", datetime.now(), str(e))

    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            temp_dirs = [
                project_root / "tmp",
                project_root / "logs"
            ]

            cleaned_files = 0
            cutoff_time = datetime.now() - timedelta(days=7)

            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    for file_path in temp_dir.glob("*"):
                        if file_path.is_file():
                            # 检查文件修改时间
                            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_mtime < cutoff_time:
                                file_path.unlink()
                                cleaned_files += 1

            if cleaned_files > 0:
                logger.info(f"清理了 {cleaned_files} 个临时文件")

        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")

    def _update_task_status(self, task_name: str, status: str,
                          run_time: datetime, error: str = None):
        """更新任务状态"""
        try:
            status_data = self._load_status()

            if "tasks" not in status_data:
                status_data["tasks"] = {}

            status_data["tasks"][task_name] = {
                "last_run": run_time.isoformat(),
                "status": status,
                "error": error
            }
            status_data["scheduler_updated"] = datetime.now().isoformat()

            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)

        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")

    def _load_status(self) -> Dict:
        """加载状态文件"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载状态文件失败: {e}")

        return {
            "scheduler_started": None,
            "tasks": {}
        }

    def start(self, daemon: bool = False):
        """启动调度器"""
        if self.is_running():
            logger.error("调度器已在运行")
            return False

        self.running = True

        # 写入PID文件
        with open(self.scheduler_pid_file, 'w') as f:
            f.write(str(os.getpid()))

        # 更新状态
        status_data = self._load_status()
        status_data["scheduler_started"] = datetime.now().isoformat()
        status_data["scheduler_pid"] = os.getpid()

        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)

        logger.info("调度器已启动")

        if daemon:
            self._run_daemon()
        else:
            self._run_foreground()

    def stop(self):
        """停止调度器"""
        if not self.is_running():
            logger.error("调度器未运行")
            return False

        try:
            # 读取PID
            with open(self.scheduler_pid_file, 'r') as f:
                pid = int(f.read().strip())

            # 终止进程
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=10)

            # 删除PID文件
            self.scheduler_pid_file.unlink()

            logger.info("调度器已停止")
            return True

        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
            return False

    def is_running(self) -> bool:
        """检查调度器是否运行"""
        if not self.scheduler_pid_file.exists():
            return False

        try:
            with open(self.scheduler_pid_file, 'r') as f:
                pid = int(f.read().strip())

            # 检查进程是否存在
            return psutil.pid_exists(pid)

        except Exception:
            return False

    def get_status(self) -> Dict:
        """获取调度器状态"""
        status_data = self._load_status()

        status_data.update({
            "is_running": self.is_running(),
            "next_runs": {
                "daily_scan": schedule.next_run() if schedule.jobs else None
            }
        })

        return status_data

    def _run_foreground(self):
        """前台运行"""
        logger.info("调度器前台运行中...")

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止调度器")
        finally:
            self._cleanup()

    def _run_daemon(self):
        """后台运行"""
        import daemon

        logger.info("调度器后台运行中...")

        with daemon.DaemonContext():
            try:
                while self.running:
                    schedule.run_pending()
                    time.sleep(60)
            except Exception as e:
                logger.error(f"调度器异常: {e}")
            finally:
                self._cleanup()

    def _cleanup(self):
        """清理资源"""
        self.running = False

        if self.scheduler_pid_file.exists():
            self.scheduler_pid_file.unlink()

        logger.info("调度器已清理")


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在停止调度器...")
    sys.exit(0)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="任务调度器")
    parser.add_argument("--start", action="store_true", help="启动调度器")
    parser.add_argument("--stop", action="store_true", help="停止调度器")
    parser.add_argument("--status", action="store_true", help="查看状态")
    parser.add_argument("--daemon", action="store_true", help="后台运行")

    args = parser.parse_args()

    # 创建日志目录
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    scheduler = TaskScheduler()

    # 注册信号处理器
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        if args.start:
            scheduler.start(daemon=args.daemon)
        elif args.stop:
            success = scheduler.stop()
            sys.exit(0 if success else 1)
        elif args.status:
            status = scheduler.get_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            parser.print_help()
    except Exception as e:
        logger.error(f"调度器操作失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()