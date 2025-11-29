# main.py
import os
import io
import json
import traceback
from typing import Optional
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
import httpx
import base64

# Environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
EXPOSED_URL = os.getenv("EXPOSED_URL", "")  # e.g. https://important-jacky-eldro-....koyeb.app
HF_API_KEY = os.getenv("HF_API_KEY", "")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN env var")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Default HF models (you can change from Koyeb envs if needed)
HF_TEXT_MODEL = os.getenv("HF_TEXT_MODEL", "deepseek-ai/DeepSeek-Math-V2")  # small default; replace with better HF-inference model you want
HF_IMAGE_MODEL = os.getenv("HF_IMAGE_MODEL", "Tongyi-MAI/Z-Image-Turbo")  # recommended: stable-diffusion model

app = FastAPI()


async def call_hf_text(prompt: str, model: Optional[str] = None) -> str:
    """
    Call Hugging Face router for text generation.
    Uses POST https://router.huggingface.co/models/{model}
    """
    model = model or HF_TEXT_MODEL
    if not HF_API_KEY:
        return "HF API key not set."

    url = f"https://router.huggingface.co/models/{model}"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "application/json",
    }
    payload = {"inputs": prompt}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            # handle status
            if resp.status_code != 200:
                # return helpful error
                return f"Hugging Face text error {resp.status_code}: {resp.text[:300]}"
            data = resp.json()
            # many HF models return different shapes. Try common ones:
            if isinstance(data, dict):
                # some models: {"generated_text": "..." }
                if "generated_text" in data:
                    return data["generated_text"]
                # or {"outputs":[{"generated_text": "..."}]}
                if "outputs" in data and isinstance(data["outputs"], list) and "generated_text" in data["outputs"][0]:
                    return data["outputs"][0]["generated_text"]
            if isinstance(data, list) and len(data) > 0:
                # huggingface sometimes returns list of objects
                first = data[0]
                if isinstance(first, dict) and "generated_text" in first:
                    return first["generated_text"]
                # other models: list of strings
                if isinstance(first, str):
                    return first
            # fallback: convert to string
            return str(data)
    except Exception as e:
        traceback.print_exc()
        return f"Hugging Face text exception: {repr(e)}"


async def call_hf_image(prompt: str, model: Optional[str] = None) -> Optional[bytes]:
    """
    Generate an image with Hugging Face router. Return raw PNG bytes or None.
    Note: some HF image endpoints return binary directly; others return base64 or JSON.
    """
    model = model or HF_IMAGE_MODEL
    if not HF_API_KEY:
        return None

    url = f"https://router.huggingface.co/models/{model}"  # router also supports /models/...
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        # Accept left default — we will handle JSON or binary below
    }
    payload = {"inputs": prompt}
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                # maybe model busy or error
                print("HF image error:", resp.status_code, resp.text)
                return None
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                data = resp.json()
                # If returned base64 in JSON:
                # {"images":["data:image/png;base64,..."]} or {"generated_images":[ "...base64..." ]}
                # or [{"data":"...base64..."}]
                # Try common keys:
                # 1) "images" list with base64 strings
                if isinstance(data, dict):
                    for key in ("images", "generated_images", "result"):
                        if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                            raw = data[key][0]
                            if isinstance(raw, str) and raw.startswith("data:"):
                                # data:image/png;base64,....
                                b64 = raw.split(",", 1)[1]
                                return base64.b64decode(b64)
                            elif isinstance(raw, str):
                                # raw base64
                                return base64.b64decode(raw)
                if isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    if isinstance(first, str) and first.startswith("data:"):
                        b64 = first.split(",", 1)[1]
                        return base64.b64decode(b64)
                    if isinstance(first, dict) and "data" in first:
                        return base64.b64decode(first["data"])
                # unknown json format
                print("HF image unknown json format:", data)
                return None
            else:
                # likely binary image (image/png)
                return resp.content
    except Exception as e:
        traceback.print_exc()
        return None


# Helper to send text message
async def send_msg(chat_id: int, text: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})


# Helper to send photo by bytes
async def send_photo_by_bytes(chat_id: int, img_bytes: bytes, caption: str = ""):
    # Telegram expects multipart form with file field "photo"
    files = {"photo": ("image.png", img_bytes, "image/png")}
    data = {"chat_id": str(chat_id), "caption": caption}
    async with httpx.AsyncClient(timeout=120.0) as client:
        await client.post(f"{TELEGRAM_API}/sendPhoto", data=data, files=files)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(req: Request, background_tasks: BackgroundTasks):
    """
    Handle telegram webhook POST.
    Enqueue the processing to background task to avoid timeouts.
    """
    body = await req.json()
    # telegram delivers {"message": {...}} or {"edited_message": ...}
    update = body
    message = update.get("message") or update.get("edited_message") or {}
    if not message:
        return {"ok": True}
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text") or message.get("caption") or ""
    if not chat_id:
        return {"ok": True}

    # add background task
    background_tasks.add_task(handle_agent, chat_id, text)
    return {"ok": True}


async def handle_agent(chat_id: int, text: str):
    text = (text or "").strip()
    if not text:
        return

    # image command: startswith /img or /image or /img:
    lowered = text.lower().strip()
    if lowered.startswith("/img") or lowered.startswith("/image"):
        # extract prompt part after command
        prompt = text.split(" ", 1)[1].strip() if " " in text else "A creative scene"
        await send_msg(chat_id, "Generating image, please wait...")

        img_bytes = await call_hf_image(prompt)
        if not img_bytes:
            await send_msg(chat_id, "Image generation failed or not available. I'll send a description instead.")
            descr = await call_hf_text(f"Describe an image scene for: {prompt}", model=None)
            await send_msg(chat_id, descr)
            return
        # send binary photo
        await send_photo_by_bytes(chat_id, img_bytes, caption=f"Image: {prompt}")
        return

    # otherwise text chat
    # small system prompt + user prompt
    system_prompt = (
        "You are Eldro Assistant — short, helpful. If asked to 'plan' do a short step list.\n"
        "Respond in brief and clear Malayalam/English depending on user tone."
    )
    cur_prompt = f"{system_prompt}\nUser: {text}\nAssistant:"
    reply = await call_hf_text(cur_prompt)
    if not reply:
        reply = "Sorry, no reply from the text model."
    await send_msg(chat_id, reply)


@app.get("/set_webhook")
async def set_webhook():
    """
    Call once after deploy. EXPOSED_URL must be set.
    """
    if not EXPOSED_URL:
        raise HTTPException(status_code=400, detail="Set EXPOSED_URL env var first")
    webhook_url = f"{EXPOSED_URL}/webhook"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{TELEGRAM_API}/setWebhook", params={"url": webhook_url, "allowed_updates": json.dumps(["message", "edited_message"])})
        return resp.json()
