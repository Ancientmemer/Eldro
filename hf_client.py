import os
import httpx
import base64

HF_API_KEY = os.getenv("HF_API_KEY")

# Text model
TEXT_MODEL = "meta-llama/Llama-3.2-1B-Instruct"

# Image model
IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"


async def call_hf_text(prompt: str) -> str:
    url = f"https://router.huggingface.co/inference/{TEXT_MODEL}"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            out = res.json()

            if isinstance(out, list) and len(out) > 0 and "generated_text" in out[0]:
                return out[0]["generated_text"]

            return str(out)

    except Exception as e:
        print("HF text error:", e)
        return "⚠️ HuggingFace text API error."


async def call_hf_image(prompt: str):
    url = f"https://router.huggingface.co/inference/{IMAGE_MODEL}"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.post(url, json=payload, headers=headers)
            res.raise_for_status()

            if "image" in res.headers.get("Content-Type", ""):
                b64 = base64.b64encode(res.content).decode()
                return b64

            data = res.json()
            return data

    except Exception as e:
        print("HF image error:", e)
        return None
