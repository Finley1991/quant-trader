import requests
import hashlib
import base64
import hmac
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime

from config import settings


class Notifier:
    def __init__(self):
        self.dingtalk_webhook = settings.DINGTALK_WEBHOOK
        self.dingtalk_secret = settings.DINGTALK_SECRET

    def _generate_dingtalk_sign(self, timestamp: str) -> str:
        secret_enc = self.dingtalk_secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.dingtalk_secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign

    def send_dingtalk(self, title: str, text: str) -> bool:
        if not self.dingtalk_webhook:
            return False

        timestamp = str(round(time.time() * 1000))
        sign = ""

        if self.dingtalk_secret:
            sign = self._generate_dingtalk_sign(timestamp)

        url = self.dingtalk_webhook
        if sign:
            url += f"&timestamp={timestamp}&sign={sign}"

        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"### {title}\n\n{text}"
            }
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        if not settings.EMAIL_SMTP_HOST:
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_USER
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(content, 'plain', 'utf-8'))

            with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.send_message(msg)

            return True
        except Exception:
            return False

    def send_signal_notification(self, signal: Dict[str, Any]) -> bool:
        title = f"【{signal['signal_type']}】{signal['name'] or signal['ts_code']}"
        text = f"""
**股票代码**: {signal['ts_code']}
**股票名称**: {signal.get('name', '-')}
**策略**: {signal['strategy_name']}
**信号类型**: {signal['signal_type']}
**触发价格**: {signal['price']:.2f}
**触发日期**: {signal['date']}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return self.send_dingtalk(title, text)


_notifier: Optional[Notifier] = None

def get_notifier() -> Notifier:
    global _notifier
    if _notifier is None:
        _notifier = Notifier()
    return _notifier
