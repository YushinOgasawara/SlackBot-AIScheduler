"""スケジュールモデルのテスト"""

import pytest
from datetime import datetime

from models.schedule_models import ScheduleInfo


def test_schedule_info_creation():
    """ScheduleInfo作成テスト"""
    schedule = ScheduleInfo(
        title="テスト会議",
        start_time=datetime(2025, 7, 18, 19, 0),
        end_time=datetime(2025, 7, 18, 21, 0),
        attendees=["test@example.com"],
        description="テスト用の説明",
        location="会議室A",
        confidence=0.95
    )
    
    assert schedule.title == "テスト会議"
    assert schedule.confidence == 0.95
    assert len(schedule.attendees) == 1


def test_schedule_info_defaults():
    """ScheduleInfoデフォルト値テスト"""
    schedule = ScheduleInfo(
        title="最小限会議",
        start_time=datetime(2025, 7, 18, 19, 0),
        end_time=datetime(2025, 7, 18, 21, 0),
        confidence=0.8
    )
    
    assert schedule.attendees == []
    assert schedule.description == ""
    assert schedule.location == ""


def test_schedule_info_validation():
    """ScheduleInfoバリデーションテスト"""
    # 終了時刻が開始時刻より前の場合
    with pytest.raises(ValueError):
        ScheduleInfo(
            title="無効な会議",
            start_time=datetime(2025, 7, 18, 21, 0),
            end_time=datetime(2025, 7, 18, 19, 0),
            confidence=0.8
        )