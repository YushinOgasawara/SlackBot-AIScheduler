"""ロギング設定モジュール"""

import logging
import sys
from typing import Optional
from functools import wraps
import time

from config.settings import get_settings


def setup_logger(name: Optional[str] = None, level: Optional[str] = None) -> logging.Logger:
    """ロガーをセットアップ
    
    Args:
        name: ロガー名（Noneの場合はルートロガー）
        level: ログレベル（Noneの場合は設定から取得）
    
    Returns:
        設定済みのロガーインスタンス
    """
    settings = get_settings()
    logger_name = name or settings.APP_NAME
    log_level = level or settings.LOG_LEVEL
    
    logger = logging.getLogger(logger_name)
    
    # 既にハンドラーが設定されている場合はそのまま返す
    if logger.handlers:
        return logger
    
    # ハンドラーの設定
    handler = logging.StreamHandler(sys.stdout)
    
    # フォーマッターの設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.propagate = False
    
    return logger


def log_execution_time(logger: Optional[logging.Logger] = None):
    """関数の実行時間をログ出力するデコレータ"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            log = logger or logging.getLogger(func.__module__)
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                log.info(f"{func.__name__} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            log = logger or logging.getLogger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                log.info(f"{func.__name__} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        
        # 非同期関数かどうかを判定
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_logger(name: str) -> logging.Logger:
    """名前付きロガーを取得"""
    return setup_logger(name)