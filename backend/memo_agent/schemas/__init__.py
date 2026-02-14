"""
速记Agent的数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ClassificationResult(BaseModel):
    """分类结果"""
    primary_category: str = Field(description="主分类")
    secondary_category: str = Field(description="次分类")
    confidence: float = Field(description="置信度", ge=0, le=1)
    reason: str = Field(description="分类理由")


class Tag(BaseModel):
    """标签"""
    name: str = Field(description="标签名称")
    confidence: float = Field(description="置信度", ge=0, le=1)


class Entity(BaseModel):
    """实体"""
    name: str = Field(description="实体名称")
    entity_type: str = Field(description="实体类型（person/organization/technology/concept/location）")
    confidence: float = Field(description="置信度", ge=0, le=1)


class ExtractionResult(BaseModel):
    """提取结果"""
    tags: List[Tag] = Field(description="标签列表")
    entities: List[Entity] = Field(description="实体列表")
    summary: Optional[str] = Field(default=None, description="内容摘要")


class EventAnalysis(BaseModel):
    """事件分析结果"""
    event_type: str = Field(description="事件类型（project/habit/impact/personality/milestone）")
    keywords: List[str] = Field(description="关键词列表")
    time_range: Optional[str] = Field(default=None, description="时间范围")
    priority: str = Field(default="medium", description="优先级（high/medium/low）")
    periodicity: Optional[str] = Field(default=None, description="周期性（daily/weekly/monthly/none）")


class RelationDecision(BaseModel):
    """关联决策"""
    target_id: int = Field(description="目标ID")
    target_type: str = Field(description="目标类型（memo/event）")
    relation_type: str = Field(description="关系类型（RELATED_TO/LINKED_TO/EXTENDS/CONTRADICTS/CAUSED_BY）")
    score: float = Field(description="关联强度评分", ge=0, le=1)
    reason: str = Field(description="关联理由")
    should_link: bool = Field(description="是否应该关联")


class RelationBatchResult(BaseModel):
    """批量关联判定结果"""
    judgments: List[RelationDecision] = Field(description="关联决策列表")


class EventBindingDecision(BaseModel):
    """事件绑定决策"""
    event_id: int = Field(description="事件ID")
    should_bind: bool = Field(description="是否应该绑定")
    binding_strength: float = Field(description="绑定强度", ge=0, le=1)
    binding_reason: str = Field(description="绑定理由")


class EventBindingBatchResult(BaseModel):
    """批量事件绑定结果"""
    decisions: List[EventBindingDecision] = Field(description="绑定决策列表")
    auto_detected_events: List[str] = Field(default_factory=list, description="自动检测到的新事件")
