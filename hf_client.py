import requests
import json
import base64
import os

HF_API_KEY = os.getenv("HF_API_KEY")

# Your repo or public model
HF_TEXT_MODEL_URL = "https://router.huggingface.co/adhinsanthosh2255/Eldro"
HF_IMAGE_MODEL_URL = "https://router.huggingface.co/models/stabilityai/sd-turbo"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

def call_hf_text(prompt: str):
    try:
        payload = {"inputs": prompt}

        r = requests.post(HF_TEXT_MODEL_URL, headers=headers, json=payload)

        if r.status_code != 200:
            print("HF text error:", r.status_code, r.content)
            return "Sorry, HF text API error."

        out = r.json()
        if isinstance(out, list) and len(out) > 0:
            return out[0].get("generated_text", "")
        return str(out)

    except Exception as e:
        print("HF text exception:", e)
        return "HF text error."


def call_hf_image(prompt: str):
    try:
        payload = {"inputs": prompt}

        r = requests.post(HF_IMAGE_MODEL_URL, headers=headers, json=payload)

        if r.status_code != 200:
            print("HF image error:", r.status_code, r.content)
            return None

        img_bytes = r.content
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        return b64

    except Exception as e:
        print("HF image exception:", e)
        return None
