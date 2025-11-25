"""Typed data contracts shared across the application layers."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class KeywordCount(BaseModel):
    word: str = Field(..., description="Keyword token")
    count: int = Field(..., ge=1,
                       description="Count of the keyword in the analyzed text")


class AnalysisResult(BaseModel):
    total_tokens: int = Field(..., ge=0)
    unique_tokens: int = Field(..., ge=0)
    top_keywords: List[KeywordCount] = Field(default_factory=list)


class TelegramAttachment(BaseModel):
    media_type: Optional[str] = Field(
        default=None, description="Underlying Telegram media class name (e.g. Photo, Document)")
    file_name: Optional[str] = Field(
        default=None, description="Original file name if available")
    mime_type: Optional[str] = Field(
        default=None, description="Media MIME type reported by Telegram")
    size_bytes: Optional[int] = Field(
        default=None, ge=0, description="Approximate file size")
    width: Optional[int] = Field(default=None, ge=0)
    height: Optional[int] = Field(default=None, ge=0)
    duration_seconds: Optional[int] = Field(
        default=None, ge=0, description="Duration for audio/video clips")
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="Public URL (served by FastAPI) that points to the cached thumbnail image",
    )
    media_url: Optional[str] = Field(
        default=None,
        description="Public URL for the original media asset when downloaded (images/videos)",
    )


class TelegramMessage(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()})

    message_id: int
    date: datetime
    text: str
    urls: List[str] = Field(default_factory=list)
    attachments: List[TelegramAttachment] = Field(
        default_factory=list, description="Any media or document attachments bundled with the message")


class PageData(BaseModel):
    url: HttpUrl | str
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    content_snippet: Optional[str] = None
    analysis: Optional[AnalysisResult] = None
    error: Optional[str] = None


class CollectedItem(BaseModel):
    telegram: TelegramMessage
    page: PageData


class GlobalAnalysis(BaseModel):
    similarity_matrix: List[List[float]] = Field(default_factory=list)
    most_frequent_keywords: List[KeywordCount] = Field(default_factory=list)


class FinalResponse(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()})

    source: str = Field(default="telegram_group")
    group_id: str
    collected_at: datetime
    items: List[CollectedItem] = Field(default_factory=list)
    messages: List[TelegramMessage] = Field(
        default_factory=list, description="Raw Telegram messages that were inspected")
    global_analysis: GlobalAnalysis
