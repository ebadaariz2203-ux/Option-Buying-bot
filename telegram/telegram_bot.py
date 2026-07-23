import requests

BOT_TOKEN = "8919072183:AAGl5NAugNtiRXrn8BgVBxHPyzT_JoY8swY"
CHAT_ID = "8357526173"


def send_telegram_message(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=data)

    return response.status_code