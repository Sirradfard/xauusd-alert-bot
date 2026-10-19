import os
import requests


def send_text(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError("Telegram secrets are not configured")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        json={"chat_id": chat_id, "text": message},
        timeout=20,
    )

    response.raise_for_status()

    if not response.json().get("ok"):
        raise RuntimeError("Telegram rejected the message")


def send_alarm(direction, ref_time, ref_high, ref_low, touch_time, zone_low, zone_high):
    message = (
        f"XAUUSD {direction}\n"
        f"H1 reference: {ref_time}\n"
        f"H1 High: {ref_high}\n"
        f"H1 Low: {ref_low}\n"
        f"Touch time: {touch_time}\n"
        f"M3 FVG zone: {zone_low} - {zone_high}\n\n"
        "Analysis alert only. Entry and risk management are manual."
    )

    send_text(message)
