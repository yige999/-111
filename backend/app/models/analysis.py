from typing import List, Optional
from pydantic import BaseModel, Field
from .tool import AnalyzedTool


class AnalysisRequest(BaseModel):
    """分析请求模型"""
    tools_data: List[dict] = Field(..., description="待分析的工具数据列表")
    analysis_type: str = Field("full", description="分析类型: full, category_only, trend_only")


class AnalysisResponse(BaseModel):
    """分析响应模型"""
    analyzed_tools: List[AnalyzedTool] = Field(..., description="分析后的工具数据")
    total_processed: int = Field(..., description="处理总数")
    tokens_used: Optional[int] = Field(None, description="使用的Token数量")
    cost_usd: Optional[float] = Field(None, description="成本（美元）")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")


class GPTAnalysisRequest(BaseModel):
    """GPT分析请求模型"""
    tools: List[dict]
    prompt_template: Optional[str] = None


class GPTAnalysisResponse(BaseModel):
    """GPT分析响应模型"""
    analyzed_tools: List[AnalyzedTool]
    usage: Optional[dict] = None