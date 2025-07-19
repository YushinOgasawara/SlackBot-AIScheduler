"""カスタム例外クラス"""


class SlackBotError(Exception):
    """SlackBotの基底例外クラス"""
    pass


class SlackAPIError(SlackBotError):
    """Slack API関連のエラー"""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class ScheduleAnalysisError(SlackBotError):
    """スケジュール解析関連のエラー"""
    pass


class CalendarError(SlackBotError):
    """Google Calendar関連のエラー"""
    
    def __init__(self, message: str, calendar_id: str = None):
        super().__init__(message)
        self.calendar_id = calendar_id


class ConfigurationError(SlackBotError):
    """設定関連のエラー"""
    pass


class ValidationError(SlackBotError):
    """バリデーション関連のエラー"""
    pass