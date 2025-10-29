#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("🔍 Проверка поддержки vision в разных моделях...")
print()

# Тестовое изображение URL (простая картинка для теста)
test_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/320px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

models_to_test = ["gpt-5", "gpt-4o", "gpt-4o-mini"]

for model in models_to_test:
    print(f"Тестирую модель: {model}")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What's in this image? Answer in one short sentence."},
                        {"type": "image_url", "image_url": {"url": test_image_url}}
                    ]
                }
            ],
            max_completion_tokens=100
        )
        print(f"  ✅ {model} поддерживает vision!")
        print(f"     Ответ: {response.choices[0].message.content}")
    except Exception as e:
        print(f"  ❌ {model} НЕ поддерживает vision")
        print(f"     Ошибка: {str(e)[:100]}")
    print()
