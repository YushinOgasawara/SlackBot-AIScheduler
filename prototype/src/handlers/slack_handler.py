import aiohttp
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.settings import Settings
from models.schedule_models import SlackEvent

logger = logging.getLogger(__name__)

class SlackHandler:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
            "Content-Type": "application/json"
        }
    
    async def get_thread_messages(self, channel: str, thread_ts: str) -> List[Dict[str, Any]]:
        """スレッドのメッセージを取得"""
        logger.info(f"Getting thread messages for channel: {channel}, thread_ts: {thread_ts}")
        url = f"{self.base_url}/conversations.replies"
        params = {
            "channel": channel,
            "ts": thread_ts,
            "inclusive": "true"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                logger.info(f"Making request to: {url} with params: {params}")
                async with session.get(url, headers=self.headers, params=params) as response:
                    data = await response.json()
                    logger.info(f"Slack API response: {data}")
                    
                    if data.get("ok"):
                        messages = data.get("messages", [])
                        logger.info(f"Successfully retrieved {len(messages)} messages")
                        return messages
                    else:
                        logger.error(f"Slack API error: {data.get('error')}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching thread messages: {e}", exc_info=True)
            return []
    
    async def send_success_message(self, channel: str, thread_ts: str, calendar_event: Dict[str, Any]):
        """成功メッセージを送信"""
        message = {
            "channel": channel,
            "thread_ts": thread_ts,
            "text": "✅ スケジュールをカレンダーに登録しました！",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{calendar_event['title']}*\n📅 {calendar_event['start_time']} - {calendar_event['end_time']}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "カレンダーで確認"
                            },
                            "url": calendar_event.get("html_link", "https://calendar.google.com"),
                            "action_id": "view_calendar"
                        }
                    ]
                }
            ]
        }
        
        await self._send_message(message)
    
    async def send_error_message(self, channel: str, thread_ts: str, error: str):
        """エラーメッセージを送信"""
        message = {
            "channel": channel,
            "thread_ts": thread_ts,
            "text": f"❌ {error}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *エラー*\n{error}"
                    }
                }
            ]
        }
        
        await self._send_message(message)
    
    async def _send_message(self, message: Dict[str, Any]):
        """メッセージを送信"""
        url = f"{self.base_url}/chat.postMessage"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=message) as response:
                    data = await response.json()
                    
                    if not data.get("ok"):
                        logger.error(f"Error sending message: {data.get('error')}")
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def get_user_email(self, user_id: str) -> Optional[str]:
        """ユーザーのメールアドレスを取得"""
        url = f"{self.base_url}/users.info"
        params = {"user": user_id}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        return data.get("user", {}).get("profile", {}).get("email")
                    else:
                        logger.error(f"Error getting user info: {data.get('error')}")
                        return None
        
        except Exception as e:
            logger.error(f"Error getting user email: {e}")
            return None