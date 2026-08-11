import os
import requests
from twilio.rest import Client

# Configuration credentials (loaded from environment variables or default mock values)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "YOUR_TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "YOUR_TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# Free Alternative: Telegram Bot API (Ideal for local testing & demos)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")


def send_telegram_alert(message: str) -> bool:
    """Sends instant push alerts via Telegram Bot API (Free)."""
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print(f"[TELEGRAM MOCK]: {message}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"[TELEGRAM ERROR]: {e}")
        return False


def send_sms_twilio(to_phone: str, message: str) -> bool:
    """Sends standard SMS notification via Twilio API."""
    if TWILIO_ACCOUNT_SID == "YOUR_TWILIO_SID":
        print(f"[SMS MOCK to {to_phone}]: {message}")
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(body=message, from_=TWILIO_PHONE_NUMBER, to=to_phone)
        print(f"[SMS SENT SUCCESS] to {to_phone}")
        return True
    except Exception as e:
        print(f"[TWILIO SMS ERROR]: {e}")
        return False


def send_whatsapp_twilio(to_phone: str, message: str) -> bool:
    """Sends WhatsApp message via Twilio Sandbox API."""
    if TWILIO_ACCOUNT_SID == "YOUR_TWILIO_SID":
        print(f"[WHATSAPP MOCK to {to_phone}]: {message}")
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        formatted_to = f"whatsapp:{to_phone}" if not to_phone.startswith("whatsapp:") else to_phone
        client.messages.create(body=message, from_=TWILIO_WHATSAPP_NUMBER, to=formatted_to)
        print(f"[WHATSAPP SENT SUCCESS] to {formatted_to}")
        return True
    except Exception as e:
        print(f"[TWILIO WHATSAPP ERROR]: {e}")
        return False


def send_caretaker_alert(
    patient_id: str,
    medicine_name: str,
    status: str,
    message: str,
    caretaker_phone: str = "+919876543210"
) -> bool:
    """
    Central dispatcher for safety alerts and status updates.
    Fires whenever an unsafe drug or wrong time slot is scanned (RED),
    a warning is issued (YELLOW), or optional confirmation updates are dispatched.
    """
    status_upper = status.upper()

    if status_upper == "RED":
        alert_header = "⚠️ *MEDICATION SAFETY ALERT*"
        status_tag = "🛑 RED (INCORRECT / HAZARD)"
    elif status_upper == "YELLOW":
        alert_header = "⚡ *MEDICATION WARNING*"
        status_tag = "⚠️ YELLOW (WARNING / ALREADY TAKEN)"
    else:
        alert_header = "✅ *MEDICATION UPDATE*"
        status_tag = "🟢 GREEN (CONFIRMED)"

    alert_msg = (
        f"{alert_header}\n\n"
        f"*Patient ID:* {patient_id}\n"
        f"*Scanned Medicine:* {medicine_name}\n"
        f"*Status:* {status_tag}\n"
        f"*Message:* {message}\n"
        f"*Action Required:* Immediate caretaker verification suggested."
    )

    print("\n==================================================")
    print(f"[CARETAKER ALERT TRIGGERED - {status_upper}]:\n{alert_msg}")
    print("==================================================\n")

    # Dispatch across all active communication channels
    telegram_sent = send_telegram_alert(alert_msg)
    whatsapp_sent = send_whatsapp_twilio(caretaker_phone, alert_msg)
    sms_sent = send_sms_twilio(caretaker_phone, alert_msg)

    return telegram_sent or whatsapp_sent or sms_sent