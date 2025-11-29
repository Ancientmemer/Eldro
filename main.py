import os
import base64
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from hf_client import call_hf_text, call_hf_image

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EXPOSED_URL = os.getenv("EXPOSED_URL")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI()

async def send_msg(chat_id, text):
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", data={
            "chat_id": chat_id,
            "text": text
        })

async def send_photo(chat_id, b64_img):
    img_bytes = base64.b64decode(b64_img)
    files = {"photo": ("image.png", img_bytes, "image/png")}
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendPhoto",
                          data={"chat_id": chat_id},
                          files=files)

async def handle_agent(chat_id, text):
    if text.startswith("/img"):
        prompt = text[4:].strip()
        await send_msg(chat_id, "Image generate cheyyunnu...")
        b64 = await call_hf_image(prompt)

        if isinstance(b64, str) and b64.startswith("Image error"):
            await send_msg(chat_id, b64)
        else:
            await send_photo(chat_id, b64)
        return

    # normal chat
    reply = await call_hf_text(text)
    await send_msg(chat_id, reply)

@app.post("/webhook")
async def webhook(req: Request, background_tasks: BackgroundTasks):
    data = await req.json()
    msg = data.get("message", {})
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text", "")

    if not chat_id or not text:
        return {"ok": True}

    background_tasks.add_task(handle_agent, chat_id, text)
    return {"ok": True}

@app.get("/set_webhook")
async def set_webhook():
    if not EXPOSED_URL:
        raise HTTPException(400, "Set EXPOSED_URL first")

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{TELEGRAM_API}/setWebhook",
                                params={"url": f"{EXPOSED_URL}/webhook"})
        return resp.json()
