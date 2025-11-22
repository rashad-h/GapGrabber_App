from twilio.rest import Client
from twilio.request_validator import RequestValidator
from app.config import settings
from typing import Optional

twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
validator = RequestValidator(settings.twilio_auth_token)


def verify_twilio_request(url: str, params: dict, signature: Optional[str]) -> bool:
    """Verify Twilio webhook signature"""
    if not signature:
        return False
    
    return validator.validate(url, params, signature)


async def send_whatsapp_message(to: str, body: str) -> str:
    """Send WhatsApp message via Twilio"""
    try:
        message = twilio_client.messages.create(
            body=body,
            from_=settings.twilio_whatsapp_number,
            to=f"whatsapp:{to}"
        )
        return message.sid
    except Exception as e:
        raise Exception(f"Failed to send WhatsApp message: {str(e)}")

