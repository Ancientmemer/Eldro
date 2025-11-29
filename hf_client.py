import os
from openai import OpenAI

HF_API_KEY = os.getenv("HF_API_KEY")

client = OpenAI(
    base_url="https://router.huggingface.co/v1/",
    api_key=HF_API_KEY
)

async def hf_text(prompt: str, model="meta-llama/Llama-3.1-8B-Instruct:novita"):
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message["content"]
    except Exception as e:
        return f"Hugging Face text error: {e}"
