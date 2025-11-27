import os
import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1/models"

headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": GEMINI_API_KEY
}

# TEXT GENERATION
async def call_gemini_text(prompt: str, model: str = "gemini-1.5-flash"):
    url = f"{BASE_URL}/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=body)

        if resp.status_code != 200:
            print("Gemini text ERROR:", resp.text)
            return "Sorry, Gemini API error."

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except:
            return "Sorry, Gemini returned empty."


# NANO BANANA IMAGE GENERATION
async def generate_image_nano_banana(prompt: str):
    url = "https://generativelanguage.googleapis.com/v1/images:generate"
    body = {
        "model": "models/imagegeneration",
        "prompt": {
            "text": prompt
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=body)

        if resp.status_code != 200:
            print("Gemini image ERROR:", resp.text)
            return None

        data = resp.json()
        try:
            b64 = data["images"][0]["data"]
            return {"b64": b64}
        except:
            return None
