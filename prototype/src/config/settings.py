import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """アプリケーション設定"""
    
    SLACK_BOT_TOKEN: str = Field(..., env="SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET: str = Field(..., env="SLACK_SIGNING_SECRET")
    
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    
    GOOGLE_CLOUD_PROJECT: str = Field(..., env="GOOGLE_CLOUD_PROJECT")
    GOOGLE_SERVICE_ACCOUNT_FILE: str = Field(
        default="service-account.json", 
        env="GOOGLE_SERVICE_ACCOUNT_FILE"
    )
    GOOGLE_SERVICE_ACCOUNT_KEY: Optional[str] = Field(default=None, env="GOOGLE_SERVICE_ACCOUNT_KEY")
    GOOGLE_CALENDAR_ID: str = Field(default="primary", env="GOOGLE_CALENDAR_ID")
    
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    APP_NAME: str = Field(default="SlackBot-AIScheduler")
    APP_VERSION: str = Field(default="1.0.0")
    
    MAX_THREAD_MESSAGES: int = Field(default=50, env="MAX_THREAD_MESSAGES")
    
    SCHEDULE_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7, 
        env="SCHEDULE_CONFIDENCE_THRESHOLD"
    )
    
    CALENDAR_TIMEZONE: str = Field(default="Asia/Tokyo", env="CALENDAR_TIMEZONE")
    
    SLACK_REQUEST_TIMEOUT: int = Field(default=30, env="SLACK_REQUEST_TIMEOUT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

def get_settings() -> Settings:
    """設定インスタンスを取得"""
    return Settings()