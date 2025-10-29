#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from telebot import TeleBot
from openai import OpenAI

# Загрузка переменных окружения
load_dotenv()

print("🔍 Проверка подключения...")
print()

# Проверка переменных окружения
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

print(f"✓ TG_BOT_TOKEN загружен: {'Да' if TG_BOT_TOKEN else 'Нет'}")
print(f"✓ OPENAI_API_KEY загружен: {'Да' if OPENAI_API_KEY else 'Нет'}")
print()

# Проверка Telegram Bot
print("📱 Проверка Telegram Bot...")
try:
    bot = TeleBot(TG_BOT_TOKEN)
    bot_info = bot.get_me()
    print(f"✓ Telegram Bot подключен успешно!")
    print(f"   Имя: {bot_info.first_name}")
    print(f"   Username: @{bot_info.username}")
    print(f"   ID: {bot_info.id}")
except Exception as e:
    print(f"✗ Ошибка подключения к Telegram: {e}")
print()

# Проверка OpenAI API
print("🤖 Проверка OpenAI API...")
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    # Простой тестовый запрос
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'Hello' in one word"}
        ],
        max_tokens=10
    )
    print(f"✓ OpenAI API подключен успешно!")
    print(f"   Ответ: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ Ошибка подключения к OpenAI: {e}")

print()
print("✅ Проверка завершена!")
