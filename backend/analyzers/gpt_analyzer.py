import openai
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import RawTool, AnalyzedTool, GPTAnalysisResponse
from ..config import settings

logger = logging.getLogger(__name__)


class GPTAnalyzer:
    """GPT分析器"""

    def __init__(self, api_key: str = None, model: str = None):
        self.client = openai.OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model or settings.openai_model
        self.categories = [
            "Video", "Text", "Productivity", "Marketing",
            "Education", "Audio", "Other"
        ]
        self.trend_signals = ["Rising", "Stable", "Declining"]

    async def analyze_tools(self, tools: List[RawTool]) -> List[AnalyzedTool]:
        """分析工具列表"""
        if not tools:
            return []

        try:
            # 准备输入数据
            tools_data = []
            for tool in tools:
                tools_data.append({
                    "tool_name": tool.tool_name,
                    "description": tool.description,
                    "votes": tool.votes
                })

            # 构建prompt
            prompt = self._build_analysis_prompt(tools_data)

            # 调用GPT API
            response = await self._call_gpt_analysis(prompt)

            # 解析响应
            analyzed_tools = self._parse_gpt_response(response)

            logger.info(f"成功分析 {len(tools)} 个工具，生成 {len(analyzed_tools)} 个分析结果")
            return analyzed_tools

        except Exception as e:
            logger.error(f"GPT分析失败: {e}")
            return []

    def _build_analysis_prompt(self, tools_data: List[Dict[str, Any]]) -> str:
        """构建分析prompt"""
        tools_json = json.dumps(tools_data, ensure_ascii=False, indent=2)

        prompt = f"""你是一个AI趋势分析系统。

输入是一组最新抓取的AI工具，包括名称、描述、点赞数。

请输出JSON数组，对每个工具进行以下分析：
1. 分类工具类型（必须是以下之一: {", ".join(self.categories)}）
2. 提炼用户痛点
3. 为每个痛点生成1~3个可独立开发的Micro SaaS点子
4. 判断趋势信号（必须是以下之一: {", ".join(self.trend_signals)}）

分类说明：
- Video: 视频相关（编辑、生成、处理等）
- Text: 文本相关（写作、翻译、摘要等）
- Productivity: 生产力工具（效率、协作、管理等）
- Marketing: 营销推广（SEO、社交媒体、邮件等）
- Education: 教育学习（课程、培训、知识管理等）
- Audio: 音频相关（音乐、语音、播客等）
- Other: 其他类别

趋势信号判断标准：
- Rising: 新兴趋势，投票数较高，描述中包含"新"、"首次"、"AI"等关键词
- Stable: 稳定需求，投票数中等，描述中包含"工具"、"平台"、"服务"等
- Declining: 下降趋势，投票数较低，描述中包含"旧"、"传统"、"基础"等

输入数据:
{tools_json}

输出格式（必须是有效的JSON）:
{{
  "analyzed_tools": [
    {{
      "tool_name": "工具名称",
      "category": "类别",
      "trend_signal": "Rising/Stable/Declining",
      "pain_point": "用户痛点",
      "micro_saas_ideas": ["点子1", "点子2"]
    }}
  ]
}}"""

        return prompt

    async def _call_gpt_analysis(self, prompt: str) -> str:
        """调用GPT分析API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的AI趋势分析师，擅长从AI工具中提炼用户痛点和商业机会。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # 降低随机性
                max_tokens=4000   # 增加token限制
            )

            content = response.choices[0].message.content
            logger.info(f"GPT分析完成，使用了 {response.usage.total_tokens} tokens")
            return content.strip()

        except openai.APIError as e:
            logger.error(f"OpenAI API错误: {e}")
            raise
        except Exception as e:
            logger.error(f"调用GPT分析失败: {e}")
            raise

    def _parse_gpt_response(self, response: str) -> List[AnalyzedTool]:
        """解析GPT响应"""
        try:
            # 尝试直接解析JSON
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            data = json.loads(response)
            analyzed_tools = []

            for item in data.get("analyzed_tools", []):
                # 验证必要字段
                if not all(key in item for key in ["tool_name", "category", "trend_signal", "pain_point"]):
                    logger.warning(f"跳过不完整的分析结果: {item}")
                    continue

                # 验证枚举值
                if item["category"] not in self.categories:
                    logger.warning(f"无效的类别: {item['category']}")
                    item["category"] = "Other"

                if item["trend_signal"] not in self.trend_signals:
                    logger.warning(f"无效的趋势信号: {item['trend_signal']}")
                    item["trend_signal"] = "Stable"

                # 确保ideas是列表
                ideas = item.get("micro_saas_ideas", [])
                if not isinstance(ideas, list):
                    ideas = [str(ideas)]

                analyzed_tool = AnalyzedTool(
                    tool_name=item["tool_name"],
                    category=item["category"],
                    trend_signal=item["trend_signal"],
                    pain_point=item["pain_point"],
                    micro_saas_ideas=ideas[:3]  # 限制最多3个点子
                )
                analyzed_tools.append(analyzed_tool)

            return analyzed_tools

        except json.JSONDecodeError as e:
            logger.error(f"GPT响应JSON解析失败: {e}")
            logger.error(f"原始响应: {response}")
            return []
        except Exception as e:
            logger.error(f"解析GPT响应失败: {e}")
            return []

    def calculate_cost(self, tokens_used: int) -> float:
        """计算API成本（以美元为单位）"""
        # GPT-4o定价 (2024年1月)
        input_price = 0.005  # per 1K input tokens
        output_price = 0.015  # per 1K output tokens

        # 假设输入token占70%，输出token占30%
        input_tokens = int(tokens_used * 0.7)
        output_tokens = int(tokens_used * 0.3)

        cost = (input_tokens * input_price / 1000) + (output_tokens * output_price / 1000)
        return round(cost, 4)

    async def analyze_batch(self, tools_batch: List[RawTool]) -> Dict[str, Any]:
        """批量分析工具"""
        start_time = datetime.now()

        try:
            analyzed_tools = await self.analyze_tools(tools_batch)

            # 估算token使用量（简化计算）
            estimated_tokens = len(tools_batch) * 200 + len(analyzed_tools) * 300

            # 计算成本
            cost = self.calculate_cost(estimated_tokens)

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            return {
                "status": "success",
                "analyzed_tools": analyzed_tools,
                "tools_count": len(tools_batch),
                "analyzed_count": len(analyzed_tools),
                "tokens_used": estimated_tokens,
                "cost_usd": cost,
                "processing_time_seconds": processing_time
            }

        except Exception as e:
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            return {
                "status": "failed",
                "error": str(e),
                "tools_count": len(tools_batch),
                "analyzed_count": 0,
                "tokens_used": 0,
                "cost_usd": 0,
                "processing_time_seconds": processing_time
            }


async def analyze_tools_with_gpt(tools: List[RawTool]) -> List[AnalyzedTool]:
    """便捷函数：使用GPT分析工具"""
    analyzer = GPTAnalyzer()
    return await analyzer.analyze_tools(tools)