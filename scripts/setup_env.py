#!/usr/bin/env python3
"""
环境变量设置脚本 - 快速配置开发和生产环境
用法: python setup_env.py [--env=development|production|staging] [--interactive]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

# 项目根目录
project_root = Path(__file__).parent.parent


class EnvironmentSetup:
    """环境配置管理器"""

    def __init__(self):
        self.templates = {
            "development": {
                "OPENAI_API_KEY": "your-openai-api-key-here",
                "OPENAI_MODEL": "gpt-4o",
                "SUPABASE_URL": "your-supabase-url-here",
                "SUPABASE_KEY": "your-supabase-anon-key-here",
                "NEXT_PUBLIC_SUPABASE_URL": "your-supabase-url-here",
                "NEXT_PUBLIC_SUPABASE_ANON_KEY": "your-supabase-anon-key-here",
                "REDDIT_CLIENT_ID": "",
                "REDDIT_CLIENT_SECRET": "",
                "DEBUG": "true",
                "LOG_LEVEL": "DEBUG",
                "CRON_SCHEDULE": "0 9 * * *",
                "DATA_SOURCE_LIMIT": "20"
            },
            "production": {
                "OPENAI_API_KEY": "",
                "OPENAI_MODEL": "gpt-4o",
                "SUPABASE_URL": "",
                "SUPABASE_KEY": "",
                "NEXT_PUBLIC_SUPABASE_URL": "",
                "NEXT_PUBLIC_SUPABASE_ANON_KEY": "",
                "REDDIT_CLIENT_ID": "",
                "REDDIT_CLIENT_SECRET": "",
                "DEBUG": "false",
                "LOG_LEVEL": "INFO",
                "CRON_SCHEDULE": "0 9 * * *",
                "DATA_SOURCE_LIMIT": "50"
            },
            "staging": {
                "OPENAI_API_KEY": "",
                "OPENAI_MODEL": "gpt-4o",
                "SUPABASE_URL": "",
                "SUPABASE_KEY": "",
                "NEXT_PUBLIC_SUPABASE_URL": "",
                "NEXT_PUBLIC_SUPABASE_ANON_KEY": "",
                "REDDIT_CLIENT_ID": "",
                "REDDIT_CLIENT_SECRET": "",
                "DEBUG": "true",
                "LOG_LEVEL": "DEBUG",
                "CRON_SCHEDULE": "0 */6 * * *",  # 每6小时
                "DATA_SOURCE_LIMIT": "30"
            }
        }

    def setup_environment(self, env: str, interactive: bool = False) -> bool:
        """设置环境变量"""
        print(f"🚀 开始设置 {env} 环境...")

        # 获取环境模板
        template = self.templates.get(env)
        if not template:
            print(f"❌ 不支持的环境: {env}")
            return False

        # 创建环境变量字典
        env_vars = template.copy()

        if interactive:
            env_vars = self._interactive_setup(env_vars)

        # 创建 .env 文件
        env_file = project_root / ".env"
        env_example_file = project_root / ".env.example"

        # 备份现有 .env 文件
        if env_file.exists():
            backup_file = project_root / f".env.backup.{int(time.time())}"
            env_file.rename(backup_file)
            print(f"📁 现有 .env 文件已备份为: {backup_file}")

        # 写入 .env 文件
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(f"# AutoSaaS Radar Environment Variables\n")
                f.write(f"# Environment: {env}\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")

                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")

            print(f"✅ .env 文件已创建: {env_file}")

            # 更新 .env.example
            with open(env_example_file, 'w', encoding='utf-8') as f:
                f.write(f"# AutoSaaS Radar Environment Variables (Example)\n")
                f.write(f"# Copy this file to .env and fill in your values\n\n")

                for key, value in template.items():
                    example_value = "your-value-here" if not value else value
                    f.write(f"{key}={example_value}\n")

            print(f"✅ .env.example 文件已更新: {env_example_file}")

            # 设置 Vercel 环境变量
            self._setup_vercel_env(env_vars, env)

            # 验证配置
            self._validate_config(env_vars, env)

            return True

        except Exception as e:
            print(f"❌ 创建环境文件失败: {e}")
            return False

    def _interactive_setup(self, template: Dict) -> Dict:
        """交互式设置"""
        import time

        print("\n📝 交互式环境配置 (按 Enter 使用默认值):")

        env_vars = template.copy()

        # 必需的配置项
        required_configs = [
            {
                "key": "OPENAI_API_KEY",
                "prompt": "OpenAI API Key",
                "required": True,
                "example": "sk-..."
            },
            {
                "key": "SUPABASE_URL",
                "prompt": "Supabase URL",
                "required": True,
                "example": "https://your-project.supabase.co"
            },
            {
                "key": "SUPABASE_KEY",
                "prompt": "Supabase Anonymous Key",
                "required": True,
                "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        ]

        # 可选的配置项
        optional_configs = [
            {
                "key": "REDDIT_CLIENT_ID",
                "prompt": "Reddit Client ID (可选)",
                "required": False
            },
            {
                "key": "REDDIT_CLIENT_SECRET",
                "prompt": "Reddit Client Secret (可选)",
                "required": False
            }
        ]

        all_configs = required_configs + optional_configs

        for config in all_configs:
            key = config["key"]
            prompt = config["prompt"]
            required = config["required"]
            current_value = env_vars[key]

            if required and current_value == "your-openai-api-key-here":
                current_value = ""

            user_input = input(f"  {prompt} [{current_value}]: ").strip()

            if user_input:
                env_vars[key] = user_input
            elif required and not current_value:
                print(f"    ⚠️  {key} 是必需的，请确保稍后手动设置")

        return env_vars

    def _setup_vercel_env(self, env_vars: Dict, env: str):
        """设置 Vercel 环境变量"""
        try:
            print("\n🌐 设置 Vercel 环境变量...")

            # 创建 Vercel 环境变量文件
            vercel_env_file = project_root / "deploy" / "vercel.env"

            with open(vercel_env_file, 'w', encoding='utf-8') as f:
                f.write("# Vercel Environment Variables\n")
                f.write(f"# Environment: {env}\n\n")

                for key, value in env_vars.items():
                    # Vercel 使用下划线命名，转换 NEXT_PUBLIC 变量
                    vercel_key = key
                    if key.startswith("NEXT_PUBLIC_"):
                        vercel_key = key.lower().replace("_", "-")

                    f.write(f"{vercel_key}={value}\n")

            print(f"✅ Vercel 环境变量文件已创建: {vercel_env_file}")

            # 提供设置命令
            print("\n📋 Vercel 环境变量设置命令:")
            for key, value in env_vars.items():
                if value and not value.startswith("your-"):
                    vercel_key = key.lower().replace("_", "-")
                    print(f"  vercel env add {vercel_key} {env}")

        except Exception as e:
            print(f"⚠️  设置 Vercel 环境变量失败: {e}")

    def _validate_config(self, env_vars: Dict, env: str):
        """验证配置"""
        print("\n🔍 验证环境配置...")

        warnings = []

        # 检查必需的配置项
        required_keys = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
        for key in required_keys:
            value = env_vars.get(key, "")
            if not value or value.startswith("your-"):
                warnings.append(f"缺少必需的配置: {key}")

        # 检查格式
        if env_vars.get("OPENAI_API_KEY", "") and not env_vars["OPENAI_API_KEY"].startswith("sk-"):
            warnings.append("OpenAI API Key 格式可能不正确")

        if env_vars.get("SUPABASE_URL", "") and not env_vars["SUPABASE_URL"].startswith("https://"):
            warnings.append("Supabase URL 格式可能不正确")

        # 输出验证结果
        if warnings:
            print("⚠️  配置警告:")
            for warning in warnings:
                print(f"   - {warning}")
        else:
            print("✅ 配置验证通过")

        print("\n📋 配置摘要:")
        print(f"   - 环境: {env}")
        print(f"   - 调试模式: {env_vars.get('DEBUG', 'false')}")
        print(f"   - 日志级别: {env_vars.get('LOG_LEVEL', 'INFO')}")
        print(f"   - 数据源限制: {env_vars.get('DATA_SOURCE_LIMIT', '50')}")

    def create_docker_env(self, env: str):
        """创建 Docker 环境文件"""
        try:
            docker_env_file = project_root / "docker" / ".env"
            docker_env_file.parent.mkdir(exist_ok=True)

            template = self.templates.get(env, self.templates["production"])

            with open(docker_env_file, 'w', encoding='utf-8') as f:
                f.write("# Docker Environment Variables\n")
                for key, value in template.items():
                    f.write(f"{key}={value}\n")

            print(f"✅ Docker 环境文件已创建: {docker_env_file}")

        except Exception as e:
            print(f"⚠️  创建 Docker 环境文件失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="环境变量设置脚本")
    parser.add_argument("--env", choices=["development", "production", "staging"],
                       default="development", help="环境类型")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="交互式设置")
    parser.add_argument("--docker", action="store_true",
                       help="同时创建 Docker 环境文件")

    args = parser.parse_args()

    # 导入时间模块
    from datetime import datetime
    import time

    setup = EnvironmentSetup()

    try:
        success = setup.setup_environment(args.env, args.interactive)

        if success and args.docker:
            setup.create_docker_env(args.env)

        if success:
            print(f"\n🎉 {args.env} 环境设置完成!")
            print("\n📝 下一步:")
            print("1. 检查并更新 .env 文件中的实际值")
            print("2. 运行 'python scripts/quick_test.py --all' 测试配置")
            print("3. 启动开发服务器")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n❌ 设置被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 环境设置失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()