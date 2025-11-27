# main.py
# Manglish comments and user-facing strings
import os
import json
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
import httpx
from gemini_client import call_gemini_text, generate_image_nano_banana

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EXPOSED_URL = os.getenv("EXPOSED_URL", "")
PORT = int(os.getenv("PORT", "8080"))

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN env var")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"msg": "Eldro AI Assistant running"}

async def send_msg(chat_id: int, text: str):
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": text})

async def send_photo_by_url(chat_id: int, url: str, caption: str = ""):
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(f"{TELEGRAM_API}/sendPhoto", data={"chat_id": chat_id, "photo": url, "caption": caption})

async def send_photo_by_b64(chat_id: int, b64: str, caption: str = ""):
    # Telegram sendPhoto via multipart requires bytes - we convert base64 to bytes and send as files
    image_bytes = b64.encode() if isinstance(b64, str) else b64
    import base64
    img = base64.b64decode(b64)
    files = {"photo": ("image.png", img, "image/png")}
    data = {"chat_id": str(chat_id), "caption": caption}
    async with httpx.AsyncClient(timeout=60.0) as client:
        await client.post(f"{TELEGRAM_API}/sendPhoto", data=data, files=files)

async def handle_agent(chat_id: int, text: str):
    """
    Manglish: Agentic rules:
    - If text starts with /img, generate image via Nano Banana and send.
    - Else handle as chat: call Gemini text model for reply.
    """
    text = (text or "").strip()
    if not text:
        return
    if text.lower().startswith("/img"):
        prompt = text[len("/img"):].strip() or "A creative scene"
        await send_msg(chat_id, "Image generate cheyyunnundu...")  # manglish
        result = await generate_image_nano_banana(prompt)
        if not result:
            await send_msg(chat_id, "Image API illa or error. I'll send a textual description instead.")
            descr = await call_gemini_text(f"Describe a scene for: {prompt}")
            await send_msg(chat_id, descr)
            return
        if result.get("url"):
            await send_photo_by_url(chat_id, result["url"], caption=f"For: {prompt}")
        elif result.get("b64"):
            await send_photo_by_b64(chat_id, result["b64"], caption=f"For: {prompt}")
        else:
            await send_msg(chat_id, "Image generation returned unknown format.")
        return

    # Default: chat
    # build a small system prompt
    system = (
        "You are Eldro Assistant — short, helpful. If asked to 'plan' do a short step list.\n"
        f"User: {text}\nAssistant:"
    )
    reply = await call_gemini_text(system, model="gemini-text-1")  # adjust model name as per your access
    if not reply:
        reply = "Sorry, no reply from Gemini."
    await send_msg(chat_id, reply)

@app.post("/webhook")
async def webhook(req: Request, background_tasks: BackgroundTasks):
    update = await req.json()
    # Only handle messages for now
    msg = update.get("message")
    if not msg:
        return {"ok": True}
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text", "")
    if not chat_id:
        return {"ok": True}
    # enqueue background work
    background_tasks.add_task(handle_agent, chat_id, text)
    return {"ok": True}

@app.get("/set_webhook")
async def set_webhook():
    """
    Manglish: Call once after deploy. EXPOSED_URL must be set to your public URL.
    """
    if not EXPOSED_URL:
        raise HTTPException(status_code=400, detail="Set EXPOSED_URL env var first")
    webhook_url = f"{EXPOSED_URL}/webhook"
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{TELEGRAM_API}/setWebhook", params={"url": webhook_url, "allowed_updates": json.dumps(["message"])})
        return resp.json()
