import os
import re
import asyncio
import aiohttp
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

AVAILABLE_MODELS = {
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "deepseek-chat": "deepseek/deepseek-chat",
    "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
}

DEFAULT_MODELS = ["gpt-4o-mini", "deepseek-chat"]

SYSTEM_PROMPT = """
Сгенерируй короткую Python-функцию, которая проверяет, является ли введенный год високосным.
Также напиши автотесты на pytest для проверки логики функции.
Не используй markdown. Верни только Python-код.
"""

async def fetch_from_model(session: aiohttp.ClientSession, model_id: str, prompt: str) -> dict:
    if not API_KEY:
        return {"model": model_id, "content": "Ошибка: API-ключ не задан", "status": "error"}

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 500,
    }

    try:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "model": model_id,
                    "content": data["choices"][0]["message"]["content"],
                    "status": "success",
                }
            else:
                error_text = await resp.text()
                return {
                    "model": model_id,
                    "content": f"Ошибка {resp.status}: {error_text[:200]}",
                    "status": "error",
                }
    except Exception as e:
        return {"model": model_id, "content": f"Исключение: {str(e)}", "status": "error"}

async def compare_models(
    models: List[str],
    session: aiohttp.ClientSession,
    custom_prompt: str = None
) -> Dict:
    prompt = custom_prompt or SYSTEM_PROMPT
    selected_ids = [AVAILABLE_MODELS[m] for m in models if m in AVAILABLE_MODELS]
    if not selected_ids:
        return {"error": "Не выбрано ни одной модели"}

    tasks = [fetch_from_model(session, mid, prompt) for mid in selected_ids]
    results = await asyncio.gather(*tasks)
    return {"results": results}

def judge_winner(results: List[dict]) -> dict:
    winners, losers = [], []
    for res in results:
        code = res.get("content", "")
        model = res.get("model", "unknown")
        if re.search(r'year\s*%\s*400\s*==\s*0|not\s+year\s*%\s*400|year\s*%\s*400\b', code):
            winners.append(model)
        else:
            losers.append(model)

    if len(winners) == 1:
        msg = f"🏆 Победитель: {winners[0]}! Учтено правило 400."
    elif len(winners) > 1:
        msg = f"🤝 Ничья! Модели {', '.join(winners)} справились."
    else:
        msg = f"😞 Все проиграли: {', '.join(losers)}. Никто не учёл правило 400."

    return {"winners": winners, "losers": losers, "message": msg}