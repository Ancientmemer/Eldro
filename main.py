# main.py
import os
import base64
import traceback
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
import httpx

from hf_client import hf_text, hf_image

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
EXPOSED_URL = os.getenv("EXPOSED_URL", "")
PORT = int(os.getenv("PORT", "8080"))

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN env var")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

app = FastAPI()

async def send_msg(chat_id: int, text: str):
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": text})

async def send_photo_b64(chat_id: int, b64: str, caption: str = ""):
    # Telegram sendPhoto with multipart requires bytes
    img_bytes = base64.b64decode(b64)
    files = {"photo": ("image.png", img_bytes, "image/png")}
    data = {"chat_id": str(chat_id), "caption": caption}
    async with httpx.AsyncClient(timeout=60.0) as client:
        await client.post(f"{TELEGRAM_API}/sendPhoto", data=data, files=files)

async def send_photo_url(chat_id: int, url: str, caption: str = ""):
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(f"{TELEGRAM_API}/sendPhoto", data={"chat_id": chat_id, "photo": url, "caption": caption})

async def handle_agent(chat_id: int, text: str):
    text = (text or "").strip()
    if not text:
        return
    # image command
    if text.lower().startswith("/img") or text.lower().startswith("/image"):
        prompt = text.split(" ", 1)[1] if " " in text else "A creative scene"
        await send_msg(chat_id, "Image generate cheyyunnundu...")
        try:
            res = await hf_image(prompt)
            if not res:
                await send_msg(chat_id, "Image API illa or error. I'll send a textual description instead.")
                descr = await hf_text(f"Describe a scene: {prompt}")
                await send_msg(chat_id, descr)
                return
            if res.get("url"):
                await send_photo_url(chat_id, res["url"], caption=prompt)
            elif res.get("b64"):
                await send_photo_b64(chat_id, res["b64"], caption=prompt)
            else:
                await send_msg(chat_id, "Image generation returned unknown format.")
        except Exception as e:
            traceback.print_exc()
            await send_msg(chat_id, f"Image error: {e}")
        return

    # default: text response using HF
    try:
        reply = await hf_text(text)
        if not reply:
            await send_msg(chat_id, "Sorry, no reply from HF.")
        else:
            await send_msg(chat_id, reply)
    except Exception as e:
        traceback.print_exc()
        await send_msg(chat_id, f"Hugging Face text error {e}")

@app.post("/webhook")
async def webhook(req: Request, background_tasks: BackgroundTasks):
    update = await req.json()
    msg = update.get("message")
    if not msg:
        return {"ok": True}
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text", "")
    if not chat_id:
        return {"ok": True}
    # handle in background so Telegram acknowledges quickly
    background_tasks.add_task(handle_agent, chat_id, text)
    return {"ok": True}

@app.get("/set_webhook")
async def set_webhook():
    if not EXPOSED_URL:
        raise HTTPException(status_code=400, detail="Set EXPOSED_URL env var first")
    webhook_url = f"{EXPOSED_URL}/webhook"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{TELEGRAM_API}/setWebhook", params={"url": webhook_url})
        return resp.json()

@app.get("/")
async def root():
    return {"msg": "Eldro HF Telegram bot running"}

# Use uvicorn on Koyeb: uvicorn main:app --host 0.0.0.0 --port 8080
