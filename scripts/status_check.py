#!/usr/bin/env python3
"""
30分钟开发进度检查脚本
窗口1专用 - 快速验证各模块完成状态
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime

class ProjectStatusChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {}

    def check_backend_modules(self):
        """检查后端模块完成状态"""
        backend_path = self.project_root / "backend"

        # 窗口2: RSS抓取模块
        rss_files = [
            "scrapers/producthunt_scraper.py",
            "scrapers/futurepedia_scraper.py",
            "scrapers/rss_manager.py"
        ]

        # 窗口3: 社媒抓取模块
        social_files = [
            "scrapers/reddit_scraper.py",
            "scrapers/hackernews_scraper.py",
            "scrapers/social_media_collector.py"
        ]

        # 窗口4: GPT分析核心
        analyzer_files = [
            "analyzers/gpt_analyzer.py",
            "analyzers/__init__.py"
        ]

        # 窗口5: 数据库模块
        database_files = [
            "app/database/connection.py",
            "app/database/__init__.py"
        ]

        # 窗口6: API接口
        api_files = [
            "app/api/main.py",
            "app/api/__init__.py",
            "app.py"
        ]

        modules = {
            "RSS抓取": rss_files,
            "社媒抓取": social_files,
            "GPT分析": analyzer_files,
            "数据库": database_files,
            "API接口": api_files
        }

        for module_name, files in modules.items():
            completed = all((backend_path / f).exists() for f in files)
            self.results[module_name] = {
                "status": "✅ 完成" if completed else "🟡 进行中",
                "files": files,
                "completed": completed
            }

    def check_frontend_modules(self):
        """检查前端模块完成状态"""
        frontend_path = self.project_root / "frontend"

        # 检查关键文件
        key_files = [
            "package.json",
            "pages/index.js",
            "pages/api/tools.js",
            "components/ToolCard.js",
            "styles/globals.css"
        ]

        completed_files = []
        missing_files = []

        for file in key_files:
            if (frontend_path / file).exists():
                completed_files.append(file)
            else:
                missing_files.append(file)

        self.results["前端模块"] = {
            "status": "✅ 完成" if len(missing_files) == 0 else "🟡 进行中",
            "completed_files": completed_files,
            "missing_files": missing_files,
            "completed": len(missing_files) == 0
        }

    def check_deployment_files(self):
        """检查部署配置文件"""
        deploy_files = [
            "scripts/daily_scan.py",
            "scripts/scheduler.py",
            "scripts/quick_test.py",
            "deploy/vercel.json",
            "Makefile"
        ]

        completed = all((self.project_root / f).exists() for f in deploy_files)
        self.results["部署自动化"] = {
            "status": "✅ 完成" if completed else "🟡 进行中",
            "files": deploy_files,
            "completed": completed
        }

    def generate_status_report(self):
        """生成状态报告"""
        print("🚀 AutoSaaS Radar - 30分钟进度检查报告")
        print("=" * 50)
        print(f"⏰ 检查时间: {datetime.now().strftime('%H:%M:%S')}")
        print()

        total_modules = len(self.results)
        completed_modules = sum(1 for r in self.results.values() if r["completed"])
        progress_percentage = (completed_modules / total_modules) * 100

        for module_name, info in self.results.items():
            print(f"📦 {module_name}: {info['status']}")
            if not info["completed"] and "missing_files" in info:
                print(f"   缺失文件: {', '.join(info['missing_files'])}")
            elif not info["completed"] and "files" in info:
                missing = [f for f in info["files"] if not (self.project_root / "backend" / f).exists()]
                if missing:
                    print(f"   缺失文件: {', '.join(missing)}")

        print()
        print("📊 总体进度:")
        print(f"   完成模块: {completed_modules}/{total_modules}")
        print(f"   进度百分比: {progress_percentage:.1f}%")

        if progress_percentage >= 80:
            print("   状态: 🟢 优秀，可进入集成测试阶段")
        elif progress_percentage >= 60:
            print("   状态: 🟡 良好，继续开发核心功能")
        else:
            print("   状态: 🔴 需要加快开发进度")

        print()
        print("🎯 下一步行动:")
        if progress_percentage >= 80:
            print("   1. 运行集成测试")
            print("   2. 验证数据流完整性")
            print("   3. 准备部署")
        else:
            print("   1. 优先完成未完成模块")
            print("   2. 确保API接口正常")
            print("   3. 前端页面功能验证")

if __name__ == "__main__":
    checker = ProjectStatusChecker()

    print("🔍 检查项目状态...")
    checker.check_backend_modules()
    checker.check_frontend_modules()
    checker.check_deployment_files()

    print()
    checker.generate_status_report()