# gemini_client.py
# Manglish comments inside strings
# This file uses the official google-genai client.
# Ensure `google-genai` is installed and GEMINI_API_KEY env var is set on Koyeb.

import base64
from google import genai

# The official client will read GEMINI_API_KEY from the environment automatically
client = genai.Client()

# -----------------------
# Text generation wrapper
# -----------------------
async def call_gemini_text(prompt: str, model: str = "gemini-2.5-flash") -> str:
    """
    Manglish: Itha text call. Important: pass plain string to `contents`.
    Returns text or an error message.
    """
    try:
        # PASS A PLAIN STRING for contents (not a dict)
        response = client.models.generate_content(
            model=model,
            contents=prompt  # <-- IMPORTANT: plain string
            # optional: temperature=0.7, max_output_tokens=512
        )
        # Most responses expose .text or candidates. Use safe extraction.
        # Try response.text first:
        text = getattr(response, "text", None)
        if text:
            return text

        # Fallback: check candidates structure
        candidates = getattr(response, "candidates", None)
        if candidates:
            try:
                cand = candidates[0]
                # cand.content.parts -> list of parts with text
                parts = getattr(cand, "content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "") or "Sorry, Gemini returned empty."
            except Exception:
                pass

        # Final fallback
        return "Sorry, Gemini returned empty."
    except Exception as e:
        # Print error to Koyeb logs for debugging
        print("Gemini text ERROR:", repr(e))
        return "Sorry, Gemini API error."

# -----------------------
# Nano Banana / Image generation wrapper
# -----------------------
async def generate_image_nano_banana(prompt: str) -> dict:
    """
    Manglish: Call Gemini image generation (Nano Banana).
    Return {'b64': <base64 PNG str>} or {'url': <public_url>} or {} on error.
    NOTE: pass prompt as plain string.
    """
    try:
        img_resp = client.images.generate(
            model="gemini-2.5-image",  # change model name if your project uses another
            prompt=prompt               # <-- IMPORTANT: plain string
            # optional params like size can be added here
        )

        # Many responses include images list with base64 in `.images[0].b64`
        images = getattr(img_resp, "images", None) or []
        if images:
            first = images[0]
            # Try common keys
            b64 = first.get("b64") or first.get("data") or first.get("image")
            # if bytes, convert
            if isinstance(b64, (bytes, bytearray)):
                return {"b64": base64.b64encode(b64).decode("utf-8")}
            if isinstance(b64, str) and b64.strip():
                return {"b64": b64}

        # fallback: some APIs return a result_url or url
        url = getattr(img_resp, "result_url", None) or (img_resp.get("url") if isinstance(img_resp, dict) else None)
        if url:
            return {"url": url}

        return {}
    except Exception as e:
        print("Gemini image ERROR:", repr(e))
        return {}
