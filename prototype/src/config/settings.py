"""アプリケーション設定モジュール"""

from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定
    
    環境変数またはデフォルト値から設定を読み込む
    """
    
    # Slack設定
    SLACK_BOT_TOKEN: str = Field(..., env="SLACK_BOT_TOKEN", description="Slack Bot Token")
    SLACK_SIGNING_SECRET: str = Field(..., env="SLACK_SIGNING_SECRET", description="Slack Signing Secret")
    SLACK_REQUEST_TIMEOUT: int = Field(default=30, env="SLACK_REQUEST_TIMEOUT", description="Slack API Request Timeout")
    
    # Gemini AI設定
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY", description="Gemini API Key")
    
    # Google Cloud設定
    GOOGLE_CLOUD_PROJECT: str = Field(..., env="GOOGLE_CLOUD_PROJECT", description="Google Cloud Project ID")
    GOOGLE_SERVICE_ACCOUNT_FILE: str = Field(
        default="service-account.json", 
        env="GOOGLE_SERVICE_ACCOUNT_FILE",
        description="Service Account JSON File Path"
    )
    GOOGLE_SERVICE_ACCOUNT_KEY: Optional[str] = Field(
        default=None, 
        env="GOOGLE_SERVICE_ACCOUNT_KEY",
        description="Service Account JSON as String"
    )
    GOOGLE_CALENDAR_ID: str = Field(
        default="primary", 
        env="GOOGLE_CALENDAR_ID",
        description="Target Calendar ID (email or 'primary')"
    )
    
    # ログ設定
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL", description="Log Level")
    
    # アプリケーション情報
    APP_NAME: str = Field(default="SlackBot-AIScheduler", description="Application Name")
    APP_VERSION: str = Field(default="1.0.21", description="Application Version")
    
    # 処理設定
    MAX_THREAD_MESSAGES: int = Field(
        default=50, 
        env="MAX_THREAD_MESSAGES",
        description="Maximum Thread Messages to Process"
    )
    SCHEDULE_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7, 
        env="SCHEDULE_CONFIDENCE_THRESHOLD",
        description="Minimum Confidence for Schedule Creation"
    )
    
    # タイムゾーン設定
    CALENDAR_TIMEZONE: str = Field(
        default="Asia/Tokyo", 
        env="CALENDAR_TIMEZONE",
        description="Default Calendar Timezone"
    )
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """ログレベルのバリデーション"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    @validator('SCHEDULE_CONFIDENCE_THRESHOLD')
    def validate_confidence_threshold(cls, v):
        """信頼度閾値のバリデーション"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence threshold must be between 0.0 and 1.0')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'


# シングルトンインスタンス
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """設定インスタンスを取得（シングルトン）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings