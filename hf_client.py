# hf_client.py
import os
import base64
import httpx
import traceback

HF_API_KEY = os.getenv("HF_API_KEY", "")
if not HF_API_KEY:
    raise RuntimeError("Set HF_API_KEY env var")

# Set the model ids you will use on Hugging Face.
# Replace with actual repo ids (owner/model).
TEXT_MODEL = os.getenv("HF_TEXT_MODEL", "meta-llama/Llama-3.1-8B-Instruct")  # example: "gpt2" or "bigscience/bloom"
IMAGE_MODEL = os.getenv("HF_IMAGE_MODEL", "Tongyi-MAI/Z-Image-Turbo")  # example

HF_API_URL = "https://router.huggingface.co/models/{}"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

async def hf_text(prompt: str, max_length: int = 256):
    """Call HF inference for text generation. Returns string or raise exception."""
    url = HF_API_URL.format(TEXT_MODEL)
    payload = {
        "inputs": prompt,
        "options": {"wait_for_model": True},
        "parameters": {"max_new_tokens": max_length},
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(url, json=payload, headers=HEADERS)
            if resp.status_code == 200:
                data = resp.json()
                # Many HF text models return a list of dicts with 'generated_text'
                if isinstance(data, list) and data and "generated_text" in data[0]:
                    return data[0]["generated_text"]
                # Some models return plain text or dict
                if isinstance(data, dict) and "generated_text" in data:
                    return data["generated_text"]
                if isinstance(data, str):
                    return data
                # fallback: convert to string
                return str(data)
            else:
                # bubble up useful error message
                raise RuntimeError(f"Hugging Face text error {resp.status_code}: {resp.text}")
        except Exception as e:
            traceback.print_exc()
            raise

async def hf_image(prompt: str, wait_for_model: bool = True):
    """
    Call HF inference for image generation.
    Returns dict with either {'b64': base64str} or {'url': ...} or raises.
    """
    url = HF_API_URL.format(IMAGE_MODEL)
    # Many image models expect {"inputs": prompt}
    payload = {"inputs": prompt, "options": {"wait_for_model": wait_for_model}}
    headers = HEADERS.copy()
    # For image generation we may want the raw bytes back; HF returns binary for some endpoints if Accept set.
    # But many models will return JSON with a link or base64.
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                # Try to parse JSON first
                content_type = resp.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = resp.json()
                    # common responses: {'generated_image': ..., 'data': ...} or [{'generated_text': ...}]
                    # Many community models return {"images": ["data:image/png;base64,..."]} or contain base64
                    # Try to extract base64 strings
                    # If data is list and first contains "generated_image" or "image"
                    if isinstance(data, dict):
                        # search for any base64 strings in dict values
                        for v in data.values():
                            if isinstance(v, str) and v.startswith("data:image"):
                                # data:image/png;base64,....
                                b64 = v.split(",", 1)[1]
                                return {"b64": b64}
                        # maybe 'images' key
                        imgs = data.get("images") or data.get("image") or data.get("result")
                        if imgs:
                            if isinstance(imgs, list) and imgs:
                                first = imgs[0]
                                if isinstance(first, str) and first.startswith("http"):
                                    return {"url": first}
                                if isinstance(first, str) and first.startswith("data:image"):
                                    return {"b64": first.split(",", 1)[1]}
                                if isinstance(first, str):
                                    # might already be base64
                                    return {"b64": first}
                    elif isinstance(data, list) and data:
                        # sometimes list of dicts with 'generated_image' or 'data'
                        first = data[0]
                        if isinstance(first, dict):
                            for k in ("image", "generated_image", "data", "b64_json"):
                                val = first.get(k)
                                if isinstance(val, str) and val.startswith("data:image"):
                                    return {"b64": val.split(",", 1)[1]}
                                if isinstance(val, str) and val.startswith("http"):
                                    return {"url": val}
                                if isinstance(val, str):
                                    return {"b64": val}
                    # fallback: return JSON as string
                    return {"json": data}
                else:
                    # if binary image returned directly (image/png)
                    if "image" in content_type or "png" in content_type:
                        b = resp.content
                        b64 = base64.b64encode(b).decode("utf-8")
                        return {"b64": b64}
                    # unknown content-type
                    raise RuntimeError(f"Hugging Face image unknown content-type: {content_type}")
            else:
                raise RuntimeError(f"Hugging Face image error {resp.status_code}: {resp.text}")
        except Exception:
            traceback.print_exc()
            raise
