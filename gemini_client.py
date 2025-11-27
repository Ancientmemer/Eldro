# gemini_client.py
# Manglish comments inside strings if needed
import os
import base64
from google import genai  # official client, installed from google-genai

# client reads GEMINI_API_KEY from environment automatically
client = genai.Client()

# Text generation
async def call_gemini_text(prompt: str, model: str = "gemini-2.5-flash") -> str:
    try:
        response = client.models.generate_content(
            model=model,
            contents=[{"type": "text", "text": prompt}],
            # optional: temperature=0.7, max_output_tokens=512
        )
        # Try to extract text safely
        text = ""
        if getattr(response, "candidates", None):
            cand = response.candidates[0]
            # content.parts -> list of dicts with 'text'
            parts = getattr(cand, "content", {}).get("parts", [])
            if parts:
                text = parts[0].get("text", "")
        if not text:
            # fallback
            text = getattr(response, "text", "") or str(response)
        if not text:
            return "Sorry, Gemini returned empty."
        return text
    except Exception as e:
        print("Gemini text ERROR:", repr(e))
        return "Sorry, Gemini API error."

# Nano Banana / Image generation
async def generate_image_nano_banana(prompt: str) -> dict:
    """
    Returns {'b64': <base64 png>} or {'url': <public_url>} or {} on error.
    """
    try:
        img_resp = client.images.generate(
            model="gemini-2.5-image",  # adjust model name if needed
            prompt=[{"type": "text", "text": prompt}],
            # optional params: size, quality, etc.
        )
        # response.images -> list of images
        images = getattr(img_resp, "images", None) or []
        if images:
            data = images[0].get("b64") or images[0].get("data") or images[0].get("image")
            if isinstance(data, str) and data.strip():
                return {"b64": data}
            if isinstance(data, (bytes, bytearray)):
                return {"b64": base64.b64encode(data).decode("utf-8")}
        # fallback URL
        url = getattr(img_resp, "result_url", None) or (img_resp.get("url") if isinstance(img_resp, dict) else None)
        if url:
            return {"url": url}
        return {}
    except Exception as e:
        print("Gemini image ERROR:", repr(e))
        return {}
