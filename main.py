import os
import httpx
from fastapi import FastAPI, Request
from hf_client import call_hf_text, call_hf_image

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok", "message": "HF Telegram bot running"}


@app.get("/set_webhook")
async def set_webhook():
    webhook_url = os.getenv("WEBHOOK_URL")
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/setWebhook?url={webhook_url}")
    return r.json()


@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    if "message" not in data:
        return {"status": "ok"}

    msg = data["message"]
    chat_id = msg["chat"]["id"]

    if "text" in msg:
        text = msg["text"]

        if text.startswith("/img"):
            prompt = text.replace("/img", "").strip()
            if prompt == "":
                return await send_message(chat_id, "❗ Usage: /img cat with hat")

            img_b64 = await call_hf_image(prompt)
            if not img_b64:
                return await send_message(chat_id, "⚠️ Image generation failed.")

            await send_photo_b64(chat_id, img_b64)
            return {"status": "ok"}

        # normal text reply
        reply = await call_hf_text(text)
        await send_message(chat_id, reply)

    return {"status": "ok"}


async def send_message(chat_id, text):
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/sendMessage",
                          json={"chat_id": chat_id, "text": text})


async def send_photo_b64(chat_id, image_b64):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{BASE_URL}/sendPhoto",
            data={"chat_id": chat_id},
            files={"photo": ("image.png", base64.b64decode(image_b64))}
        )
