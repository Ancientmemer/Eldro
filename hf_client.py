# hf_client.py
# Manglish comments: lightweight HF Inference API helper
# Uses HF_API_KEY env var. Do NOT hardcode keys.

import os
import base64
import json
import httpx

HF_API_KEY = os.getenv("HF_API_KEY", "")
if not HF_API_KEY:
    raise RuntimeError("Set HF_API_KEY env var")

HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}"
}

async def generate_text(prompt: str, model: str = "gpt2") -> str:
    """
    Manglish: Call HF inference for text generation.
    Default model gpt2 (open) — change to a better model if you have access.
    Returns generated text or empty string on error.
    """
    url = f"https://api-inference.huggingface.co/models/{model}"
    payload = {"inputs": prompt}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(url, headers=HEADERS, json=payload)
            if r.status_code == 200:
                data = r.json()
                # Many text models return list of dicts with 'generated_text'
                if isinstance(data, dict) and "generated_text" in data:
                    return data["generated_text"]
                if isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    if isinstance(first, dict) and "generated_text" in first:
                        return first["generated_text"]
                    # some models return text string directly
                    if isinstance(first, str):
                        return first
                # fallback: stringify
                return json.dumps(data)
            else:
                print("HF text error:", r.status_code, await r.aread())
                return ""
        except Exception as e:
            print("HF text exception:", e)
            return ""

async def generate_image(prompt: str, model: str = "stabilityai/stable-diffusion-xl-base-1.0") -> dict:
    """
    Manglish: Generate image via HF Inference API.
    Returns dict:
      - {'b64': <base64 png bytes>}  OR
      - {'error': '...'}
    """
    url = f"https://api-inference.huggingface.co/models/{model}"
    payload = {"inputs": prompt}
    # Some image models require specific options; adjust as needed.
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            r = await client.post(url, headers=HEADERS, json=payload)
            if r.status_code == 200:
                ct = r.headers.get("content-type", "")
                content = await r.aread()
                # If image bytes returned
                if ct.startswith("image/"):
                    b64 = base64.b64encode(content).decode("utf-8")
                    return {"b64": b64}
                # If JSON (some models return dict with 'image' as data URL)
                try:
                    data = r.json()
                    # possible keys: 'images', 'generated_image', etc.
                    if isinstance(data, dict):
                        # images may be list of base64 strings
                        for k in ("images", "image", "generated_image", "data"):
                            if k in data:
                                val = data[k]
                                # if list
                                if isinstance(val, list) and val:
                                    first = val[0]
                                    if isinstance(first, str) and first.startswith("data:"):
                                        # data:image/png;base64,...
                                        b64 = first.split(",", 1)[1]
                                        return {"b64": b64}
                                    if isinstance(first, (bytes, bytearray)):
                                        return {"b64": base64.b64encode(first).decode("utf-8")}
                                if isinstance(val, str) and val.startswith("data:"):
                                    b64 = val.split(",", 1)[1]
                                    return {"b64": b64}
                                if isinstance(val, str):
                                    # maybe plain base64
                                    return {"b64": val}
                    # fallback
                    return {"error": "Unexpected HF response format"}
                except Exception:
                    # not JSON and not image => error
                    return {"error": f"HF returned {r.status_code} content-type {ct}"}
            else:
                # non-200, include body for debugging
                txt = await r.aread()
                print("HF image error:", r.status_code, txt)
                return {"error": f"status {r.status_code}"}
        except Exception as e:
            print("HF image exception:", e)
            return {"error": str(e)}
