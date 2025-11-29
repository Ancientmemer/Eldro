# hf_client.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")

client = OpenAI(
    api_key=HF_API_KEY,
    base_url="https://router.huggingface.co/v1/"
)

# TEXT generation
async def call_hf_text(prompt: str, model="meta-llama/Llama-3.1-8B-Instruct"):
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return completion.choices[0].message["content"]
    except Exception as e:
        return f"Hugging Face text error: {e}"

# IMAGE generation
async def call_hf_image(prompt: str, model="black-forest-labs/FLUX.1-dev"):
    try:
        img = client.images.generate(
            model=model,
            prompt=prompt
        )
        b64 = img.data[0].b64_json
        return b64
    except Exception as e:
        return f"Image error: {e}"
