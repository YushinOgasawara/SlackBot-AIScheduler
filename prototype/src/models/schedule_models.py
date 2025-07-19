from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class ScheduleInfo(BaseModel):
    """スケジュール情報モデル"""
    title: str = Field(..., description="会議タイトル")
    start_time: datetime = Field(..., description="開始時刻")
    end_time: datetime = Field(..., description="終了時刻")
    attendees: List[str] = Field(default_factory=list, description="参加者メールアドレス")
    description: Optional[str] = Field(default="", description="会議詳細")
    location: Optional[str] = Field(default="", description="場所")
    confidence: float = Field(..., description="抽出信頼度", ge=0.0, le=1.0)
    
    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
    
    @validator('confidence')
    def confidence_must_be_valid(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('confidence must be between 0.0 and 1.0')
        return v

class SlackEvent(BaseModel):
    """Slackイベントモデル"""
    type: str = Field(..., description="イベントタイプ")
    channel: str = Field(..., description="チャンネルID")
    user: str = Field(..., description="ユーザーID")
    text: str = Field(..., description="メッセージ内容")
    ts: str = Field(..., description="タイムスタンプ")
    thread_ts: Optional[str] = Field(default=None, description="スレッドタイムスタンプ")
    
    class Config:
        extra = "allow"

class SlackMessage(BaseModel):
    """Slackメッセージモデル"""
    type: str = Field(default="message", description="メッセージタイプ")
    user: str = Field(..., description="ユーザーID")
    text: str = Field(..., description="メッセージ内容")
    ts: str = Field(..., description="タイムスタンプ")
    thread_ts: Optional[str] = Field(default=None, description="スレッドタイムスタンプ")
    
    class Config:
        extra = "allow"

class CalendarEvent(BaseModel):
    """カレンダーイベントモデル"""
    id: str = Field(..., description="イベントID")
    title: str = Field(..., description="イベントタイトル")
    start_time: datetime = Field(..., description="開始時刻")
    end_time: datetime = Field(..., description="終了時刻")
    html_link: str = Field(..., description="イベントへのリンク")
    attendees: List[str] = Field(default_factory=list, description="参加者")
    location: Optional[str] = Field(default="", description="場所")
    description: Optional[str] = Field(default="", description="詳細")

class AnalysisResult(BaseModel):
    """解析結果モデル"""
    success: bool = Field(..., description="解析成功フラグ")
    schedule_info: Optional[ScheduleInfo] = Field(default=None, description="スケジュール情報")
    error_message: Optional[str] = Field(default=None, description="エラーメッセージ")
    processing_time: float = Field(..., description="処理時間（秒）")
    
    class Config:
        extra = "allow"