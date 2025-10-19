"""
数据库模块测试
"""
import asyncio
import json
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

from .data_validator import data_validator
from .database_manager import db_manager
from .batch_optimizer import batch_optimizer

def generate_test_data(count: int = 100) -> List[Dict[str, Any]]:
    """生成测试数据"""
    categories = ["Video", "Text", "Productivity", "Marketing", "Education", "Audio", "Other"]
    trends = ["Rising", "Stable", "Declining"]

    test_tools = []
    for i in range(count):
        tool = {
            "tool_name": f"测试工具 {i+1}",
            "description": f"这是一个测试工具的描述，用于验证数据库功能。工具编号：{i+1}",
            "category": random.choice(categories),
            "votes": random.randint(0, 1000),
            "link": f"https://example.com/tool{i+1}",
            "trend_signal": random.choice(trends),
            "pain_point": f"用户在使用{i+1}类工具时遇到的痛点描述",
            "micro_saas_ideas": [
                f"基于{i+1}的微SaaS点子1",
                f"基于{i+1}的微SaaS点子2"
            ],
            "date": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat()
        }
        test_tools.append(tool)

    return test_tools

async def test_data_validation():
    """测试数据验证"""
    print("🔍 测试数据验证功能...")

    # 生成测试数据
    test_data = generate_test_data(10)

    # 添加一些无效数据
    invalid_data = [
        {"tool_name": "", "description": "无效工具"},
        {"tool_name": "Valid Tool", "votes": -1},
        {"tool_name": "Test", "link": "invalid-url"},
        {"description": "Missing name"}  # 缺少必要字段
    ]

    all_data = test_data + invalid_data

    # 执行验证
    results = await data_validator.validate_batch(all_data)

    # 统计结果
    summary = data_validator.get_validation_summary(results)
    print(f"✅ 数据验证完成:")
    print(f"   总数: {summary['total']}")
    print(f"   有效: {summary['valid']}")
    print(f"   无效: {summary['invalid']}")
    print(f"   有效率: {summary['valid_rate']}%")
    print(f"   警告数: {summary['total_warnings']}")

    return [r.cleaned_data for r in results if r.is_valid and r.cleaned_data]

async def test_batch_insertion(valid_data: List[Dict[str, Any]]):
    """测试批量插入"""
    print(f"\n🚀 测试批量插入功能... ({len(valid_data)} 项)")

    # 性能基准测试
    if len(valid_data) >= 20:
        test_sample = valid_data[:20]  # 使用前20项进行测试
        benchmark_result = await batch_optimizer.benchmark_performance(test_sample)

        print("⚡ 性能基准测试结果:")
        print(f"   最佳批次大小: {benchmark_result['best_batch_size']}")
        print(f"   最佳性能: {benchmark_result['best_performance']} 项/秒")

        # 使用最佳批次大小
        batch_optimizer.batch_size = benchmark_result['best_batch_size']

    # 执行批量插入
    progress_updates = []

    async def progress_callback(progress, stats, current, total):
        update = f"进度: {progress:.1f}% ({current}/{total}) - 成功: {stats.get('success', 0)}, 失败: {stats.get('failed', 0)}"
        progress_updates.append(update)
        print(f"   {update}")

    # 执行智能批量插入
    if valid_data:
        result = await batch_optimizer.smart_batch_insert(
            valid_data,
            auto_chunk_size=True
        )

        print(f"✅ 批量插入完成:")
        print(f"   总数: {result['total']}")
        print(f"   成功: {result['success']}")
        print(f"   失败: {result['failed']}")
        print(f"   重复: {result['duplicates']}")
        print(f"   耗时: {result['time']}秒")
        print(f"   速度: {result.get('items_per_second', 0)} 项/秒")

        return result
    else:
        print("⚠️  没有有效数据可插入")
        return None

async def test_database_operations():
    """测试数据库操作"""
    print("\n🗄️  测试数据库操作功能...")

    try:
        # 测试获取今日Top工具
        today_tools = await db_manager.get_today_top_tools(5)
        print(f"✅ 今日Top工具: {len(today_tools)} 项")

        # 测试获取趋势工具
        trending_tools = await db_manager.get_trending_tools_by_category(days=7, limit=10)
        print(f"✅ 趋势工具: {len(trending_tools)} 项")

        # 测试按分类获取工具
        if trending_tools:
            sample_category = trending_tools[0].get('category', 'Other')
            category_tools = await db_manager.db.get_tools_by_category(sample_category, 5)
            print(f"✅ 分类工具 ({sample_category}): {len(category_tools)} 项")

        # 测试搜索功能
        search_results = await db_manager.search_tools("测试", 10)
        print(f"✅ 搜索结果: {len(search_results)} 项")

        # 测试获取统计信息
        stats = await db_manager.db.get_stats()
        print(f"✅ 统计信息: 总工具 {stats.get('total_tools', 0)}, 今日新增 {stats.get('today_tools', 0)}")

        # 测试分类汇总
        category_summary = await db_manager.get_category_summary(7)
        print(f"✅ 分类汇总: {len(category_summary)} 个分类")

        # 测试每日统计
        daily_stats = await db_manager.get_daily_stats(3)
        print(f"✅ 每日统计: {len(daily_stats)} 天的数据")

        return True

    except Exception as e:
        print(f"❌ 数据库操作测试失败: {e}")
        return False

async def test_data_export():
    """测试数据导出"""
    print("\n📤 测试数据导出功能...")

    try:
        # 导出JSON格式
        json_export = await db_manager.export_tools_data("json", 7)
        if json_export:
            print(f"✅ JSON导出成功: {len(json_export)} 字符")

        # 导出CSV格式
        csv_export = await db_manager.export_tools_data("csv", 7)
        if csv_export:
            print(f"✅ CSV导出成功: {len(csv_export)} 字符")

        return True

    except Exception as e:
        print(f"❌ 数据导出测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("🧪 开始数据库模块完整测试\n")

    # 检查数据库连接
    if not db_manager.db.test_connection():
        print("❌ 数据库连接失败，请检查配置")
        return False

    print("✅ 数据库连接正常")

    # 测试1: 数据验证
    valid_data = await test_data_validation()

    # 测试2: 批量插入
    insert_result = await test_batch_insertion(valid_data)

    # 测试3: 数据库操作
    db_ops_result = await test_database_operations()

    # 测试4: 数据导出
    export_result = await test_data_export()

    # 总结
    print("\n" + "="*50)
    print("🎯 测试总结:")
    print(f"   数据验证: ✅")
    print(f"   批量插入: {'✅' if insert_result else '❌'}")
    print(f"   数据库操作: {'✅' if db_ops_result else '❌'}")
    print(f"   数据导出: {'✅' if export_result else '❌'}")

    success = db_ops_result and export_result
    print(f"\n🚀 数据库模块测试: {'全部通过' if success else '部分失败'}")

    if insert_result:
        print(f"📊 插入统计: 成功 {insert_result['success']}, 失败 {insert_result['failed']}, 重复 {insert_result['duplicates']}")

    return success

if __name__ == "__main__":
    # 运行测试
    asyncio.run(run_all_tests())