"""
分析器测试 - 窗口4
测试GPT分析器功能
"""

import asyncio
import json
import os
from datetime import datetime

from .analyzer import AIAnalyzer
from .config import config

async def test_analyzer():
    """测试分析器功能"""
    print("🧪 开始测试AI分析器...")

    # 检查API密钥
    if not config.openai_api_key:
        print("❌ 未设置OPENAI_API_KEY，使用模拟模式")
        return await test_local_analysis()

    try:
        # 初始化分析器
        analyzer = AIAnalyzer(
            api_key=config.openai_api_key,
            model=config.openai_model
        )

        # 测试数据
        test_tools = [
            {
                "tool_name": "AI Resume Builder",
                "description": "Automatically create optimized resumes using AI that pass ATS systems and impress recruiters",
                "votes": 156,
                "link": "https://example.com/ai-resume-builder",
                "date": datetime.now().isoformat()
            },
            {
                "tool_name": "Video Subtitle Generator",
                "description": "Generate accurate subtitles for videos in 50+ languages using advanced speech recognition",
                "votes": 89,
                "link": "https://example.com/video-subtitles",
                "date": datetime.now().isoformat()
            },
            {
                "tool_name": "Meeting Assistant",
                "description": "AI-powered meeting assistant that takes notes, tracks action items, and summarizes key decisions",
                "votes": 234,
                "link": "https://example.com/meeting-assistant",
                "date": datetime.now().isoformat()
            }
        ]

        print(f"📊 测试 {len(test_tools)} 个工具...")

        # 执行分析
        results = await analyzer.analyze_tools(test_tools)

        print(f"✅ 分析完成！")
        print(f"📈 使用统计: {analyzer.get_usage_stats()}")

        # 显示结果
        for i, tool in enumerate(results, 1):
            print(f"\n🔧 工具 {i}: {tool['tool_name']}")
            print(f"   📂 类别: {tool['category']}")
            print(f"   📊 趋势: {tool['trend_signal']}")
            print(f"   💡 痛点: {tool['pain_point']}")
            print(f"   🚀 点子: {', '.join(tool['micro_saas_ideas'])}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_local_analysis():
    """测试本地分析功能"""
    print("🔧 测试本地分析功能...")

    from .trend_detector import TrendDetector

    detector = TrendDetector()

    test_tool = {
        "tool_name": "AI Video Editor",
        "description": "Revolutionary AI-powered video editing tool that automatically creates stunning videos",
        "votes": 150,
        "date": datetime.now().isoformat()
    }

    trend = detector.detect_trend(test_tool)
    print(f"✅ 趋势检测结果: {trend}")

    return True

def run_tests():
    """运行所有测试"""
    print("🚀 开始分析器测试套件...")
    print("=" * 50)

    try:
        result = asyncio.run(test_analyzer())
        if result:
            print("\n🎉 所有测试通过！")
        else:
            print("\n⚠️  部分测试失败，请检查配置")
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")

if __name__ == "__main__":
    run_tests()