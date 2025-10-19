"""
分析Prompt模板 - 窗口4
定义所有用于GPT分析的提示词模板
"""

class AnalysisPrompts:
    """分析提示词模板类"""

    CATEGORIES = [
        "Video", "Text", "Productivity", "Marketing",
        "Education", "Audio", "Other"
    ]

    TREND_SIGNALS = ["Rising", "Stable", "Declining"]

    @staticmethod
    def get_analysis_prompt(tools_data):
        """获取主要分析提示词"""
        return f"""你是一个AI趋势分析系统。

输入是一组最新抓取的AI工具，包括名称、描述、点赞数。请分析每个工具并输出JSON数组：

分析要求：
1. 分类工具类型（必须是: {', '.join(AnalysisPrompts.CATEGORIES)} 之一）
2. 提炼用户痛点（简洁明确，不超过20字）
3. 为每个痛点生成1~3个可独立开发的Micro SaaS点子
4. 判断趋势信号（必须是: {', '.join(AnalysisPrompts.TREND_SIGNALS)} 之一）

输入数据: {tools_data}

输出格式（必须是有效的JSON）:
{{
  "analyzed_tools": [
    {{
      "tool_name": "工具名称",
      "category": "类别",
      "trend_signal": "趋势信号",
      "pain_point": "用户痛点",
      "micro_saas_ideas": ["点子1", "点子2"]
    }}
  ]
}}

注意：
- 严格按照输出格式，不要添加任何其他文字
- category必须是预定义的类别之一
- trend_signal必须是Rising/Stable/Declining之一
- pain_point要简洁明确，直击核心痛点
- micro_saas_ideas要具体可执行"""

    @staticmethod
    def get_trend_analysis_prompt(tool, historical_data=None):
        """获取趋势分析提示词"""
        context = ""
        if historical_data:
            context = f"\n历史数据参考: {historical_data}"

        return f"""分析工具趋势信号：{tool['tool_name']}

当前数据：
- 描述: {tool['description']}
- 投票数: {tool['votes']}
- 类别: {tool['category']}
{context}

基于工具描述、投票数和市场趋势，判断趋势信号：
- Rising: 新兴热门，增长迅速
- Stable: 稳定发展，市场成熟
- Declining: 热度下降，需求减少

只返回一个词：Rising、Stable 或 Declining"""

    @staticmethod
    def get_pain_point_extraction_prompt(tool_description):
        """获取痛点提取提示词"""
        return f"""从这个AI工具描述中提炼核心用户痛点：

工具描述: {tool_description}

要求：
- 识别用户真正的问题
- 用20字以内表达
- 直击痛点，避免泛泛而谈

输出格式：{{"pain_point": "用户痛点"}}"""

    @staticmethod
    def get_saas_ideas_prompt(pain_point, tool_category):
        """获取SaaS点子生成提示词"""
        return f"""基于以下信息生成Micro SaaS点子：

用户痛点: {pain_point}
工具类别: {tool_category}

要求：
- 生成1-3个可独立开发的Micro SaaS点子
- 每个点子都要具体可行
- 专注于解决核心痛点
- 避免过于复杂或需要大量资源的点子

输出格式：{{"ideas": ["点子1", "点子2", "点子3"]}}"""

    @staticmethod
    def get_category_classification_prompt(tool_name, tool_description):
        """获取分类提示词"""
        return f"""将AI工具分类到以下类别之一：
{', '.join(AnalysisPrompts.CATEGORIES)}

工具名称: {tool_name}
工具描述: {tool_description}

只返回类别名称，不要其他文字。"""