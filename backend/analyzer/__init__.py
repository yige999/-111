"""
GPT分析器模块 - 窗口4
负责：OpenAI API集成、分析Prompt开发、痛点提炼算法、点子生成逻辑
"""
from .analyzer import AIAnalyzer
from .prompts import AnalysisPrompts
from .trend_detector import TrendDetector

__all__ = ['AIAnalyzer', 'AnalysisPrompts', 'TrendDetector']