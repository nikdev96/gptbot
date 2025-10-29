#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("🧪 Тестирование GPT-5...")
print()

# Тестовый запрос
test_message = "Привет! Ты GPT-5? Расскажи кратко о своих главных улучшениях по сравнению с GPT-4."

print(f"Вопрос: {test_message}")
print()
print("Ответ от GPT-5:")
print("-" * 60)

try:
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "user", "content": test_message}
        ],
        max_completion_tokens=500
    )

    answer = response.choices[0].message.content
    print(answer)
    print("-" * 60)
    print()
    print(f"✓ Модель: {response.model}")
    print(f"✓ Использовано токенов: {response.usage.total_tokens}")
    print(f"  - Запрос: {response.usage.prompt_tokens}")
    print(f"  - Ответ: {response.usage.completion_tokens}")

except Exception as e:
    print(f"✗ Ошибка: {e}")
