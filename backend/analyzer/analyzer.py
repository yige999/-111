"""
AI分析器核心 - 窗口4
集成OpenAI API，实现完整的工具分析流程
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import openai
from openai import OpenAI

from .prompts import AnalysisPrompts
from .trend_detector import TrendDetector

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIAnalyzer:
    """AI分析器主类"""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        初始化AI分析器

        Args:
            api_key: OpenAI API密钥
            model: 使用的模型，默认gpt-4o
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompts = AnalysisPrompts()
        self.trend_detector = TrendDetector()

        # 成本跟踪
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0

    async def analyze_tools(self, tools_data: List[Dict]) -> List[Dict]:
        """
        分析工具列表，生成完整的分析结果

        Args:
            tools_data: 原始工具数据列表

        Returns:
            List[Dict]: 分析后的工具数据列表
        """
        if not tools_data:
            logger.warning("没有工具数据需要分析")
            return []

        logger.info(f"开始分析 {len(tools_data)} 个工具")

        try:
            # 1. 使用GPT进行批量分析
            analyzed_tools = await self._batch_analyze_with_gpt(tools_data)

            # 2. 使用本地趋势检测器验证和调整趋势信号
            final_tools = self._enhance_with_local_analysis(analyzed_tools, tools_data)

            # 3. 数据验证和清理
            validated_tools = self._validate_analysis_results(final_tools)

            logger.info(f"成功分析 {len(validated_tools)} 个工具")
            return validated_tools

        except Exception as e:
            logger.error(f"分析工具时出错: {str(e)}")
            # 降级到本地分析
            return self._fallback_local_analysis(tools_data)

    async def _batch_analyze_with_gpt(self, tools_data: List[Dict]) -> List[Dict]:
        """使用GPT进行批量分析"""
        try:
            # 准备输入数据
            input_data = []
            for tool in tools_data:
                input_data.append({
                    "tool_name": tool.get("tool_name", ""),
                    "description": tool.get("description", ""),
                    "votes": tool.get("votes", 0)
                })

            # 调用OpenAI API
            prompt = self.prompts.get_analysis_prompt(json.dumps(input_data, ensure_ascii=False))

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的AI工具趋势分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 降低随机性，确保输出稳定
                max_tokens=4000
            )

            # 更新成本跟踪
            usage = response.usage
            if usage:
                self.total_tokens_used += usage.total_tokens
                # GPT-4o 定价（约）: $0.005/1K input tokens, $0.015/1K output tokens
                cost = (usage.prompt_tokens * 0.005 + usage.completion_tokens * 0.015) / 1000
                self.total_cost_usd += cost

            # 解析响应
            response_text = response.choices[0].message.content.strip()

            # 尝试提取JSON
            try:
                # 清理响应文本，移除可能的markdown格式
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                result = json.loads(response_text)
                analyzed_tools = result.get("analyzed_tools", [])

                logger.info(f"GPT分析完成，生成 {len(analyzed_tools)} 个结果")
                return analyzed_tools

            except json.JSONDecodeError as e:
                logger.error(f"解析GPT响应失败: {e}")
                logger.debug(f"原始响应: {response_text}")
                raise

        except Exception as e:
            logger.error(f"GPT分析失败: {e}")
            raise

    def _enhance_with_local_analysis(self, gpt_results: List[Dict], original_data: List[Dict]) -> List[Dict]:
        """使用本地分析增强GPT结果"""
        enhanced_tools = []

        for i, gpt_tool in enumerate(gpt_results):
            # 获取对应的原始数据
            original_tool = original_data[i] if i < len(original_data) else {}

            # 合并数据
            enhanced_tool = {
                "tool_name": gpt_tool.get("tool_name", original_tool.get("tool_name", "")),
                "description": original_tool.get("description", ""),
                "category": gpt_tool.get("category", "Other"),
                "votes": original_tool.get("votes", 0),
                "link": original_tool.get("link", ""),
                "trend_signal": gpt_tool.get("trend_signal", "Stable"),
                "pain_point": gpt_tool.get("pain_point", ""),
                "micro_saas_ideas": gpt_tool.get("micro_saas_ideas", []),
                "date": original_tool.get("date", datetime.now().isoformat())
            }

            # 使用本地趋势检测器验证趋势信号
            local_trend = self.trend_detector.detect_trend(enhanced_tool)

            # 如果本地和GPT分析结果差异很大，采用本地结果
            if enhanced_tool["trend_signal"] != local_trend:
                logger.info(f"趋势信号调整: {enhanced_tool['tool_name']} {enhanced_tool['trend_signal']} -> {local_trend}")
                enhanced_tool["trend_signal"] = local_trend

            enhanced_tools.append(enhanced_tool)

        return enhanced_tools

    def _validate_analysis_results(self, tools: List[Dict]) -> List[Dict]:
        """验证分析结果"""
        validated_tools = []

        for tool in tools:
            # 必需字段检查
            if not tool.get("tool_name"):
                logger.warning("跳过没有名称的工具")
                continue

            # 类别验证
            if tool.get("category") not in self.prompts.CATEGORIES:
                logger.warning(f"无效类别 {tool.get('category')}，设置为Other")
                tool["category"] = "Other"

            # 趋势信号验证
            if tool.get("trend_signal") not in self.prompts.TREND_SIGNALS:
                logger.warning(f"无效趋势信号 {tool.get('trend_signal')}，设置为Stable")
                tool["trend_signal"] = "Stable"

            # 确保micro_saas_ideas是列表
            if not isinstance(tool.get("micro_saas_ideas"), list):
                tool["micro_saas_ideas"] = []

            # 痛点长度限制
            pain_point = tool.get("pain_point", "")
            if len(pain_point) > 50:
                tool["pain_point"] = pain_point[:50] + "..."

            validated_tools.append(tool)

        return validated_tools

    def _fallback_local_analysis(self, tools_data: List[Dict]) -> List[Dict]:
        """降级到本地分析"""
        logger.warning("使用本地分析作为降级方案")

        analyzed_tools = []
        for tool in tools_data:
            # 基础分类（基于关键词）
            category = self._simple_categorize(tool.get("description", ""))

            # 趋势检测
            trend_signal = self.trend_detector.detect_trend(tool)

            # 简单痛点提取
            pain_point = self._extract_pain_point_simple(tool.get("description", ""))

            # 生成基础点子
            saas_ideas = self._generate_simple_ideas(pain_point, category)

            analyzed_tool = {
                "tool_name": tool.get("tool_name", ""),
                "description": tool.get("description", ""),
                "category": category,
                "votes": tool.get("votes", 0),
                "link": tool.get("link", ""),
                "trend_signal": trend_signal,
                "pain_point": pain_point,
                "micro_saas_ideas": saas_ideas,
                "date": tool.get("date", datetime.now().isoformat())
            }

            analyzed_tools.append(analyzed_tool)

        return analyzed_tools

    def _simple_categorize(self, description: str) -> str:
        """简单分类逻辑"""
        description_lower = description.lower()

        if any(word in description_lower for word in ['video', 'movie', 'youtube', 'tiktok']):
            return "Video"
        elif any(word in description_lower for word in ['text', 'writing', 'content', 'blog']):
            return "Text"
        elif any(word in description_lower for word in ['productivity', 'task', 'management', 'organize']):
            return "Productivity"
        elif any(word in description_lower for word in ['marketing', 'sales', 'promotion', 'ad']):
            return "Marketing"
        elif any(word in description_lower for word in ['education', 'learning', 'course', 'teach']):
            return "Education"
        elif any(word in description_lower for word in ['audio', 'music', 'podcast', 'sound']):
            return "Audio"
        else:
            return "Other"

    def _extract_pain_point_simple(self, description: str) -> str:
        """简单痛点提取"""
        # 这里使用简单的关键词匹配
        # 在实际项目中，可以集成NLP库进行更准确的提取
        pain_indicators = ['difficult', 'hard', 'time-consuming', 'expensive', 'manual']

        description_lower = description.lower()
        for indicator in pain_indicators:
            if indicator in description_lower:
                return f"解决{indicator}问题"

        return "提升效率"

    def _generate_simple_ideas(self, pain_point: str, category: str) -> List[str]:
        """生成简单的SaaS点子"""
        base_ideas = {
            "Video": ["AI视频剪辑工具", "自动字幕生成器", "视频内容优化器"],
            "Text": ["AI写作助手", "内容优化工具", "自动化文案生成器"],
            "Productivity": ["任务管理工具", "时间追踪器", "效率分析仪表盘"],
            "Marketing": ["营销自动化工具", "客户分析平台", "社交媒体管理器"],
            "Education": ["在线学习平台", "智能课程推荐", "学习进度追踪器"],
            "Audio": ["AI音频编辑器", "语音转文字工具", "播客内容优化器"],
            "Other": ["效率提升工具", "自动化解决方案", "智能助手"]
        }

        return base_ideas.get(category, ["智能助手", "效率工具", "自动化方案"])[:2]

    def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "model": self.model
        }

    async def analyze_single_tool(self, tool_data: Dict) -> Dict:
        """分析单个工具"""
        results = await self.analyze_tools([tool_data])
        return results[0] if results else {}