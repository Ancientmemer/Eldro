import os
import httpx
import traceback
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from hf_client import hf_text

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EXPOSED_URL = os.getenv("EXPOSED_URL")
PORT = int(os.getenv("PORT", "8080"))

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN env var first")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


async def send_msg(chat_id: int, text: str):
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            data={"chat_id": chat_id, "text": text}
        )


async def handle_agent(chat_id: int, text: str):
    text = (text or "").strip()
    if not text:
        return

    reply = await hf_text(text)
    await send_msg(chat_id, reply)


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

    background_tasks.add_task(handle_agent, chat_id, text)
    return {"ok": True}


@app.get("/set_webhook")
async def set_webhook():
    if not EXPOSED_URL:
        raise HTTPException(status_code=400, detail="Set EXPOSED_URL env var first")

    webhook_url = f"{EXPOSED_URL}/webhook"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TELEGRAM_API}/setWebhook",
            params={"url": webhook_url}
        )
        return resp.json()
