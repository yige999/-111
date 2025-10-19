import logging
import json
import time
from typing import List, Dict, Optional
from datetime import datetime

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import settings
from ..models.tool import RawToolData, AnalyzedTool, Category, TrendSignal
from ..models.analysis import AnalysisRequest, AnalysisResponse, GPTAnalysisRequest

logger = logging.getLogger(__name__)


class GPTAnalyzer:
    """GPT分析器 - 使用AI分析工具数据并生成洞察"""

    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE

        # 分析提示模板
        self.analysis_prompt = """
你是一个专业的AI趋势分析系统。你的任务是分析最新的AI工具数据，提炼用户痛点，并生成可复制的Micro SaaS点子。

输入是一组最新的AI工具数据，包括工具名称、描述、投票数、链接等。

请仔细分析每个工具，然后输出JSON格式的分析结果：

分析要求：
1. 分类工具类型（必须从以下分类选择）：Video, Text, Productivity, Marketing, Education, Audio, Other
2. 提炼该工具解决的用户痛点
3. 基于痛点生成1-3个可独立开发的Micro SaaS点子
4. 判断趋势信号（Rising/Stable/Declining）

分类说明：
- Video: 视频生成、编辑、处理相关工具
- Text: 文本生成、写作、翻译相关工具
- Productivity: 生产力、效率、自动化工具
- Marketing: 营销、推广、销售工具
- Education: 教育、学习、培训工具
- Audio: 音频生成、编辑、处理工具
- Other: 不属于以上分类的工具

趋势判断标准：
- Rising: 新兴趋势，用户需求增长快
- Stable: 成熟领域，需求稳定
- Declining: 需求下降或已饱和

输入数据：
{tools_data}

输出格式（必须严格按照此JSON格式）：
```json
{{
  "analyzed_tools": [
    {{
      "tool_name": "工具名称",
      "category": "分类",
      "trend_signal": "趋势信号",
      "pain_point": "用户痛点描述",
      "micro_saas_ideas": ["点子1", "点子2", "点子3"]
    }}
  ]
}}
```

注意：
1. 必须返回有效的JSON格式
2. 分类必须从指定的7个分类中选择
3. 趋势信号必须是Rising、Stable或Declining之一
4. 痛点描述要具体，避免空泛
5. Micro SaaS点子要具有可操作性，是独立开发者可以实现的
"""

    async def analyze_tools(self, raw_tools: List[RawToolData]) -> AnalysisResponse:
        """分析原始工具数据"""
        logger.info(f"开始分析 {len(raw_tools)} 个工具数据...")

        start_time = time.time()
        total_processed = 0
        analyzed_tools = []
        tokens_used = 0

        # 分批处理，避免超过token限制
        batch_size = settings.ANALYSIS_BATCH_SIZE
        batches = [raw_tools[i:i + batch_size] for i in range(0, len(raw_tools), batch_size)]

        for i, batch in enumerate(batches):
            logger.info(f"正在处理第 {i + 1}/{len(batches)} 批数据...")

            try:
                batch_result = await self._analyze_batch(batch)
                analyzed_tools.extend(batch_result.analyzed_tools)
                total_processed += len(batch)
                tokens_used += batch_result.tokens_used or 0

            except Exception as e:
                logger.error(f"分析第 {i + 1} 批数据失败: {e}")
                continue

        processing_time = time.time() - start_time
        cost_usd = self._calculate_cost(tokens_used)

        logger.info(f"分析完成: 处理 {total_processed} 个工具，耗时 {processing_time:.2f}s，使用 {tokens_used} tokens")

        return AnalysisResponse(
            analyzed_tools=analyzed_tools,
            total_processed=total_processed,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            processing_time=processing_time
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _analyze_batch(self, tools: List[RawToolData]) -> AnalysisResponse:
        """分析一批工具数据"""
        # 准备输入数据
        tools_data = []
        for tool in tools:
            tools_data.append({
                "tool_name": tool.tool_name,
                "description": tool.description,
                "votes": tool.votes,
                "link": tool.link,
                "source": tool.source
            })

        # 构造提示
        prompt = self.analysis_prompt.format(
            tools_data=json.dumps(tools_data, ensure_ascii=False, indent=2)
        )

        try:
            # 调用OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的AI趋势分析系统。你必须返回有效的JSON格式数据。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            # 解析响应
            content = response.choices[0].message.content
            analysis_result = json.loads(content)

            # 转换为AnalyzedTool对象
            analyzed_tools = []
            for tool_data in analysis_result.get("analyzed_tools", []):
                try:
                    analyzed_tool = AnalyzedTool(
                        tool_name=tool_data["tool_name"],
                        category=Category(tool_data["category"]),
                        trend_signal=TrendSignal(tool_data["trend_signal"]),
                        pain_point=tool_data["pain_point"],
                        micro_saas_ideas=tool_data["micro_saas_ideas"]
                    )
                    analyzed_tools.append(analyzed_tool)
                except Exception as e:
                    logger.warning(f"解析工具数据失败: {e}, 数据: {tool_data}")
                    continue

            return AnalysisResponse(
                analyzed_tools=analyzed_tools,
                total_processed=len(tools),
                tokens_used=response.usage.total_tokens,
                cost_usd=self._calculate_cost(response.usage.total_tokens),
                processing_time=None  # 不在此处计算
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 原始内容: {content}")
            raise
        except Exception as e:
            logger.error(f"GPT分析失败: {e}")
            raise

    def _calculate_cost(self, tokens: int) -> float:
        """计算API调用成本（美元）"""
        # GPT-4o 定价 (2024年1月)
        # Input: $0.005 / 1K tokens
        # Output: $0.015 / 1K tokens
        # 这里使用平均估算
        cost_per_1k_tokens = 0.01
        return (tokens / 1000) * cost_per_1k_tokens

    async def analyze_single_tool(self, tool: RawToolData) -> Optional[AnalyzedTool]:
        """分析单个工具"""
        result = await self.analyze_tools([tool])
        if result.analyzed_tools:
            return result.analyzed_tools[0]
        return None

    async def generate_trend_insights(self, tools: List[AnalyzedTool]) -> Dict[str, any]:
        """生成趋势洞察"""
        logger.info("正在生成趋势洞察...")

        # 统计各类别的数量
        category_stats = {}
        trend_stats = {}
        pain_points = []
        all_ideas = []

        for tool in tools:
            # 类别统计
            category = tool.category.value
            category_stats[category] = category_stats.get(category, 0) + 1

            # 趋势统计
            trend = tool.trend_signal.value
            trend_stats[trend] = trend_stats.get(trend, 0) + 1

            # 收集痛点和点子
            if tool.pain_point:
                pain_points.append(tool.pain_point)
            if tool.micro_saas_ideas:
                all_ideas.extend(tool.micro_saas_ideas)

        # 生成洞察
        insights = {
            "total_tools": len(tools),
            "category_distribution": category_stats,
            "trend_distribution": trend_stats,
            "top_categories": sorted(category_stats.items(), key=lambda x: x[1], reverse=True)[:3],
            "rising_trends": [tool for tool in tools if tool.trend_signal == TrendSignal.RISING][:5],
            "common_pain_points": list(set(pain_points))[:5],
            "popular_saas_ideas": list(set(all_ideas))[:10],
            "generated_at": datetime.utcnow().isoformat()
        }

        return insights

    def get_analysis_prompt(self) -> str:
        """获取分析提示模板"""
        return self.analysis_prompt

    def update_analysis_prompt(self, new_prompt: str):
        """更新分析提示模板"""
        self.analysis_prompt = new_prompt
        logger.info("分析提示模板已更新")