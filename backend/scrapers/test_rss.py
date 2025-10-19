#!/usr/bin/env python3
"""
RSS抓取模块测试脚本
窗口2：RSS 抓取模块测试
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# 添加父目录到路径以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scrapers import (
        fetch_producthunt_tools,
        fetch_futurepedia_tools,
        fetch_ai_tools_from_rss,
        get_rss_sources_info,
        clean_and_validate_tools
    )
    from models import RawTool
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在backend目录中运行此脚本")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_sources():
    """测试单个RSS源抓取"""
    print("\n" + "="*50)
    print("🧪 测试单个RSS源抓取")
    print("="*50)

    # 测试ProductHunt
    print("\n📡 测试 ProductHunt 抓取...")
    try:
        ph_tools = await fetch_producthunt_tools(limit=5)
        print(f"✅ ProductHunt: 抓取到 {len(ph_tools)} 个工具")
        if ph_tools:
            print(f"   示例工具: {ph_tools[0].tool_name[:50]}...")
            print(f"   投票数: {ph_tools[0].votes}")
            print(f"   分类: {ph_tools[0].category}")
    except Exception as e:
        print(f"❌ ProductHunt 抓取失败: {e}")

    # 测试Futurepedia
    print("\n📡 测试 Futurepedia 抓取...")
    try:
        fp_tools = await fetch_futurepedia_tools(limit=5)
        print(f"✅ Futurepedia: 抓取到 {len(fp_tools)} 个工具")
        if fp_tools:
            print(f"   示例工具: {fp_tools[0].tool_name[:50]}...")
            print(f"   投票数: {fp_tools[0].votes}")
            print(f"   分类: {fp_tools[0].category}")
    except Exception as e:
        print(f"❌ Futurepedia 抓取失败: {e}")


async def test_unified_rss():
    """测试统一RSS管理器"""
    print("\n" + "="*50)
    print("🔄 测试统一RSS管理器")
    print("="*50)

    # 获取支持的源
    sources = get_rss_sources_info()
    print(f"📋 支持的RSS源: {list(sources.keys())}")
    for name, desc in sources.items():
        print(f"   - {name}: {desc}")

    # 测试抓取所有源
    print("\n📡 测试所有源抓取...")
    try:
        result = await fetch_ai_tools_from_rss(limit_per_source=3)

        print(f"✅ 整体状态: {'成功' if result['success'] else '失败'}")
        print(f"   总抓取工具: {result.get('total_tools', 0)}")
        print(f"   清洗后工具: {result.get('cleaned_count', 0)}")
        print(f"   抓取时间: {result.get('fetch_time', 'N/A')}")

        # 显示各源状态
        for source_name, source_result in result.get('sources', {}).items():
            status = '✅' if source_result.get('success') else '❌'
            count = source_result.get('tools_count', 0)
            print(f"   {status} {source_name}: {count} 个工具")

        # 显示错误
        if result.get('errors'):
            print(f"\n⚠️  发生错误: {len(result['errors'])} 个")
            for error in result['errors'][:3]:  # 只显示前3个错误
                print(f"   - {error}")

        # 显示清洗后的工具示例
        cleaned_tools = result.get('cleaned_tools', [])
        if cleaned_tools:
            print(f"\n📊 清洗后工具示例:")
            for i, tool in enumerate(cleaned_tools[:3]):
                print(f"   {i+1}. {tool.tool_name[:40]}...")
                print(f"      分类: {tool.category} | 投票: {tool.votes}")
                print(f"      描述: {tool.description[:60]}...")

    except Exception as e:
        print(f"❌ 统一RSS抓取失败: {e}")


async def test_data_cleaning():
    """测试数据清洗功能"""
    print("\n" + "="*50)
    print("🧹 测试数据清洗功能")
    print("="*50)

    # 创建一些测试数据
    test_tools = [
        RawTool(
            tool_name="🚀   AI Writer Pro  -  Best Tool Ever  ",
            description="<p>This is a <strong>great</strong> AI writing tool! It helps you write better content. This tool is amazing and great.</p>",
            votes=150,
            link="https://example.com/ai-writer?utm_source=test&utm_medium=referral",
            date=datetime.now(),
            category="  text generation  "
        ),
        RawTool(
            tool_name="[Product Hunt] Video Creator Suite",
            description="Create amazing videos with AI. This tool helps you create amazing videos.",
            votes=0,
            link="video-creator-suite",  # 不完整URL
            date=datetime.now(),
            category="video editing"
        ),
        RawTool(
            tool_name="",  # 空名称，应该被过滤
            description="Valid description",
            votes=10,
            link="https://valid-tool.com",
            date=datetime.now(),
            category="Productivity"
        )
    ]

    print(f"📝 输入测试数据: {len(test_tools)} 个工具")
    for i, tool in enumerate(test_tools):
        print(f"   {i+1}. 名称: '{tool.tool_name}' | 投票: {tool.votes} | 链接: {tool.link}")

    # 执行清洗
    print("\n🧹 执行数据清洗...")
    try:
        cleaned_tools = clean_and_validate_tools(test_tools)
        print(f"✅ 清洗完成: {len(cleaned_tools)} 个有效工具")

        if cleaned_tools:
            print("\n📊 清洗后结果:")
            for i, tool in enumerate(cleaned_tools):
                print(f"   {i+1}. 名称: '{tool.tool_name}'")
                print(f"      分类: '{tool.category}' | 投票: {tool.votes}")
                print(f"      链接: '{tool.link}'")
                print(f"      描述: '{tool.description[:50]}...'")

    except Exception as e:
        print(f"❌ 数据清洗失败: {e}")


async def main():
    """主测试函数"""
    print("🚀 AutoSaaS Radar - RSS抓取模块测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("👤 窗口2: RSS 抓取模块")

    try:
        # 1. 测试单个源
        await test_single_sources()

        # 2. 测试统一管理器
        await test_unified_rss()

        # 3. 测试数据清洗
        await test_data_cleaning()

        print("\n" + "="*50)
        print("🎉 所有测试完成！")
        print("="*50)

    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 检查是否在正确的目录
    if not os.path.exists("models.py"):
        print("❌ 请在backend目录中运行此脚本")
        sys.exit(1)

    # 运行测试
    asyncio.run(main())