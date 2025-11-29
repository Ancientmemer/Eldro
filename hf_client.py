# hf_client.py
# HuggingFace new API implementation

import base64
from huggingface_hub import InferenceClient

import os

HF_API_KEY = os.getenv("HF_API_KEY")

# Create the client
client = InferenceClient(api_key=HF_API_KEY)

# --------------------------- TEXT GENERATION ---------------------------
async def call_hf_text(prompt: str):
    try:
        response = client.text_generation(
            model="deepseek-ai/DeepSeek-Math-V2",
            prompt=prompt,
            max_new_tokens=200
        )
        return response
    except Exception as e:
        print("HF text error:", e)
        return "HuggingFace text error."

# --------------------------- IMAGE GENERATION ---------------------------
async def call_hf_image(prompt: str):
    try:
        img_bytes = client.text_to_image(
            model="Tongyi-MAI/Z-Image-Turbo",
            prompt=prompt
        )
        encoded = base64.b64encode(img_bytes).decode("utf-8")
        return encoded
    except Exception as e:
        print("HF image error:", e)
        return None
