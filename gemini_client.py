# gemini_client.py
# Manglish comments inside
import os
import httpx
import base64
import json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not set — falling back to local dummy responses")

# Replace with real Gemini endpoints if Google changes them.
GEMINI_BASE = "https://api.google.com/v1"  # placeholder; actual base from Google docs (ai.google.dev/gemini-api/docs)

async def call_gemini_text(prompt: str, model: str = "gpt-4o-like-or-gemini-text") -> str:
    """
    Manglish: Text generation call. Replace model name with Gemini text model identifier.
    """
    if not GEMINI_API_KEY:
        # dev fallback: playful reversed text
        return "AI (dev fallback): " + prompt[::-1]

    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        # The exact body shape depends on Google API; adapt from ai.google.dev/gemini-api/docs quickstart.
        "model": model,
        "input": prompt,
        "maxOutputTokens": 800
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        # NOTE: update URL to the provider's endpoint per docs (example path used)
        url = f"https://api.google.com/v1/models/{model}:generate"
        resp = await client.post(url, headers=headers, json=body)
        if resp.status_code == 200:
            data = resp.json()
            # Actual response parsing depends on Gemini response format.
            # Example fallback:
            text = data.get("candidates", [{}])[0].get("content", "")
            if not text:
                # try alternative keys
                text = data.get("output", {}).get("text", "")
            return text or "Sorry, empty reply from Gemini."
        else:
            print("Gemini text error:", resp.status_code, resp.text)
            return "Sorry, Gemini API error."

async def generate_image_nano_banana(prompt: str) -> dict:
    """
    Manglish: Call Nano Banana (Gemini image). Return dict with either {'url': ...} or {'b64': '...'}
    The exact API endpoint and payload must follow Google docs; below is a template.
    """
    if not GEMINI_API_KEY:
        # dev fallback: return empty (no image)
        return {}

    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gemini-2-5-flash-image",  # Nano Banana model id (example)
        "prompt": prompt,
        "imageFormat": "png",
        "maxOutputTokens": 800
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        url = f"https://api.google.com/v1/images:generate"  # update per actual docs
        resp = await client.post(url, headers=headers, json=body)
        if resp.status_code == 200:
            data = resp.json()
            # Parsing depends on response form; common patterns:
            # - inlineDataParts -> bytes base64
            # - candidates -> parts -> inline data
            # Try multiple common fields:
            # Example: data["candidates"][0]["content"][0]["image"] -> base64
            try:
                # try inline bytes path
                parts = data.get("candidates", [])[0].get("content", [])
                for p in parts:
                    if p.get("type") == "image" and p.get("imageBytes"):
                        return {"b64": p["imageBytes"]}
            except Exception:
                pass
            # fallback: check a top-level URL
            url_out = data.get("url") or data.get("resultUrl")
            if url_out:
                return {"url": url_out}
            return {}
        else:
            print("Gemini image error:", resp.status_code, resp.text)
            return {}
