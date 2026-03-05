from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.notifier import get_notifier
from config import settings

router = APIRouter()

class NotifyRequest(BaseModel):
    title: str
    text: str

class SettingsUpdate(BaseModel):
    tushare_token: Optional[str] = None
    dingtalk_webhook: Optional[str] = None
    dingtalk_secret: Optional[str] = None

@router.post("/test")
def test_notification(request: NotifyRequest):
    notifier = get_notifier()
    success = notifier.send_dingtalk(request.title, request.text)
    return {"success": success}

@router.get("/settings")
def get_settings():
    return {
        "tushare_token_set": bool(settings.TUSHARE_TOKEN),
        "dingtalk_webhook_set": bool(settings.DINGTALK_WEBHOOK),
        "dingtalk_secret_set": bool(settings.DINGTALK_SECRET)
    }

@router.post("/settings")
def update_settings(data: SettingsUpdate):
    if data.tushare_token:
        settings.TUSHARE_TOKEN = data.tushare_token
    if data.dingtalk_webhook:
        settings.DINGTALK_WEBHOOK = data.dingtalk_webhook
    if data.dingtalk_secret:
        settings.DINGTALK_SECRET = data.dingtalk_secret

    return {"success": True}
