# gemini_client.py
# Manglish comments included 😄
# ✔ Official google-genai client
# ✔ Correct payload format
# ✔ Auto list available models if 404 happens

import base64
import traceback
from google import genai
from google.api_core.exceptions import ClientError

# Client auto-reads GEMINI_API_KEY from Environment
client = genai.Client()


# ======================================================
#  TEXT GENERATION
# ======================================================
async def call_gemini_text(prompt: str, model: str = "gemini-1.5-flash") -> str:
    """
    Manglish: Prompt plain string koduth generate cheyyum.
    Model not found aanenkil list_model print cheyyum.
    """

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt  # <-- IMPORTANT: plain string, NOT dict
        )

        # 1) Try response.text
        if hasattr(response, "text") and response.text:
            return response.text

        # 2) Fallback: candidates[0].content.parts[0].text
        candidates = getattr(response, "candidates", None)
        if candidates:
            try:
                cand = candidates[0]
                parts = getattr(cand, "content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "") or "Sorry, Gemini returned empty."
            except:
                pass

        # Final fallback
        return "Sorry, Gemini returned empty."

    except ClientError as ce:
        # MODEL NOT FOUND OR OTHER GOOGLE ERRORS
        print("Gemini ClientError:", repr(ce))

        # If model not found: list models
        try:
            print("Listing available models from Google →")
            models = client.models.list()
            names = [m.name for m in models]
            print("Available models:", names)
        except Exception as e:
            print("Failed listing models:", repr(e))
            traceback.print_exc()

        return "Sorry, Gemini API error (model not found). Check logs."

    except Exception as e:
        print("Gemini text ERROR:", repr(e))
        traceback.print_exc()
        return "Sorry, Gemini API error."


# ======================================================
#  IMAGE GENERATION (NANO BANANA STYLE)
# ======================================================
async def generate_image_nano_banana(prompt: str) -> dict:
    """
    Manglish: Nano Banana / Gemini Image generation.
    Returns:
      { "b64": "<base64image>" }
      or { "url": "<public_url>" }
      or {} on error
    """

    try:
        img_resp = client.images.generate(
            model="gemini-2.5-image",    # If not available, logs will show correct name
            prompt=prompt                # <-- IMPORTANT: plain string input
        )

        # 1) Try image list with base64
        images = getattr(img_resp, "images", None) or []
        if images:
            first = images[0]
            b64 = first.get("b64") or first.get("data") or first.get("image")

            # If bytes → convert to base64
            if isinstance(b64, (bytes, bytearray)):
                return {"b64": base64.b64encode(b64).decode("utf-8")}

            # If already plain base64 string
            if isinstance(b64, str) and b64.strip():
                return {"b64": b64}

        # 2) Fallback public URL
        url = getattr(img_resp, "result_url", None) or (
            img_resp.get("url") if isinstance(img_resp, dict) else None
        )

        if url:
            return {"url": url}

        return {}  # empty image result

    except Exception as e:
        print("Gemini image ERROR:", repr(e))
        traceback.print_exc()
        return {}
