#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("🎨 Тестирование DALL-E...")
print()

# Тестовый запрос
prompt = "A cute robot reading a book in a cozy library"

try:
    print(f"Генерирую изображение: '{prompt}'")
    print("Ожидайте...")
    print()

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url

    print("✅ Изображение сгенерировано успешно!")
    print(f"URL: {image_url}")
    print()
    print(f"Revised prompt: {response.data[0].revised_prompt}")

except Exception as e:
    print(f"❌ Ошибка: {e}")
