#!/usr/bin/env python3
"""
部署脚本 - 自动化部署到生产环境
用法: python deploy.py [--backend] [--frontend] [--database] [--all] [--env=production|staging]
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 项目根目录
project_root = Path(__file__).parent.parent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "logs" / "deploy.log")
    ]
)

logger = logging.getLogger(__name__)


class Deployer:
    """部署管理器"""

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.deploy_config = self._load_deploy_config()
        self.deploy_log = []

    def _load_deploy_config(self) -> Dict:
        """加载部署配置"""
        config_file = project_root / "deploy" / "config.json"

        if not config_file.exists():
            logger.error(f"部署配置文件不存在: {config_file}")
            sys.exit(1)

        with open(config_file, 'r') as f:
            config = json.load(f)

        return config.get(self.environment, {})

    def deploy_backend(self) -> bool:
        """部署后端服务"""
        logger.info("开始部署后端服务...")

        try:
            backend_dir = project_root / "backend"

            # 1. 检查代码
            if not self._run_command(["git", "pull", "origin", "main"], backend_dir):
                return False

            # 2. 安装依赖
            if not self._run_command(["pip", "install", "-r", "requirements.txt"], backend_dir):
                return False

            # 3. 运行测试
            if self.deploy_config.get("run_tests", True):
                if not self._run_command(["python", "-m", "pytest", "tests/"], backend_dir):
                    logger.warning("后端测试失败，但继续部署")

            # 4. 构建Docker镜像（如果使用Docker）
            if self.deploy_config.get("use_docker", False):
                docker_tag = f"autosaas-backend:{int(time.time())}"
                if not self._run_command([
                    "docker", "build", "-t", docker_tag, "."
                ], backend_dir):
                    return False

                # 推送到镜像仓库
                registry = self.deploy_config.get("docker_registry")
                if registry:
                    if not self._run_command([
                        "docker", "tag", docker_tag, f"{registry}/{docker_tag}"
                    ], backend_dir):
                        return False

                    if not self._run_command([
                        "docker", "push", f"{registry}/{docker_tag}"
                    ], backend_dir):
                        return False

            # 5. 重启服务
            if self.deploy_config.get("use_systemd", False):
                if not self._restart_systemd_service("autosaas-backend"):
                    return False
            else:
                # 使用进程管理器重启
                if not self._restart_process_manager("backend"):
                    return False

            # 6. 健康检查
            if not self._health_check_backend():
                return False

            self._log_deploy_step("backend", "success", "后端服务部署成功")
            return True

        except Exception as e:
            logger.error(f"后端部署失败: {e}")
            self._log_deploy_step("backend", "failed", str(e))
            return False

    def deploy_frontend(self) -> bool:
        """部署前端应用"""
        logger.info("开始部署前端应用...")

        try:
            frontend_dir = project_root / "frontend"

            # 1. 检查代码
            if not self._run_command(["git", "pull", "origin", "main"], frontend_dir):
                return False

            # 2. 安装依赖
            if not self._run_command(["npm", "install"], frontend_dir):
                return False

            # 3. 构建应用
            env_vars = self.deploy_config.get("frontend_env", {})
            env_cmd = []
            for key, value in env_vars.items():
                env_cmd.extend([f"{key}={value}"])

            build_cmd = env_cmd + ["npm", "run", "build"]
            if not self._run_command(build_cmd, frontend_dir):
                return False

            # 4. 部署到Vercel
            if self.deploy_config.get("use_vercel", True):
                vercel_cmd = ["vercel", "--prod"]
                if self.environment == "staging":
                    vercel_cmd = ["vercel"]

                if not self._run_command(vercel_cmd, frontend_dir):
                    return False

            # 5. 健康检查
            if not self._health_check_frontend():
                return False

            self._log_deploy_step("frontend", "success", "前端应用部署成功")
            return True

        except Exception as e:
            logger.error(f"前端部署失败: {e}")
            self._log_deploy_step("frontend", "failed", str(e))
            return False

    def deploy_database(self) -> bool:
        """部署数据库迁移"""
        logger.info("开始部署数据库迁移...")

        try:
            database_dir = project_root / "database"

            # 1. 备份数据库
            if not self._backup_database():
                return False

            # 2. 运行迁移
            migration_files = sorted(database_dir.glob("*.sql"))
            for migration_file in migration_files:
                logger.info(f"运行迁移: {migration_file.name}")
                if not self._run_sql_file(migration_file):
                    return False

            # 3. 验证数据库
            if not self._verify_database():
                return False

            self._log_deploy_step("database", "success", "数据库迁移成功")
            return True

        except Exception as e:
            logger.error(f"数据库部署失败: {e}")
            self._log_deploy_step("database", "failed", str(e))
            return False

    def deploy_all(self) -> bool:
        """部署所有服务"""
        logger.info("开始完整部署...")

        # 按顺序部署：数据库 -> 后端 -> 前端
        services = ["database", "backend", "frontend"]
        success_count = 0

        for service in services:
            if getattr(self, f"deploy_{service}")():
                success_count += 1
                logger.info(f"{service} 部署成功")
            else:
                logger.error(f"{service} 部署失败")
                if service == "database":
                    # 数据库部署失败时停止整个部署
                    logger.error("数据库部署失败，停止后续部署")
                    break

        # 生成部署报告
        self._generate_deploy_report(success_count, len(services))

        return success_count == len(services)

    def _run_command(self, cmd: List[str], cwd: Path, timeout: int = 300) -> bool:
        """运行命令"""
        try:
            logger.info(f"执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=cwd,
                timeout=timeout,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info(f"命令执行成功")
                return True
            else:
                logger.error(f"命令执行失败: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"命令执行超时: {' '.join(cmd)}")
            return False
        except Exception as e:
            logger.error(f"命令执行异常: {e}")
            return False

    def _restart_systemd_service(self, service_name: str) -> bool:
        """重启systemd服务"""
        try:
            # 重启服务
            if not self._run_command(["sudo", "systemctl", "restart", service_name], Path.cwd()):
                return False

            # 检查状态
            if not self._run_command(["sudo", "systemctl", "is-active", service_name], Path.cwd()):
                return False

            logger.info(f"SystemD服务 {service_name} 重启成功")
            return True

        except Exception as e:
            logger.error(f"重启SystemD服务失败: {e}")
            return False

    def _restart_process_manager(self, service: str) -> bool:
        """重启进程管理器中的服务"""
        try:
            # 使用pm2或supervisor等进程管理器
            if self.deploy_config.get("process_manager") == "pm2":
                return self._run_command(["pm2", "restart", service], project_root)
            elif self.deploy_config.get("process_manager") == "supervisor":
                return self._run_command(["supervisorctl", "restart", service], project_root)
            else:
                logger.warning("未配置进程管理器")
                return True

        except Exception as e:
            logger.error(f"重启进程管理器服务失败: {e}")
            return False

    def _health_check_backend(self) -> bool:
        """后端健康检查"""
        try:
            import httpx

            backend_url = self.deploy_config.get("backend_url", "http://localhost:8000")
            health_url = f"{backend_url}/api/health"

            # 等待服务启动
            time.sleep(10)

            with httpx.Client(timeout=30) as client:
                response = client.get(health_url)
                if response.status_code == 200:
                    logger.info("后端健康检查通过")
                    return True
                else:
                    logger.error(f"后端健康检查失败: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"后端健康检查异常: {e}")
            return False

    def _health_check_frontend(self) -> bool:
        """前端健康检查"""
        try:
            import httpx

            frontend_url = self.deploy_config.get("frontend_url", "http://localhost:3000")

            # 等待服务启动
            time.sleep(10)

            with httpx.Client(timeout=30) as client:
                response = client.get(frontend_url)
                if response.status_code == 200:
                    logger.info("前端健康检查通过")
                    return True
                else:
                    logger.error(f"前端健康检查失败: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"前端健康检查异常: {e}")
            return False

    def _backup_database(self) -> bool:
        """备份数据库"""
        try:
            backup_dir = project_root / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"backup_{timestamp}.sql"

            # 根据数据库类型执行备份命令
            db_config = self.deploy_config.get("database", {})
            db_type = db_config.get("type", "postgresql")

            if db_type == "postgresql":
                cmd = [
                    "pg_dump",
                    f"--host={db_config['host']}",
                    f"--port={db_config['port']}",
                    f"--username={db_config['username']}",
                    f"--dbname={db_config['database']}",
                    f"--file={backup_file}"
                ]
            elif db_type == "mysql":
                cmd = [
                    "mysqldump",
                    f"--host={db_config['host']}",
                    f"--port={db_config['port']}",
                    f"--user={db_config['username']}",
                    f"--password={db_config['password']}",
                    db_config['database'],
                    "--result-file", str(backup_file)
                ]
            else:
                logger.error(f"不支持的数据库类型: {db_type}")
                return False

            if self._run_command(cmd, Path.cwd()):
                logger.info(f"数据库备份成功: {backup_file}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False

    def _run_sql_file(self, sql_file: Path) -> bool:
        """运行SQL文件"""
        try:
            db_config = self.deploy_config.get("database", {})
            db_type = db_config.get("type", "postgresql")

            if db_type == "postgresql":
                cmd = [
                    "psql",
                    f"--host={db_config['host']}",
                    f"--port={db_config['port']}",
                    f"--username={db_config['username']}",
                    f"--dbname={db_config['database']}",
                    f"--file={sql_file}"
                ]
            elif db_type == "mysql":
                cmd = [
                    "mysql",
                    f"--host={db_config['host']}",
                    f"--port={db_config['port']}",
                    f"--user={db_config['username']}",
                    f"--password={db_config['password']}",
                    db_config['database'],
                    "--execute", f"source {sql_file}"
                ]
            else:
                logger.error(f"不支持的数据库类型: {db_type}")
                return False

            return self._run_command(cmd, Path.cwd())

        except Exception as e:
            logger.error(f"执行SQL文件失败: {e}")
            return False

    def _verify_database(self) -> bool:
        """验证数据库"""
        try:
            # 检查关键表是否存在
            db_config = self.deploy_config.get("database", {})
            db_type = db_config.get("type", "postgresql")

            if db_type == "postgresql":
                cmd = [
                    "psql",
                    f"--host={db_config['host']}",
                    f"--port={db_config['port']}",
                    f"--username={db_config['username']}",
                    f"--dbname={db_config['database']}",
                    "--command", "SELECT COUNT(*) FROM tools LIMIT 1;"
                ]
            elif db_type == "mysql":
                cmd = [
                    "mysql",
                    f"--host={db_config['host']}",
                    f"--port={db_config['port']}",
                    f"--user={db_config['username']}",
                    f"--password={db_config['password']}",
                    db_config['database'],
                    "--execute", "SELECT COUNT(*) FROM tools LIMIT 1;"
                ]

            return self._run_command(cmd, Path.cwd())

        except Exception as e:
            logger.error(f"数据库验证失败: {e}")
            return False

    def _log_deploy_step(self, component: str, status: str, message: str):
        """记录部署步骤"""
        step = {
            "component": component,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.deploy_log.append(step)

    def _generate_deploy_report(self, success_count: int, total_count: int):
        """生成部署报告"""
        report = {
            "deployment": {
                "environment": self.environment,
                "timestamp": datetime.now().isoformat(),
                "success_count": success_count,
                "total_count": total_count,
                "success_rate": f"{(success_count/total_count)*100:.1f}%",
                "status": "success" if success_count == total_count else "partial_failure"
            },
            "steps": self.deploy_log
        }

        # 保存报告
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)

        report_file = reports_dir / f"deploy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"部署报告已保存: {report_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="部署脚本")
    parser.add_argument("--backend", action="store_true", help="部署后端")
    parser.add_argument("--frontend", action="store_true", help="部署前端")
    parser.add_argument("--database", action="store_true", help="部署数据库")
    parser.add_argument("--all", action="store_true", help="部署所有服务")
    parser.add_argument("--env", choices=["production", "staging"],
                       default="production", help="部署环境")

    args = parser.parse_args()

    # 创建日志目录
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # 验证参数
    if not any([args.backend, args.frontend, args.database, args.all]):
        parser.print_help()
        sys.exit(1)

    # 执行部署
    deployer = Deployer(environment=args.env)
    success = True

    if args.all:
        success = deployer.deploy_all()
    else:
        if args.backend:
            success &= deployer.deploy_backend()
        if args.frontend:
            success &= deployer.deploy_frontend()
        if args.database:
            success &= deployer.deploy_database()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()