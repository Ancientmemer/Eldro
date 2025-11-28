# main.py
# Manglish comments in critical parts.
import os
import base64
import json
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
import httpx
from hf_client import generate_text, generate_image

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
HF_API_KEY = os.getenv("HF_API_KEY", "")
EXPOSED_URL = os.getenv("EXPOSED_URL", "")  # set your koyeb url
PORT = int(os.getenv("PORT", "8080"))

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN env var")
if not HF_API_KEY:
    raise RuntimeError("Set HF_API_KEY env var")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

app = FastAPI()

async def send_msg(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": text})

async def send_photo_by_b64(chat_id: int, b64: str, caption: str = ""):
    # Telegram expects multipart/form-data file content. We send as bytes stream.
    image_bytes = base64.b64decode(b64)
    files = {"photo": ("image.jpg", image_bytes, "image/jpeg")}
    data = {"chat_id": str(chat_id), "caption": caption}
    async with httpx.AsyncClient(timeout=60.0) as client:
        await client.post(f"{TELEGRAM_API}/sendPhoto", data=data, files=files)

async def handle_agent(chat_id: int, text: str):
    """
    Manglish: If user starts with /img or /image generate image via HF.
    Else call text generation.
    """
    text = (text or "").strip()
    if not text:
        return
    # image trigger
    if text.lower().startswith("/img") or text.lower().startswith("/image"):
        # remove command prefix
        prompt = text.split(" ", 1)[1].strip() if " " in text else "A creative scene"
        await send_msg(chat_id, "Image generate cheyyunnundu...")
        img = await generate_image(prompt)
        if img.get("b64"):
            await send_photo_by_b64(chat_id, img["b64"], caption=f"For: {prompt}")
            return
        else:
            # fallback use text description
            await send_msg(chat_id, "Image API illa or error. I'll send a textual description instead.")
            descr = await generate_text(f"Describe a scene: {prompt}")
            if not descr:
                descr = "Sorry, I couldn't generate an image or description."
            await send_msg(chat_id, descr)
            return

    # default text chat
    # small system prompt style
    system = "You are Eldro Assistant - short, helpful."
    # combine
    prompt = f"{system}\nUser: {text}\nAssistant:"
    reply = await generate_text(prompt, model="gpt2")  # change model if you have access
    if not reply:
        reply = "Sorry, no reply from the model."
    await send_msg(chat_id, reply)

@app.post("/webhook")
async def webhook(req: Request, background_tasks: BackgroundTasks):
    update = await req.json()
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return {"ok": True}
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text", "") or ""
    if not chat_id:
        return {"ok": True}
    background_tasks.add_task(handle_agent, chat_id, text)
    return {"ok": True}

@app.get("/set_webhook")
async def set_webhook():
    if not EXPOSED_URL:
        raise HTTPException(status_code=400, detail="Set EXPOSED_URL env var first")
    webhook_url = f"{EXPOSED_URL}/webhook"
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{TELEGRAM_API}/setWebhook", params={"url": webhook_url})
        return resp.json()

@app.get("/health")
async def health():
    return {"status": "ok"}
