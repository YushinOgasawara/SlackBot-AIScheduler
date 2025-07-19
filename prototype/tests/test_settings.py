"""設定モジュールのテスト"""

import pytest
from pydantic import ValidationError

from config.settings import Settings


def test_settings_validation():
    """設定のバリデーションテスト"""
    # 正常なケース
    settings = Settings(
        SLACK_BOT_TOKEN="xoxb-test",
        SLACK_SIGNING_SECRET="test-secret",
        GEMINI_API_KEY="test-key",
        GOOGLE_CLOUD_PROJECT="test-project"
    )
    assert settings.LOG_LEVEL == "INFO"
    assert settings.SCHEDULE_CONFIDENCE_THRESHOLD == 0.7


def test_log_level_validation():
    """ログレベルのバリデーションテスト"""
    # 無効なログレベル
    with pytest.raises(ValidationError):
        Settings(
            SLACK_BOT_TOKEN="xoxb-test",
            SLACK_SIGNING_SECRET="test-secret", 
            GEMINI_API_KEY="test-key",
            GOOGLE_CLOUD_PROJECT="test-project",
            LOG_LEVEL="INVALID"
        )


def test_confidence_threshold_validation():
    """信頼度閾値のバリデーションテスト"""
    # 範囲外の値
    with pytest.raises(ValidationError):
        Settings(
            SLACK_BOT_TOKEN="xoxb-test",
            SLACK_SIGNING_SECRET="test-secret",
            GEMINI_API_KEY="test-key", 
            GOOGLE_CLOUD_PROJECT="test-project",
            SCHEDULE_CONFIDENCE_THRESHOLD=1.5
        )