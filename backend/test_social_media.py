#!/usr/bin/env python3
"""
社媒抓取模块测试脚本
测试Reddit和Hacker News抓取器功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.reddit_scraper import RedditScraper
from scrapers.hackernews_scraper import HackerNewsScraper
from scrapers.social_media_collector import SocialMediaCollector

async def test_reddit_scraper():
    """测试Reddit抓取器"""
    print("🔄 测试Reddit抓取器...")
    scraper = RedditScraper()
    try:
        await scraper.initialize()
        result = await scraper.scrape_all_subreddits(3)  # 只抓取3个进行测试
        print(f"✅ Reddit抓取测试成功! 获取到 {len(result)} 个工具")
        for i, tool in enumerate(result[:2], 1):
            print(f"  {i}. {tool.tool_name}")
            print(f"     来源: {tool.source}")
            print(f"     描述: {tool.description[:80]}...")
            print(f"     投票: {tool.votes}")
            print()
        return True
    except Exception as e:
        print(f"❌ Reddit抓取测试失败: {e}")
        return False
    finally:
        await scraper.close()

async def test_hackernews_scraper():
    """测试Hacker News抓取器"""
    print("🔄 测试Hacker News抓取器...")
    scraper = HackerNewsScraper()
    try:
        await scraper.initialize()
        result = await scraper.scrape_hacker_news(3)  # 只抓取3个进行测试
        print(f"✅ Hacker News抓取测试成功! 获取到 {len(result)} 个工具")
        for i, tool in enumerate(result[:2], 1):
            print(f"  {i}. {tool.tool_name}")
            print(f"     来源: {tool.source}")
            print(f"     描述: {tool.description[:80]}...")
            print(f"     投票: {tool.votes}")
            print()
        return True
    except Exception as e:
        print(f"❌ Hacker News抓取测试失败: {e}")
        return False
    finally:
        await scraper.close()

async def test_social_media_collector():
    """测试统一社媒抓取器"""
    print("🔄 测试统一社媒抓取器...")
    collector = SocialMediaCollector()
    try:
        await collector.initialize()
        result = await collector.scrape_all_sources(2)  # 每源只抓取2个
        print(f"✅ 统一社媒抓取测试成功! 总共获取到 {len(result)} 个工具")

        # 统计各数据源
        source_stats = {}
        for tool in result:
            source = tool.source
            source_stats[source] = source_stats.get(source, 0) + 1

        print("📊 数据源统计:")
        for source, count in source_stats.items():
            print(f"  - {source}: {count} 个")

        print("\n🔍 示例工具:")
        for i, tool in enumerate(result[:3], 1):
            print(f"  {i}. {tool.tool_name} ({tool.source})")
            print(f"     {tool.description[:60]}...")
            print()
        return True
    except Exception as e:
        print(f"❌ 统一社媒抓取测试失败: {e}")
        return False
    finally:
        await collector.close()

async def test_connections():
    """测试连接状态"""
    print("🔄 测试社媒数据源连接...")
    collector = SocialMediaCollector()
    try:
        await collector.initialize()
        results = await collector.test_connections()
        print("📡 连接测试结果:")
        for source, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {source}: {'连接成功' if status else '连接失败'}")
        return all(results.values())
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False
    finally:
        await collector.close()

async def main():
    """主测试函数"""
    print("🚀 开始社媒抓取模块完整测试\n")

    tests = [
        ("Reddit抓取器", test_reddit_scraper),
        ("Hacker News抓取器", test_hackernews_scraper),
        ("统一社媒抓取器", test_social_media_collector),
        ("连接测试", test_connections)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"=" * 50)
        result = await test_func()
        results.append((test_name, result))
        print()

    # 总结
    print("=" * 50)
    print("🎯 测试总结:")
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {test_name}")
        if result:
            passed += 1

    print(f"\n📈 总体结果: {passed}/{len(tests)} 测试通过")

    if passed == len(tests):
        print("🎉 所有测试通过！社媒抓取模块工作正常！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)