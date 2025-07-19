import hashlib
import hmac
import time
from typing import Dict, Any
from fastapi import HTTPException

from config.settings import Settings

class SlackVerification:
    """Slack署名検証クラス"""
    
    def __init__(self, settings: Settings):
        self.signing_secret = settings.SLACK_SIGNING_SECRET
    
    def verify_signature(self, body: bytes, headers: Dict[str, str]) -> bool:
        """Slack署名を検証"""
        try:
            timestamp = headers.get('X-Slack-Request-Timestamp')
            signature = headers.get('X-Slack-Signature')
            
            if not timestamp or not signature:
                return False
            
            if abs(time.time() - int(timestamp)) > 60 * 5:
                return False
            
            sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
            
            expected_signature = 'v0=' + hmac.new(
                self.signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception:
            return False