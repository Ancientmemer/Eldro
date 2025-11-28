# main.py
import os
import base64
from fastapi import FastAPI, Request
import httpx

from hf_client import call_hf_text, call_hf_image

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# -------------------------- TELEGRAM HELPERS --------------------------
async def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": chat_id, "text": text})

async def send_photo(chat_id, image_b64):
    url = f"{BASE_URL}/sendPhoto"
    async with httpx.AsyncClient() as client:
        await client.post(
            url,
            json={
                "chat_id": chat_id,
                "photo": f"data:image/png;base64,{image_b64}"
            },
        )

# -------------------------- WEBHOOK ENDPOINT --------------------------
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    if "message" not in data:
        return {"status": "ok"}

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # /img prompt
    if text.startswith("/img"):
        prompt = text.replace("/img", "").strip()
        await send_message(chat_id, "Generating image... please wait!")

        img_b64 = await call_hf_image(prompt)
        if img_b64:
            await send_photo(chat_id, img_b64)
        else:
            await send_message(chat_id, "Image generation failed.")
        return {"ok": True}

    # Normal text chat
    reply = await call_hf_text(text)
    await send_message(chat_id, reply)

    return {"ok": True}

# -------------------------- WEBHOOK SETUP --------------------------
@app.get("/set_webhook")
async def set_webhook():
    webhook_url = os.getenv("WEBHOOK_URL")
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/setWebhook?url={webhook_url}")
        return r.json()

@app.get("/")
async def root():
    return {"status": "running"}
