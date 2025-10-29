#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("🔍 Проверка доступных моделей GPT...")
print()

try:
    models = client.models.list()

    # Фильтруем только GPT модели
    gpt_models = [m for m in models.data if 'gpt' in m.id.lower()]

    print("Доступные GPT модели:")
    for model in sorted(gpt_models, key=lambda x: x.id):
        print(f"  - {model.id}")

    print()
    print("Проверка на GPT-5:")
    gpt5_models = [m for m in gpt_models if 'gpt-5' in m.id.lower()]
    if gpt5_models:
        print("✓ GPT-5 модели найдены:")
        for m in gpt5_models:
            print(f"  - {m.id}")
    else:
        print("✗ GPT-5 модели не найдены")
        print()
        print("Доступные новейшие модели:")
        print("  - gpt-4o (самая новая)")
        print("  - gpt-4-turbo")
        print("  - gpt-4")
        print("  - gpt-3.5-turbo")

except Exception as e:
    print(f"Ошибка: {e}")
