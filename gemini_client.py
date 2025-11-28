# gemini_client.py
# Manglish comments inside
# Default model set to gemini-2.0-flash
# Requires: google-genai, google-api-core, googleapis-common-protos in requirements.txt

import base64
import traceback
from google import genai
from google.api_core.exceptions import ClientError

# Client reads GEMINI_API_KEY from environment automatically
client = genai.Client()

# Default model (change if your Google project gives another model)
MODEL_DEFAULT = "gemini-1.5-flash"   # <-- default model set here

# -----------------------
# Text generation wrapper
# -----------------------
async def call_gemini_text(prompt: str, model: str = None) -> str:
    """
    Manglish: Generate text. If model is None, use MODEL_DEFAULT.
    Returns text or friendly error message.
    """
    model_to_use = model or MODEL_DEFAULT
    try:
        response = client.models.generate_content(
            model=model_to_use,
            contents=prompt  # IMPORTANT: plain string for the official client
        )

        # Try response.text first
        text = getattr(response, "text", None)
        if text:
            return text

        # Fallback: candidates -> content -> parts
        candidates = getattr(response, "candidates", None)
        if candidates:
            try:
                cand = candidates[0]
                parts = getattr(cand, "content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "") or "Sorry, Gemini returned empty."
            except Exception:
                pass

        return "Sorry, Gemini returned empty."

    except ClientError as ce:
        # If model not found or permission error, list available models to logs
        print("Gemini ClientError:", repr(ce))
        try:
            print("Listing available models for debugging...")
            models = client.models.list()
            names = [m.name for m in models]
            print("Available models:", names)
        except Exception as e:
            print("Failed listing models:", repr(e))
            traceback.print_exc()
        return f"Sorry, Gemini API error (model: {model_to_use}). Check logs."

    except Exception as e:
        print("Gemini text ERROR:", repr(e))
        traceback.print_exc()
        return "Sorry, Gemini API error."

# -----------------------
# Image generation wrapper (Nano Banana)
# -----------------------
async def generate_image_nano_banana(prompt: str, model: str = None) -> dict:
    """
    Manglish: Generate image with Gemini image model.
    Returns {'b64': base64_png} or {'url': public_url} or {} on error.
    """
    model_to_use = model or "gemini-2.5-image"
    try:
        img_resp = client.images.generate(
            model=model_to_use,
            prompt=prompt  # IMPORTANT: plain string
        )

        images = getattr(img_resp, "images", None) or []
        if images:
            first = images[0]
            # try common keys
            b64 = first.get("b64") or first.get("data") or first.get("image")
            if isinstance(b64, (bytes, bytearray)):
                return {"b64": base64.b64encode(b64).decode("utf-8")}
            if isinstance(b64, str) and b64.strip():
                return {"b64": b64}

        # fallback: public url
        url = getattr(img_resp, "result_url", None) or (img_resp.get("url") if isinstance(img_resp, dict) else None)
        if url:
            return {"url": url}

        return {}
    except Exception as e:
        print("Gemini image ERROR:", repr(e))
        traceback.print_exc()
        return {}
