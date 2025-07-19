import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from config.settings import Settings
from models.schedule_models import ScheduleInfo

logger = logging.getLogger(__name__)

class ScheduleAnalyzer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1
        )
        self.prompt_template = self._create_prompt_template()
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """スケジュール解析用のプロンプトテンプレートを作成"""
        system_message = """
あなたはSlackの会話からスケジュール情報を抽出する専門家です。
以下のルールに従って、会話からスケジュール情報を抽出してください。

## 抽出ルール
1. 会議のタイトルを識別
2. 日時（開始時刻・終了時刻）を特定
3. 参加者を特定
4. 場所があれば抽出
5. 詳細があれば抽出
6. 抽出の信頼度（0.0-1.0）を評価

## 出力形式
以下のJSON形式で出力してください：
```json
{{
    "title": "会議のタイトル",
    "start_time": "2024-01-15T10:00:00",
    "end_time": "2024-01-15T11:00:00",
    "attendees": ["user1@example.com", "user2@example.com"],
    "description": "会議の詳細",
    "location": "場所",
    "confidence": 0.85
}}
```

## 注意事項
- 曖昧な情報は confidence を下げる
- 時刻が不明確な場合は推測しない
- 参加者のメールアドレスが分からない場合は空配列
- スケジュール情報が見つからない場合は null を返す
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "以下のSlack会話からスケジュール情報を抽出してください：\n\n{conversation}")
        ])
    
    async def analyze_schedule(self, messages: List[Dict[str, Any]]) -> Optional[ScheduleInfo]:
        """Slackメッセージからスケジュール情報を解析"""
        try:
            logger.info(f"Starting schedule analysis with {len(messages)} messages")
            logger.info(f"Input messages: {messages}")
            
            conversation = self._format_conversation(messages)
            logger.info(f"Formatted conversation: {conversation}")
            
            chain = self.prompt_template | self.llm
            logger.info("Calling Gemini API...")
            logger.info(f"API Key configured: {bool(self.settings.GEMINI_API_KEY)}")
            
            response = await chain.ainvoke({"conversation": conversation})
            logger.info(f"Gemini response type: {type(response)}")
            logger.info(f"Gemini response content: {response.content}")
            
            schedule_data = self._parse_response(response.content)
            logger.info(f"Parsed schedule data: {schedule_data}")
            
            if schedule_data:
                logger.info("Creating ScheduleInfo object...")
                schedule_info = ScheduleInfo(**schedule_data)
                logger.info(f"ScheduleInfo created: {schedule_info}")
                return schedule_info
            else:
                logger.warning("No schedule data found")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing schedule: {e}", exc_info=True)
            return None
    
    def _format_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """メッセージリストを会話形式に変換"""
        formatted_messages = []
        
        for msg in messages:
            timestamp = datetime.fromtimestamp(float(msg.get("ts", 0)))
            user = msg.get("user", "unknown")
            text = msg.get("text", "")
            
            formatted_messages.append(
                f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {user}: {text}"
            )
        
        return "\n".join(formatted_messages)
    
    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """LLMレスポンスをパース"""
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            
            if data is None:
                return None
            
            data = self._normalize_schedule_data(data)
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return None
    
    def _normalize_schedule_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """スケジュールデータを正規化"""
        normalized = {}
        
        normalized["title"] = data.get("title", "")
        
        start_time = data.get("start_time")
        if start_time:
            normalized["start_time"] = self._parse_datetime(start_time)
        
        end_time = data.get("end_time")
        if end_time:
            normalized["end_time"] = self._parse_datetime(end_time)
        elif start_time:
            start_dt = self._parse_datetime(start_time)
            normalized["end_time"] = start_dt + timedelta(hours=1)
        
        normalized["attendees"] = data.get("attendees", [])
        normalized["description"] = data.get("description", "")
        normalized["location"] = data.get("location", "")
        normalized["confidence"] = float(data.get("confidence", 0.0))
        
        return normalized
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """日時文字列をdatetimeオブジェクトに変換"""
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Error parsing datetime: {e}")
            return datetime.now()
    
    async def validate_schedule(self, schedule_info: ScheduleInfo) -> bool:
        """スケジュール情報の妥当性をチェック"""
        if not schedule_info.title:
            return False
        
        if not schedule_info.start_time or not schedule_info.end_time:
            return False
        
        if schedule_info.start_time >= schedule_info.end_time:
            return False
        
        if schedule_info.confidence < 0.5:
            return False
        
        return True