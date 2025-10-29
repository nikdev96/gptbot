#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("⚡ Тест скорости разных моделей GPT")
print("=" * 60)
print()

# Тестовый запрос
test_message = "Привет! Ответь одним предложением: как дела?"

# Модели для тестирования
models = [
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-3.5-turbo"
]

results = []

for model in models:
    print(f"🧪 Тестирую: {model}")

    try:
        start_time = time.time()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": test_message}
            ],
            max_completion_tokens=100
        )

        end_time = time.time()
        duration = end_time - start_time

        answer = response.choices[0].message.content
        tokens = response.usage.total_tokens

        results.append({
            "model": model,
            "duration": duration,
            "tokens": tokens,
            "answer": answer
        })

        print(f"   ⏱  Время: {duration:.2f} сек")
        print(f"   📊 Токенов: {tokens}")
        print(f"   💬 Ответ: {answer[:50]}...")
        print()

    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:80]}")
        print()

# Сортируем по скорости
results.sort(key=lambda x: x["duration"])

print("=" * 60)
print("🏆 РЕЗУЛЬТАТЫ (от самой быстрой к самой медленной):")
print("=" * 60)
print()

for i, result in enumerate(results, 1):
    print(f"{i}. {result['model']}")
    print(f"   ⏱  {result['duration']:.2f} сек")
    print(f"   📊 {result['tokens']} токенов")
    print()

print("=" * 60)
print(f"✅ Самая быстрая модель: {results[0]['model']} ({results[0]['duration']:.2f} сек)")
print(f"⚡ Рекомендуется для бота: {results[0]['model']}")
