import os
import base64
import httpx
from fastapi import FastAPI, Request, BackgroundTasks
from huggingface_client import call_hf_text, call_hf_image

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EXPOSED_URL = os.getenv("EXPOSED_URL", "")
PORT = int(os.getenv("PORT", 8080))

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI()

# -----------------------------------------------------------
# Telegram helpers
# -----------------------------------------------------------
async def send_msg(chat_id, text):
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", data={
            "chat_id": chat_id,
            "text": text
        })

async def send_photo_b64(chat_id, b64, caption=""):
    img_bytes = base64.b64decode(b64)
    files = {"photo": ("ai.png", img_bytes, "image/png")}
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendPhoto",
                          data={"chat_id": chat_id, "caption": caption},
                          files=files)

# -----------------------------------------------------------
# Bot Brain
# -----------------------------------------------------------
async def handle_agent(chat_id, text):
    text = text.strip()

    # IMAGE MODE
    if text.lower().startswith("/img"):
        prompt = text[len("/img"):].strip()
        await send_msg(chat_id, "Generating image…")

        b64 = call_hf_image(prompt)

        if not b64:
            await send_msg(chat_id, "Image API error. Trying text mode…")
            desc = call_hf_text(f"Describe an image for: {prompt}")
            await send_msg(chat_id, desc)
        else:
            await send_photo_b64(chat_id, b64, caption=f"AI Image for: {prompt}")
        return

    # TEXT MODE
    reply = call_hf_text(text)
    if not reply:
        reply = "No response from AI."
    await send_msg(chat_id, reply)

# -----------------------------------------------------------
# Webhook handler
# -----------------------------------------------------------
@app.post("/webhook")
async def webhook(req: Request, background_tasks: BackgroundTasks):
    update = await req.json()

    msg = update.get("message", {})
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text", "")

    if chat_id and text:
        background_tasks.add_task(handle_agent, chat_id, text)

    return {"ok": True}

# -----------------------------------------------------------
# Setup webhook
# -----------------------------------------------------------
@app.get("/set_webhook")
async def set_webhook():
    if not EXPOSED_URL:
        return {"error": "Set EXPOSED_URL first"}

    webhook_url = f"{EXPOSED_URL}/webhook"

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{TELEGRAM_API}/setWebhook",
            params={"url": webhook_url}
        )
        return r.json()

@app.get("/")
async def home():
    return {"msg": "HF AI Assistant running"}
