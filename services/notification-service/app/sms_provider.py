import abc
import os
from typing import Any, Dict, List, Optional
from shared.config import settings
from shared.logging_setup import setup_logger

logger = setup_logger("sms_provider")


class BaseSmsProvider(abc.ABC):
    @abc.abstractmethod
    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """Dispatch SMS notification to target recipient."""
        pass


class MockSmsProvider(BaseSmsProvider):
    """Default zero-credentials SMS provider recording all outgoing dispatches in-memory."""

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        record = {
            "to": to_phone,
            "message": message,
            "status": "delivered_mock",
            "provider": "mock",
        }
        self.sent_messages.append(record)
        logger.info(f"[MOCK SMS] Sent to {to_phone}: {message}")
        return record

    def clear(self):
        self.sent_messages.clear()


class TwilioSmsProvider(BaseSmsProvider):
    """Twilio production provider implementation."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        try:
            import requests

            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            response = requests.post(
                url,
                data={
                    "From": self.from_number,
                    "To": to_phone,
                    "Body": message,
                },
                auth=(self.account_sid, self.auth_token),
                timeout=10,
            )
            data = response.json()
            logger.info(f"Twilio SMS response status: {response.status_code}")
            return {
                "to": to_phone,
                "message_sid": data.get("sid"),
                "status": data.get("status", "sent"),
                "provider": "twilio",
            }
        except Exception as e:
            logger.error(f"Failed to dispatch Twilio SMS: {e}", exc_info=True)
            return {"to": to_phone, "status": "failed", "error": str(e), "provider": "twilio"}


_sms_provider_instance: Optional[BaseSmsProvider] = None


def get_sms_provider() -> BaseSmsProvider:
    global _sms_provider_instance
    if _sms_provider_instance is None:
        provider_name = os.getenv("SMS_PROVIDER", settings.SMS_PROVIDER).lower()
        tw_sid = os.getenv("TWILIO_ACCOUNT_SID")
        tw_token = os.getenv("TWILIO_AUTH_TOKEN")
        tw_from = os.getenv("TWILIO_FROM_PHONE")

        if provider_name == "twilio" and tw_sid and tw_token and tw_from:
            _sms_provider_instance = TwilioSmsProvider(tw_sid, tw_token, tw_from)
        else:
            _sms_provider_instance = MockSmsProvider()
    return _sms_provider_instance
