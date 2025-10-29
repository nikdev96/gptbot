#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("🧪 Простой тест GPT-5...")
print()

try:
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "user", "content": "Say hello in one word"}
        ]
    )

    print(f"Ответ: '{response.choices[0].message.content}'")
    print(f"Модель: {response.model}")
    print(f"Finish reason: {response.choices[0].finish_reason}")
    print(f"Токенов использовано: {response.usage.total_tokens}")
    print()
    print("✓ GPT-5 работает!")

except Exception as e:
    print(f"✗ Ошибка: {e}")
