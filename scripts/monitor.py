#!/usr/bin/env python3
"""
监控脚本 - 系统健康监控和告警
用法: python monitor.py [--health-check] [--logs] [--alerts] [--daemon]
"""

import argparse
import asyncio
import json
import logging
import smtplib
import sys
import time
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import psutil

# 项目根目录
project_root = Path(__file__).parent.parent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "logs" / "monitor.log")
    ]
)

logger = logging.getLogger(__name__)


class SystemMonitor:
    """系统监控器"""

    def __init__(self):
        self.config = self._load_config()
        self.alerts_sent = {}
        self.monitoring_data = {}

    def _load_config(self) -> Dict:
        """加载监控配置"""
        config_file = project_root / "deploy" / "monitoring.json"

        if not config_file.exists():
            # 创建默认配置
            default_config = {
                "health_checks": {
                    "enabled": True,
                    "interval": 300,  # 5分钟
                    "endpoints": [
                        {"name": "backend", "url": "http://localhost:8000/api/health"},
                        {"name": "frontend", "url": "http://localhost:3000"}
                    ]
                },
                "system_metrics": {
                    "enabled": True,
                    "interval": 60,  # 1分钟
                    "thresholds": {
                        "cpu_percent": 80,
                        "memory_percent": 85,
                        "disk_percent": 90
                    }
                },
                "logs": {
                    "enabled": True,
                    "level": "ERROR",
                    "patterns": ["ERROR", "CRITICAL", "FAILED"]
                },
                "alerts": {
                    "email": {
                        "enabled": False,
                        "smtp_host": "",
                        "smtp_port": 587,
                        "username": "",
                        "password": "",
                        "recipients": []
                    },
                    "webhook": {
                        "enabled": False,
                        "url": ""
                    }
                }
            }

            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)

            return default_config

        with open(config_file, 'r') as f:
            return json.load(f)

    async def run_health_checks(self) -> Dict:
        """运行健康检查"""
        if not self.config["health_checks"]["enabled"]:
            return {}

        results = {}
        endpoints = self.config["health_checks"]["endpoints"]

        async with httpx.AsyncClient(timeout=30) as client:
            for endpoint in endpoints:
                name = endpoint["name"]
                url = endpoint["url"]

                try:
                    start_time = time.time()
                    response = await client.get(url)
                    response_time = (time.time() - start_time) * 1000

                    results[name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "status_code": response.status_code,
                        "response_time_ms": round(response_time, 2),
                        "timestamp": datetime.now().isoformat()
                    }

                    # 检查响应时间
                    if response_time > 5000:  # 5秒
                        await self._send_alert(
                            f"High response time for {name}",
                            f"Response time: {response_time:.2f}ms"
                        )

                except Exception as e:
                    results[name] = {
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }

                    await self._send_alert(
                        f"Health check failed for {name}",
                        f"Error: {str(e)}"
                    )

        return results

    def get_system_metrics(self) -> Dict:
        """获取系统指标"""
        if not self.config["system_metrics"]["enabled"]:
            return {}

        thresholds = self.config["system_metrics"]["thresholds"]

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100

        metrics = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "timestamp": datetime.now().isoformat()
        }

        # 检查阈值
        alerts = []

        if cpu_percent > thresholds["cpu_percent"]:
            alerts.append(f"CPU usage high: {cpu_percent}%")

        if memory_percent > thresholds["memory_percent"]:
            alerts.append(f"Memory usage high: {memory_percent}%")

        if disk_percent > thresholds["disk_percent"]:
            alerts.append(f"Disk usage high: {disk_percent}%")

        # 发送告警
        if alerts:
            asyncio.create_task(
                self._send_alert("System resource alerts", "; ".join(alerts))
            )

        return metrics

    def check_logs(self) -> List[Dict]:
        """检查日志错误"""
        if not self.config["logs"]["enabled"]:
            return []

        error_patterns = self.config["logs"]["patterns"]
        log_files = [
            project_root / "logs" / "daily_scan.log",
            project_root / "logs" / "scheduler.log",
            project_root / "logs" / "deploy.log",
            project_root / "logs" / "monitor.log"
        ]

        errors = []

        for log_file in log_files:
            if not log_file.exists():
                continue

            try:
                # 检查最近1小时的日志
                cutoff_time = datetime.now() - timedelta(hours=1)
                recent_errors = []

                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        # 检查时间戳
                        try:
                            line_time_str = line.split(' - ')[0]
                            line_time = datetime.strptime(line_time_str, '%Y-%m-%d %H:%M:%S,%f')

                            if line_time < cutoff_time:
                                continue
                        except:
                            continue

                        # 检查错误模式
                        line_lower = line.lower()
                        if any(pattern.lower() in line_lower for pattern in error_patterns):
                            recent_errors.append({
                                "file": log_file.name,
                                "timestamp": line_time_str,
                                "message": line.strip()
                            })

                if recent_errors:
                    errors.extend(recent_errors)

            except Exception as e:
                logger.warning(f"检查日志文件 {log_file} 失败: {e}")

        # 如果有新错误，发送告警
        if errors:
            error_summary = f"发现 {len(errors)} 个新错误"
            asyncio.create_task(
                self._send_alert(error_summary, json.dumps(errors[:5], ensure_ascii=False))
            )

        return errors

    async def _send_alert(self, subject: str, message: str):
        """发送告警"""
        alert_key = f"{subject}:{message}"
        current_time = datetime.now()

        # 避免重复发送（1小时内不重复）
        if alert_key in self.alerts_sent:
            last_sent = self.alerts_sent[alert_key]
            if current_time - last_sent < timedelta(hours=1):
                return

        # 邮件告警
        if self.config["alerts"]["email"]["enabled"]:
            await self._send_email_alert(subject, message)

        # Webhook告警
        if self.config["alerts"]["webhook"]["enabled"]:
            await self._send_webhook_alert(subject, message)

        self.alerts_sent[alert_key] = current_time
        logger.warning(f"告警已发送: {subject}")

    async def _send_email_alert(self, subject: str, message: str):
        """发送邮件告警"""
        try:
            email_config = self.config["alerts"]["email"]

            msg = MimeMultipart()
            msg['From'] = email_config["username"]
            msg['To'] = ", ".join(email_config["recipients"])
            msg['Subject'] = f"[AutoSaaS Radar Alert] {subject}"

            body = f"""
告警时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

告警内容:
{message}

---
AutoSaaS Radar 监控系统
            """

            msg.attach(MimeText(body, 'plain', 'utf-8'))

            server = smtplib.SMTP(email_config["smtp_host"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.send_message(msg)
            server.quit()

        except Exception as e:
            logger.error(f"发送邮件告警失败: {e}")

    async def _send_webhook_alert(self, subject: str, message: str):
        """发送Webhook告警"""
        try:
            webhook_config = self.config["alerts"]["webhook"]
            webhook_url = webhook_config["url"]

            payload = {
                "timestamp": datetime.now().isoformat(),
                "subject": subject,
                "message": message,
                "service": "autosaas-radar"
            }

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()

        except Exception as e:
            logger.error(f"发送Webhook告警失败: {e}")

    async def run_monitoring(self, daemon: bool = False):
        """运行监控"""
        logger.info("启动系统监控...")

        try:
            while True:
                # 健康检查
                health_results = await self.run_health_checks()
                if health_results:
                    self.monitoring_data["health"] = health_results

                # 系统指标
                system_metrics = self.get_system_metrics()
                if system_metrics:
                    self.monitoring_data["system"] = system_metrics

                # 日志检查
                log_errors = self.check_logs()
                if log_errors:
                    self.monitoring_data["errors"] = log_errors

                # 保存监控数据
                self._save_monitoring_data()

                if not daemon:
                    break

                # 等待下次检查
                await asyncio.sleep(60)  # 1分钟检查一次

        except KeyboardInterrupt:
            logger.info("监控已停止")
        except Exception as e:
            logger.error(f"监控异常: {e}")

    def _save_monitoring_data(self):
        """保存监控数据"""
        try:
            monitor_dir = project_root / "monitor"
            monitor_dir.mkdir(exist_ok=True)

            data_file = monitor_dir / f"monitor_{datetime.now().strftime('%Y%m%d')}.json"

            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.monitoring_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存监控数据失败: {e}")

    def get_status(self) -> Dict:
        """获取监控状态"""
        return {
            "config": self.config,
            "monitoring_data": self.monitoring_data,
            "alerts_sent_count": len(self.alerts_sent),
            "timestamp": datetime.now().isoformat()
        }


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="系统监控脚本")
    parser.add_argument("--health-check", action="store_true", help="运行健康检查")
    parser.add_argument("--logs", action="store_true", help="检查日志错误")
    parser.add_argument("--alerts", action="store_true", help="测试告警发送")
    parser.add_argument("--daemon", action="store_true", help="后台运行监控")

    args = parser.parse_args()

    # 创建日志目录
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    monitor = SystemMonitor()

    try:
        if args.health_check:
            results = await monitor.run_health_checks()
            print(json.dumps(results, indent=2, ensure_ascii=False))
        elif args.logs:
            errors = monitor.check_logs()
            print(json.dumps(errors, indent=2, ensure_ascii=False))
        elif args.alerts:
            await monitor._send_alert("测试告警", "这是一条测试告警消息")
            print("测试告警已发送")
        else:
            await monitor.run_monitoring(daemon=args.daemon)

    except Exception as e:
        logger.error(f"监控运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())