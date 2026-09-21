import requests
from fastapi import FastAPI, Request

from get_answer_cohere import get_answer_cohere

BOT_TOKEN = "8494944485:AAHrAvgwtepTyPeUCi6Fgw8zsDiPPm99scI"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI()

LAST_UPDATE_ID = -1

@app.post("/telegram")
async def telegram_webhook(req: Request):
    global LAST_UPDATE_ID
    data = await req.json()

    update_id = data.get("update_id", -1)
    if update_id <= LAST_UPDATE_ID:
        return {"status": "duplicate ignored"}

    LAST_UPDATE_ID = update_id

    # Safety check
    if "message" not in data:
        return {"status": "ignored"}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    # Optional: ignore empty messages
    if not text:
        return {"status": "no text"}

    # 🔥 CALL YOUR FUNCTION
    try:
        answer = get_answer_cohere()
    except Exception as e:
        answer = f"Error: {str(e)}"

    # 🔁 Send reply back to Telegram
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": answer
        }
    )

    return {"status": "ok"}
