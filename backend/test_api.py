"""
API接口测试脚本
简单测试FastAPI服务是否正常运行
"""

import asyncio
import aiohttp
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List


class APITester:
    """API测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get(self, endpoint: str) -> Dict[str, Any]:
        """发送GET请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.get(url) as response:
                return {
                    "status": response.status,
                    "data": await response.json() if response.content_type == "application/json" else await response.text(),
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {
                "status": 0,
                "error": str(e)
            }

    async def post(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送POST请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.post(url, json=data) as response:
                return {
                    "status": response.status,
                    "data": await response.json() if response.content_type == "application/json" else await response.text(),
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {
                "status": 0,
                "error": str(e)
            }

    async def test_root(self):
        """测试根路径"""
        print("🔍 测试根路径...")
        result = await self.get("/")
        if result["status"] == 200:
            print("✅ 根路径正常")
            print(f"   响应: {result['data']}")
        else:
            print(f"❌ 根路径失败: {result}")
        return result["status"] == 200

    async def test_health(self):
        """测试健康检查"""
        print("\n🏥 测试健康检查...")

        # 简单健康检查
        result = await self.get("/api/health/simple")
        if result["status"] == 200:
            print("✅ 简单健康检查正常")
        else:
            print(f"❌ 简单健康检查失败: {result}")

        # 完整健康检查
        result = await self.get("/api/health")
        if result["status"] == 200:
            print("✅ 完整健康检查正常")
            data = result["data"]
            print(f"   服务状态: {data.get('status')}")
            print(f"   组件数量: {len(data.get('components', {}))}")
        else:
            print(f"❌ 完整健康检查失败: {result}")

        return result["status"] == 200

    async def test_tools_endpoints(self):
        """测试工具相关接口"""
        print("\n🛠️ 测试工具接口...")

        success_count = 0
        total_count = 0

        # 测试获取最新工具
        total_count += 1
        result = await self.get("/api/tools/latest?limit=5")
        if result["status"] == 200:
            print("✅ 获取最新工具正常")
            data = result["data"]
            if isinstance(data, list):
                print(f"   返回 {len(data)} 条记录")
            success_count += 1
        else:
            print(f"❌ 获取最新工具失败: {result}")

        # 测试按分类获取
        total_count += 1
        result = await self.get("/api/tools/category/Productivity?limit=5")
        if result["status"] == 200:
            print("✅ 按分类获取工具正常")
            data = result["data"]
            if isinstance(data, list):
                print(f"   返回 {len(data)} 条记录")
            success_count += 1
        else:
            print(f"❌ 按分类获取工具失败: {result}")

        # 测试获取趋势工具
        total_count += 1
        result = await self.get("/api/tools/trending?days=7&limit=5")
        if result["status"] == 200:
            print("✅ 获取趋势工具正常")
            data = result["data"]
            if isinstance(data, list):
                print(f"   返回 {len(data)} 条记录")
            success_count += 1
        else:
            print(f"❌ 获取趋势工具失败: {result}")

        # 测试按日期获取
        total_count += 1
        today = date.today().isoformat()
        result = await self.get(f"/api/tools/date/{today}")
        if result["status"] == 200:
            print("✅ 按日期获取工具正常")
            data = result["data"]
            if isinstance(data, list):
                print(f"   返回 {len(data)} 条记录")
            success_count += 1
        else:
            print(f"❌ 按日期获取工具失败: {result}")

        # 测试搜索
        total_count += 1
        result = await self.get("/api/tools/search?query=AI&limit=5")
        if result["status"] == 200:
            print("✅ 搜索工具正常")
            data = result["data"]
            if isinstance(data, list):
                print(f"   返回 {len(data)} 条记录")
            success_count += 1
        else:
            print(f"❌ 搜索工具失败: {result}")

        # 测试统计信息
        total_count += 1
        result = await self.get("/api/tools/stats?days=7")
        if result["status"] == 200:
            print("✅ 获取统计信息正常")
            data = result["data"]
            print(f"   总工具数: {data.get('total_tools', 0)}")
            success_count += 1
        else:
            print(f"❌ 获取统计信息失败: {result}")

        print(f"\n工具接口测试结果: {success_count}/{total_count} 通过")
        return success_count == total_count

    async def test_version(self):
        """测试版本信息"""
        print("\n📋 测试版本信息...")
        result = await self.get("/api/version")
        if result["status"] == 200:
            print("✅ 版本信息正常")
            data = result["data"]
            print(f"   服务: {data.get('service')}")
            print(f"   版本: {data.get('version')}")
            return True
        else:
            print(f"❌ 版本信息失败: {result}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始API接口测试")
        print("=" * 50)

        start_time = datetime.utcnow()

        tests = [
            ("根路径", self.test_root),
            ("健康检查", self.test_health),
            ("工具接口", self.test_tools_endpoints),
            ("版本信息", self.test_version),
        ]

        passed = 0
        total = len(tests)

        for name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ {name}测试异常: {e}")

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 50)
        print(f"🏁 测试完成")
        print(f"✅ 通过: {passed}/{total}")
        print(f"⏱️ 耗时: {duration:.2f}秒")

        if passed == total:
            print("🎉 所有测试通过！")
        else:
            print("⚠️ 部分测试失败，请检查服务状态")

        return passed == total


async def main():
    """主函数"""
    print("AutoSaaS Radar API 测试工具")
    print("请确保后端服务已启动 (python main.py)")
    print()

    async with APITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())