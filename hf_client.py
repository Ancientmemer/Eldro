# hf_client.py
import os
import traceback
from openai import OpenAI

HF_API_KEY = os.getenv("HF_API_KEY")

client = OpenAI(
    base_url="https://router.huggingface.co/v1/",
    api_key=HF_API_KEY
)

MODEL_TEXT = "openai-community/gpt2"  
MODEL_IMAGE = "black-forest-labs/FLUX.1-dev"

async def call_hf_text(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model=MODEL_TEXT,
            messages=[{"role": "user", "content": prompt}]
        )

        # NEW CORRECT WAY
        reply = completion.choices[0].message.content
        return reply

    except Exception as e:
        traceback.print_exc()
        return f"Hugging Face text error: {e}"


async def call_hf_image(prompt: str):
    try:
        result = client.images.generate(
            model=MODEL_IMAGE,
            prompt=prompt
        )

        # Some models return base64, some return URL
        output = result.data[0]

        if hasattr(output, "b64_json") and output.b64_json:
            return {"b64": output.b64_json}

        if hasattr(output, "url") and output.url:
            return {"url": output.url}

        return {}

    except Exception as e:
        traceback.print_exc()
        return {}
