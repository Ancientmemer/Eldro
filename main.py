# hf_client.py
# Manglish comments ok
import os
import base64
import traceback
import asyncio
from huggingface_hub import InferenceApi, inference_api

# Read HF key from env
HF_KEY = os.getenv("HUGGINGFACE_API_KEY")
if not HF_KEY:
    print("Warning: HUGGINGFACE_API_KEY not set. HF calls will fail.")

# Helper to create InferenceApi instance
def _get_inference(model: str):
    # The InferenceApi class will route requests to the correct HF router.
    # It uses the HF token for auth.
    return InferenceApi(repo_id=model, token=HF_KEY)

# ------------------------
# Text generation wrapper
# ------------------------
async def call_hf_text(prompt: str, model: str = "gpt2") -> str:
    """
    Manglish: Call Hugging Face text model via huggingface_hub.InferenceApi
    model default "gpt2" (change to a better HF model you have access to).
    """
    try:
        # run blocking InferenceApi in thread
        def _sync_call():
            api = _get_inference(model)
            # for text generation, pass {"inputs": prompt}
            out = api(inputs=prompt, params={"max_new_tokens": 256})
            # `out` can be a string or a dict depending on model/format
            if isinstance(out, str):
                return out
            # Some models return list/dict; try safe extraction:
            if isinstance(out, list) and out:
                if isinstance(out[0], dict) and "generated_text" in out[0]:
                    return out[0]["generated_text"]
                return str(out[0])
            if isinstance(out, dict):
                # try common keys
                for k in ("generated_text","text","output"):
                    if k in out:
                        return out[k]
                return str(out)
            return str(out)
        return await asyncio.to_thread(_sync_call)
    except Exception as e:
        print("HF text error:", repr(e))
        traceback.print_exc()
        return "Sorry, HF text API error."

# ------------------------
# Image generation wrapper
# ------------------------
async def call_hf_image(prompt: str, model: str = "stabilityai/stable-diffusion-2") -> dict:
    """
    Manglish: Generate image using HF Inference API for image models (SD etc).
    Returns dict: {'b64': <base64 png>} or {'url': <public_url>} or {} on error.
    model default: stabilityai/stable-diffusion-2 (change if you prefer another)
    """
    try:
        def _sync_img():
            api = _get_inference(model)
            # For image generation, HF often returns binary bytes.
            resp = api(inputs=prompt, options={"wait_for_model": True})
            # If resp is bytes, assume image bytes
            if isinstance(resp, (bytes, bytearray)):
                return {"b64": base64.b64encode(resp).decode("utf-8")}
            # If dict with 'generated_image' or 'image' or 'data'
            if isinstance(resp, dict):
                for k in ("generated_image","image","data","b64"):
                    if k in resp:
                        v = resp[k]
                        if isinstance(v, (bytes, bytearray)):
                            return {"b64": base64.b64encode(v).decode("utf-8")}
                        if isinstance(v, str) and v.strip():
                            return {"b64": v}
                # If an URL provided
                if "url" in resp:
                    return {"url": resp["url"]}
            # If response is string (rare) — maybe a URL or base64
            if isinstance(resp, str):
                # if looks like base64 (very long) treat as b64; otherwise return as url/text
                if len(resp) > 200 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r" for c in resp[:100]):
                    return {"b64": resp}
                return {"url": resp}
            return {}
        return await asyncio.to_thread(_sync_img)
    except Exception as e:
        print("HF image error:", repr(e))
        traceback.print_exc()
        return {}
