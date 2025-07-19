import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import Settings
from models.schedule_models import ScheduleInfo

logger = logging.getLogger(__name__)

class CalendarHandler:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.calendar_service = self._build_calendar_service()
    
    def _build_calendar_service(self):
        """Google Calendar API サービスを構築"""
        try:
            logger.info("Building calendar service...")
            logger.info(f"Environment variable GOOGLE_SERVICE_ACCOUNT_KEY exists: {bool(self.settings.GOOGLE_SERVICE_ACCOUNT_KEY)}")
            logger.info(f"Service account file path: {self.settings.GOOGLE_SERVICE_ACCOUNT_FILE}")
            
            # 環境変数からサービスアカウントキーを読み込み
            if self.settings.GOOGLE_SERVICE_ACCOUNT_KEY:
                logger.info("Using service account key from environment variable")
                try:
                    service_account_info = json.loads(self.settings.GOOGLE_SERVICE_ACCOUNT_KEY)
                    logger.info(f"Service account email: {service_account_info.get('client_email')}")
                    credentials = Credentials.from_service_account_info(
                        service_account_info,
                        scopes=['https://www.googleapis.com/auth/calendar']
                    )
                    logger.info("Credentials created from environment variable")
                except Exception as e:
                    logger.error(f"Error parsing service account key from environment: {e}")
                    raise
            else:
                # ファイルから読み込み（ローカル開発用）
                logger.info("Using service account key from file")
                try:
                    credentials = Credentials.from_service_account_file(
                        self.settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                        scopes=['https://www.googleapis.com/auth/calendar']
                    )
                    logger.info("Credentials created from file")
                except Exception as e:
                    logger.error(f"Error loading service account file: {e}")
                    raise
            
            logger.info("Building Google Calendar service with credentials...")
            service = build('calendar', 'v3', credentials=credentials)
            logger.info("Calendar service built successfully")
            
            # テスト用にカレンダー情報を取得してみる
            try:
                calendar = service.calendars().get(calendarId=self.settings.GOOGLE_CALENDAR_ID).execute()
                logger.info(f"Successfully connected to calendar: {calendar.get('summary')} (ID: {self.settings.GOOGLE_CALENDAR_ID})")
            except Exception as e:
                logger.warning(f"Could not test calendar connection for {self.settings.GOOGLE_CALENDAR_ID}: {e}")
            
            return service
            
        except Exception as e:
            logger.error(f"Error building calendar service: {e}", exc_info=True)
            return None
    
    async def create_event(self, schedule_info: ScheduleInfo) -> Dict[str, Any]:
        """カレンダーイベントを作成"""
        try:
            logger.info(f"Creating calendar event for: {schedule_info.title}")
            logger.info(f"Calendar service status: {self.calendar_service is not None}")
            
            # カレンダーサービスが利用できない場合はモックイベントを返す
            if not self.calendar_service:
                logger.info("Calendar service not available, creating mock event")
                return {
                    'id': 'mock_event_id',
                    'title': schedule_info.title,
                    'start_time': schedule_info.start_time.isoformat(),
                    'end_time': schedule_info.end_time.isoformat(),
                    'html_link': 'https://calendar.google.com'
                }
            
            logger.info("Calendar service is available, proceeding with real event creation")
            
            event_data = {
                'summary': schedule_info.title,
                'description': schedule_info.description,
                'start': {
                    'dateTime': schedule_info.start_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': schedule_info.end_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'attendees': [
                    {'email': email} for email in schedule_info.attendees
                ] if schedule_info.attendees else [],
                'location': schedule_info.location,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }
            
            if schedule_info.location:
                event_data['location'] = schedule_info.location
            
            logger.info(f"Event data prepared: {event_data}")
            loop = asyncio.get_event_loop()
            logger.info("Calling Google Calendar API...")
            event = await loop.run_in_executor(
                None, 
                self._create_event_sync, 
                event_data
            )
            logger.info(f"Event created successfully: {event.get('id')}")
            
            return {
                'id': event['id'],
                'title': event['summary'],
                'start_time': event['start']['dateTime'],
                'end_time': event['end']['dateTime'],
                'html_link': event['htmlLink']
            }
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}", exc_info=True)
            raise
    
    def _create_event_sync(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """同期的にイベントを作成"""
        try:
            logger.info("Executing Google Calendar API insert request...")
            event = self.calendar_service.events().insert(
                calendarId=self.settings.GOOGLE_CALENDAR_ID,
                body=event_data
            ).execute()
            
            logger.info(f"Calendar event created successfully: {event.get('htmlLink')}")
            logger.info(f"Event ID: {event.get('id')}")
            return event
            
        except HttpError as error:
            logger.error(f"HTTP error creating event: {error}")
            raise
    
    async def check_availability(self, start_time: datetime, end_time: datetime) -> bool:
        """指定時間帯の空き状況をチェック"""
        try:
            time_min = start_time.isoformat()
            time_max = end_time.isoformat()
            
            loop = asyncio.get_event_loop()
            events = await loop.run_in_executor(
                None,
                self._get_events_sync,
                time_min,
                time_max
            )
            
            return len(events) == 0
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return True
    
    def _get_events_sync(self, time_min: str, time_max: str) -> List[Dict[str, Any]]:
        """同期的にイベントを取得"""
        try:
            events_result = self.calendar_service.events().list(
                calendarId=self.settings.GOOGLE_CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except HttpError as error:
            logger.error(f"HTTP error getting events: {error}")
            return []
    
    async def update_event(self, event_id: str, schedule_info: ScheduleInfo) -> Dict[str, Any]:
        """イベントを更新"""
        try:
            event_data = {
                'summary': schedule_info.title,
                'description': schedule_info.description,
                'start': {
                    'dateTime': schedule_info.start_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': schedule_info.end_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'attendees': [
                    {'email': email} for email in schedule_info.attendees
                ] if schedule_info.attendees else [],
                'location': schedule_info.location,
            }
            
            loop = asyncio.get_event_loop()
            event = await loop.run_in_executor(
                None,
                self._update_event_sync,
                event_id,
                event_data
            )
            
            return {
                'id': event['id'],
                'title': event['summary'],
                'start_time': event['start']['dateTime'],
                'end_time': event['end']['dateTime'],
                'html_link': event['htmlLink']
            }
            
        except Exception as e:
            logger.error(f"Error updating calendar event: {e}")
            raise
    
    def _update_event_sync(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """同期的にイベントを更新"""
        try:
            event = self.calendar_service.events().update(
                calendarId=self.settings.GOOGLE_CALENDAR_ID,
                eventId=event_id,
                body=event_data
            ).execute()
            
            logger.info(f"Calendar event updated: {event.get('htmlLink')}")
            return event
            
        except HttpError as error:
            logger.error(f"HTTP error updating event: {error}")
            raise
    
    async def delete_event(self, event_id: str) -> bool:
        """イベントを削除"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._delete_event_sync,
                event_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting calendar event: {e}")
            return False
    
    def _delete_event_sync(self, event_id: str):
        """同期的にイベントを削除"""
        try:
            self.calendar_service.events().delete(
                calendarId=self.settings.GOOGLE_CALENDAR_ID,
                eventId=event_id
            ).execute()
            
            logger.info(f"Calendar event deleted: {event_id}")
            
        except HttpError as error:
            logger.error(f"HTTP error deleting event: {error}")
            raise