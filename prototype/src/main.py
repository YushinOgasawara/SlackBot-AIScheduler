"""SlackBot-AIScheduler メインアプリケーション"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import os
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from handlers.slack_handler import SlackHandler
from handlers.schedule_analyzer import ScheduleAnalyzer
from handlers.calendar_handler import CalendarHandler
from config.settings import get_settings
from utils.slack_verification import SlackVerification
from utils.logger import setup_logger, log_execution_time
from utils.exceptions import SlackBotError, SlackAPIError, CalendarError

# グローバル変数
slack_handler: Optional[SlackHandler] = None
schedule_analyzer: Optional[ScheduleAnalyzer] = None
calendar_handler: Optional[CalendarHandler] = None
slack_verification: Optional[SlackVerification] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の初期化
    await initialize_services()
    yield
    # シャットダウン時のクリーンアップ（必要に応じて）
    pass


async def initialize_services():
    """サービスの初期化"""
    global slack_handler, schedule_analyzer, calendar_handler, slack_verification
    
    settings = get_settings()
    logger = setup_logger()
    
    logger.info(f"Initializing {settings.APP_NAME} v{settings.APP_VERSION}")
    
    try:
        # Slack関連サービスの初期化
        slack_handler = SlackHandler(settings)
        slack_verification = SlackVerification(settings)
        logger.info("Slack services initialized")
        
        # スケジュール解析サービスの初期化
        schedule_analyzer = ScheduleAnalyzer(settings)
        logger.info("Schedule analyzer initialized")
        
        # カレンダーサービスの初期化
        logger.info("Initializing calendar handler...")
        calendar_handler = CalendarHandler(settings)
        if calendar_handler.calendar_service:
            logger.info("Calendar handler initialized successfully")
        else:
            logger.error("Calendar handler initialized but service is None")
            
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise


# FastAPIアプリケーションの作成
settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Slack bot for automatic calendar scheduling",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    settings = get_settings()
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.APP_VERSION,
        "status": "operational"
    }


@app.get("/health")
async def health():
    """ヘルスチェックエンドポイント"""
    # サービスの状態をチェック
    services_status = {
        "slack_handler": slack_handler is not None,
        "schedule_analyzer": schedule_analyzer is not None,
        "calendar_handler": calendar_handler is not None and calendar_handler.calendar_service is not None,
        "slack_verification": slack_verification is not None
    }
    
    all_healthy = all(services_status.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services_status,
        "timestamp": settings.CALENDAR_TIMEZONE
    }

@app.post("/slack/events")
@log_execution_time()
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    """Slackイベントエンドポイント"""
    logger = setup_logger()
    
    try:
        body = await request.body()
        headers = request.headers
        payload = await request.json()
        
        # URL verification は署名検証の前に処理
        if payload.get("type") == "url_verification":
            challenge = payload.get("challenge")
            logger.info(f"URL verification challenge: {challenge}")
            return {"challenge": challenge}
        
        # 署名検証
        if not slack_verification.verify_signature(body, headers):
            logger.warning("Invalid Slack signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # イベントコールバック処理
        if payload.get("type") == "event_callback":
            event = payload.get("event", {})
            if event.get("type") == "app_mention":
                logger.info(f"App mention received: {event.get('ts')}")
                background_tasks.add_task(process_mention_event, event)
            else:
                logger.debug(f"Ignored event type: {event.get('type')}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing Slack event: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail="Internal server error")

@log_execution_time()
async def process_mention_event(event: Dict[str, Any]):
    """メンションイベントの処理"""
    logger = setup_logger()
    settings = get_settings()
    
    channel = event["channel"]
    thread_ts = event.get("thread_ts", event["ts"])
    
    try:
        logger.info(f"Processing mention event: {event.get('ts')}")
        
        # Step 1: スレッドメッセージの取得
        logger.info("Step 1: Getting thread messages...")
        if not slack_handler:
            raise SlackBotError("Slack handler not initialized")
            
        thread_messages = await slack_handler.get_thread_messages(channel, thread_ts)
        logger.info(f"Step 1 completed: Retrieved {len(thread_messages)} messages")
        
        # Step 2: スケジュール解析
        logger.info("Step 2: Analyzing schedule...")
        if not schedule_analyzer:
            raise SlackBotError("Schedule analyzer not initialized")
            
        schedule_info = await schedule_analyzer.analyze_schedule(thread_messages)
        logger.info(f"Step 2 completed: Schedule analysis result: {schedule_info}")
        
        # Step 3: 信頼度チェック
        confidence = schedule_info.confidence if schedule_info else 0.0
        logger.info(f"Step 3: Checking schedule confidence: {confidence}")
        
        if schedule_info and confidence >= settings.SCHEDULE_CONFIDENCE_THRESHOLD:
            logger.info("Step 3a: Schedule confidence is high, proceeding with calendar creation")
            
            # カレンダーハンドラーの確認
            if not calendar_handler or not calendar_handler.calendar_service:
                error_msg = "カレンダーサービスが利用できません。"
                logger.error(error_msg)
                await slack_handler.send_error_message(channel, thread_ts, error_msg)
                return
                
            # Step 4: カレンダーイベント作成
            logger.info("Step 4: Creating calendar event...")
            calendar_event = await calendar_handler.create_event(schedule_info)
            logger.info(f"Step 4 completed: Calendar event created: {calendar_event}")
            
            # Step 5: 成功メッセージ送信
            logger.info("Step 5: Sending success message to Slack...")
            await slack_handler.send_success_message(channel, thread_ts, calendar_event)
            logger.info("Step 5 completed: Success message sent")
            
        else:
            logger.info(f"Step 3b: Schedule confidence is low ({confidence} < {settings.SCHEDULE_CONFIDENCE_THRESHOLD})")
            await slack_handler.send_error_message(
                channel, 
                thread_ts, 
                "スケジュールの解析に失敗しました。もう少し詳細な情報を含めてください。"
            )
            
    except SlackAPIError as e:
        logger.error(f"Slack API error: {e}", exc_info=True)
        error_msg = "Slackとの通信でエラーが発生しました。"
        await _safe_send_error(channel, thread_ts, error_msg)
        
    except CalendarError as e:
        logger.error(f"Calendar error: {e}", exc_info=True)
        error_msg = "カレンダーの操作でエラーが発生しました。"
        await _safe_send_error(channel, thread_ts, error_msg)
        
    except Exception as e:
        logger.error(f"Unexpected error processing mention event: {e}", exc_info=True)
        error_msg = f"予期しないエラーが発生しました: {str(e)}"
        await _safe_send_error(channel, thread_ts, error_msg)


async def _safe_send_error(channel: str, thread_ts: str, message: str):
    """安全にエラーメッセージを送信"""
    logger = setup_logger()
    try:
        if slack_handler:
            await slack_handler.send_error_message(channel, thread_ts, message)
        else:
            logger.error(f"Cannot send error message - slack_handler not available: {message}")
    except Exception as e:
        logger.error(f"Failed to send error message to Slack: {e}", exc_info=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger = setup_logger()
    settings = get_settings()
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} on port {port}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level=settings.LOG_LEVEL.lower()
    )