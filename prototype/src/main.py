from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import logging
import os
from typing import Dict, Any

from handlers.slack_handler import SlackHandler
from handlers.schedule_analyzer import ScheduleAnalyzer
from handlers.calendar_handler import CalendarHandler
from config.settings import Settings
from utils.slack_verification import SlackVerification
from utils.logger import setup_logger

app = FastAPI(title="SlackBot-AIScheduler", version="1.0.0")

settings = Settings()
logger = setup_logger()

slack_handler = SlackHandler(settings)
schedule_analyzer = ScheduleAnalyzer(settings)

logger.info("Initializing calendar handler...")
try:
    calendar_handler = CalendarHandler(settings)
    if calendar_handler.calendar_service:
        logger.info("Calendar handler initialized successfully")
    else:
        logger.error("Calendar handler initialized but service is None")
except Exception as e:
    logger.error(f"Failed to initialize calendar handler: {e}", exc_info=True)
    calendar_handler = None

slack_verification = SlackVerification(settings)

@app.get("/")
async def root():
    return {"message": "SlackBot-AIScheduler is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    headers = request.headers
    
    payload = await request.json()
    
    # URL verification は署名検証の前に処理
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}
    
    # 通常のイベントは署名検証を実行
    if not slack_verification.verify_signature(body, headers):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    if payload.get("type") == "event_callback":
        event = payload.get("event", {})
        if event.get("type") == "app_mention":
            background_tasks.add_task(process_mention_event, event)
    
    return {"status": "ok"}

async def process_mention_event(event: Dict[str, Any]):
    try:
        logger.info(f"Processing mention event: {event}")
        
        logger.info("Step 1: Getting thread messages...")
        thread_messages = await slack_handler.get_thread_messages(
            event["channel"], event.get("thread_ts", event["ts"])
        )
        logger.info(f"Step 1 completed: Retrieved {len(thread_messages)} messages")
        
        logger.info("Step 2: Analyzing schedule...")
        schedule_info = await schedule_analyzer.analyze_schedule(thread_messages)
        logger.info(f"Step 2 completed: Schedule analysis result: {schedule_info}")
        
        logger.info(f"Step 3: Checking schedule confidence: {schedule_info.confidence if schedule_info else 'None'}")
        if schedule_info and schedule_info.confidence > 0.7:
            logger.info("Step 3a: Schedule confidence is high, proceeding with calendar creation")
            if calendar_handler is None:
                logger.error("Calendar handler is None, cannot create event")
                await slack_handler.send_error_message(
                    event["channel"],
                    event.get("thread_ts", event["ts"]),
                    "カレンダーサービスが利用できません。"
                )
                return
                
            logger.info("Step 4: Creating calendar event...")
            calendar_event = await calendar_handler.create_event(schedule_info)
            logger.info(f"Step 4 completed: Calendar event created: {calendar_event}")
            
            logger.info("Step 5: Sending success message to Slack...")
            await slack_handler.send_success_message(
                event["channel"],
                event.get("thread_ts", event["ts"]),
                calendar_event
            )
            logger.info("Step 5 completed: Success message sent")
        else:
            logger.info("Step 3b: Schedule confidence is low, sending error message")
            await slack_handler.send_error_message(
                event["channel"],
                event.get("thread_ts", event["ts"]),
                "スケジュールの解析に失敗しました。"
            )
    
    except Exception as e:
        logger.error(f"Error processing mention event: {e}", exc_info=True)
        try:
            await slack_handler.send_error_message(
                event["channel"],
                event.get("thread_ts", event["ts"]),
                f"エラーが発生しました: {str(e)}"
            )
        except Exception as slack_error:
            logger.error(f"Failed to send error message to Slack: {slack_error}", exc_info=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)