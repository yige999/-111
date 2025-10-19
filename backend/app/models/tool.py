from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class TrendSignal(str, Enum):
    """趋势信号枚举"""
    RISING = "Rising"
    STABLE = "Stable"
    DECLINING = "Declining"


class Category(str, Enum):
    """工具分类枚举"""
    VIDEO = "Video"
    TEXT = "Text"
    PRODUCTIVITY = "Productivity"
    MARKETING = "Marketing"
    EDUCATION = "Education"
    AUDIO = "Audio"
    OTHER = "Other"


class Tool(BaseModel):
    """工具数据模型"""
    id: Optional[int] = None
    tool_name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    category: Optional[Category] = Field(None, description="工具分类")
    votes: int = Field(0, description="投票数")
    link: Optional[HttpUrl] = Field(None, description="工具链接")
    trend_signal: Optional[TrendSignal] = Field(None, description="趋势信号")
    pain_point: Optional[str] = Field(None, description="用户痛点")
    micro_saas_ideas: Optional[List[str]] = Field(default_factory=list, description="Micro SaaS 点子列表")
    date: datetime = Field(default_factory=datetime.utcnow, description="数据日期")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class ToolCreate(BaseModel):
    """创建工具数据模型"""
    tool_name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    votes: int = Field(0, description="投票数")
    link: Optional[str] = Field(None, description="工具链接")
    date: Optional[datetime] = Field(default_factory=datetime.utcnow, description="数据日期")


class ToolUpdate(BaseModel):
    """更新工具数据模型"""
    description: Optional[str] = None
    category: Optional[Category] = None
    votes: Optional[int] = None
    trend_signal: Optional[TrendSignal] = None
    pain_point: Optional[str] = None
    micro_saas_ideas: Optional[List[str]] = None


class ToolResponse(BaseModel):
    """工具响应数据模型"""
    id: int
    tool_name: str
    description: Optional[str]
    category: Optional[Category]
    votes: int
    link: Optional[str]
    trend_signal: Optional[TrendSignal]
    pain_point: Optional[str]
    micro_saas_ideas: Optional[List[str]]
    date: datetime
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class RawToolData(BaseModel):
    """原始抓取的工具数据"""
    tool_name: str
    description: Optional[str]
    votes: int = 0
    link: Optional[str]
    date: datetime
    source: str = Field(..., description="数据源")


class AnalyzedTool(BaseModel):
    """分析后的工具数据"""
    tool_name: str
    category: Category
    trend_signal: TrendSignal
    pain_point: str
    micro_saas_ideas: List[str]