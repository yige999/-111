"""
趋势检测器 - 窗口4
基于工具特征和市场数据判断趋势信号
"""

import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class TrendDetector:
    """趋势信号检测器"""

    def __init__(self):
        # 热门关键词权重
        self.hot_keywords = {
            'Rising': [
                'AI', 'GPT', 'ChatGPT', 'OpenAI', 'automatically', 'auto',
                '智能', '自动', 'AI驱动', '智能助手', 'AI助手',
                'new', 'latest', 'innovative', 'breakthrough', 'revolutionary',
                '新', '最新', '创新', '突破', '革命性'
            ],
            'Declining': [
                'deprecated', 'old', 'legacy', 'outdated', 'discontinued',
                '过时', '旧版', '停止维护', 'deprecated'
            ]
        }

        # 投票数阈值
        self.vote_thresholds = {
            'high': 100,    # 高投票数，可能是Rising
            'medium': 50,   # 中等投票数，可能是Stable
            'low': 10       # 低投票数，可能是Declining
        }

    def detect_trend(self, tool_data: Dict, historical_data: Optional[List] = None) -> str:
        """
        检测工具趋势信号

        Args:
            tool_data: 工具数据，包含name, description, votes等
            historical_data: 历史数据（可选）

        Returns:
            str: 趋势信号 ("Rising", "Stable", "Declining")
        """
        # 基础评分
        rising_score = 0
        stable_score = 50  # 默认稳定
        declining_score = 0

        # 1. 投票数分析
        votes = tool_data.get('votes', 0)
        if votes >= self.vote_thresholds['high']:
            rising_score += 30
        elif votes <= self.vote_thresholds['low']:
            declining_score += 20

        # 2. 描述关键词分析
        description = tool_data.get('description', '').lower()
        name = tool_data.get('tool_name', '').lower()
        text_to_analyze = f"{name} {description}"

        # 检查热门关键词
        for keyword in self.hot_keywords['Rising']:
            if keyword.lower() in text_to_analyze:
                rising_score += 15

        # 检查过时关键词
        for keyword in self.hot_keywords['Declining']:
            if keyword.lower() in text_to_analyze:
                declining_score += 25

        # 3. 时间因素分析
        tool_date = tool_data.get('date')
        if tool_date:
            try:
                if isinstance(tool_date, str):
                    tool_date = datetime.fromisoformat(tool_date.replace('Z', '+00:00'))

                days_ago = (datetime.now() - tool_date.replace(tzinfo=None)).days
                if days_ago <= 7:  # 一周内
                    rising_score += 20
                elif days_ago >= 30:  # 一个月前
                    declining_score += 15
            except:
                pass

        # 4. 历史数据对比（如果有）
        if historical_data:
            trend_from_history = self._analyze_historical_trend(tool_data, historical_data)
            if trend_from_history == 'Rising':
                rising_score += 25
            elif trend_from_history == 'Declining':
                declining_score += 25
            else:
                stable_score += 25

        # 5. 特殊模式检测
        if self._is_breakthrough_tool(text_to_analyze):
            rising_score += 20

        # 决策
        if rising_score > stable_score and rising_score > declining_score:
            return "Rising"
        elif declining_score > stable_score:
            return "Declining"
        else:
            return "Stable"

    def _analyze_historical_trend(self, current_tool: Dict, historical_data: List) -> str:
        """分析历史数据趋势"""
        if not historical_data:
            return "Stable"

        # 查找相同或相似工具的历史数据
        similar_tools = []
        current_name = current_tool.get('tool_name', '').lower()

        for tool in historical_data:
            tool_name = tool.get('tool_name', '').lower()
            # 简单的相似度检测
            if any(word in tool_name for word in current_name.split() if len(word) > 2):
                similar_tools.append(tool)

        if not similar_tools:
            return "Stable"

        # 分析投票趋势
        latest_votes = max(tool.get('votes', 0) for tool in similar_tools)
        current_votes = current_tool.get('votes', 0)

        if current_votes > latest_votes * 1.5:
            return "Rising"
        elif current_votes < latest_votes * 0.5:
            return "Declining"
        else:
            return "Stable"

    def _is_breakthrough_tool(self, text: str) -> bool:
        """检测是否为突破性工具"""
        breakthrough_patterns = [
            r'first.*ai.*tool',
            r'worlds first',
            r'breakthrough.*ai',
            r'revolutionary.*approach',
            r'game changer',
            r'paradigm shift'
        ]

        for pattern in breakthrough_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def batch_detect_trends(self, tools_data: List[Dict]) -> List[Dict]:
        """批量检测趋势信号"""
        results = []
        for tool in tools_data:
            trend_signal = self.detect_trend(tool)
            tool_with_trend = tool.copy()
            tool_with_trend['trend_signal'] = trend_signal
            results.append(tool_with_trend)
        return results