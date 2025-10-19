from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RawTool(BaseModel):
    """原始抓取的工具数据"""
    tool_name: str
    description: str
    votes: int = 0
    link: str
    date: datetime
    category: str = ""


class AnalyzedTool(BaseModel):
    """AI分析后的工具数据"""
    tool_name: str
    category: str
    trend_signal: str  # Rising, Stable, Declining
    pain_point: str
    micro_saas_ideas: List[str]


class Tool(BaseModel):
    """数据库存储的工具数据"""
    id: Optional[int] = None
    tool_name: str
    description: str
    category: str
    votes: int = 0
    link: str
    trend_signal: str
    pain_point: str
    micro_saas_ideas: List[str]
    date: datetime
    created_at: Optional[datetime] = None


class GPTAnalysisResponse(BaseModel):
    """GPT分析响应格式"""
    analyzed_tools: List[AnalyzedTool]


class AnalysisLog(BaseModel):
    """分析日志"""
    id: Optional[int] = None
    date: datetime
    tools_analyzed: int
    tokens_used: int
    cost_usd: float
    status: str  # success, failed, partial
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None