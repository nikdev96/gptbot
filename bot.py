#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import base64
import requests
import telebot
from telebot import types
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Загрузка переменных окружения
load_dotenv()

# Инициализация Telegram бота
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
bot = telebot.TeleBot(TG_BOT_TOKEN)

# Инициализация OpenAI клиента
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

# Директория для хранения истории чатов
HISTORY_DIR = Path('./chat_history')
HISTORY_DIR.mkdir(exist_ok=True)

# Хранилище настроек пользователей (модель по умолчанию)
user_settings = {}
DEFAULT_MODEL = "gpt-4o-mini"

# Доступные модели
MODELS = {
    "gpt-4o-mini": {
        "name": "GPT-4o Mini ⚡",
        "speed": "0.75 сек",
        "description": "Быстрая модель"
    },
    "gpt-5": {
        "name": "GPT-5 🧠",
        "speed": "3.80 сек",
        "description": "Мощная модель"
    }
}

# Системное сообщение для ChatGPT
SYSTEM_MESSAGE = {
    "role": "system",
    "content": "You are a helpful assistant."
}


def get_chat_history_path(chat_id):
    """Получить путь к файлу истории чата"""
    return HISTORY_DIR / f"chat_{chat_id}.json"


def load_chat_history(chat_id):
    """Загрузить историю чата из файла"""
    history_path = get_chat_history_path(chat_id)
    if history_path.exists():
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return [SYSTEM_MESSAGE]
    return [SYSTEM_MESSAGE]


def save_chat_history(chat_id, history):
    """Сохранить историю чата в файл"""
    history_path = get_chat_history_path(chat_id)
    try:
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving chat history: {e}")


def clear_chat_history(chat_id):
    """Очистить историю чата"""
    history_path = get_chat_history_path(chat_id)
    if history_path.exists():
        history_path.unlink()


def get_user_model(chat_id):
    """Получить модель пользователя"""
    return user_settings.get(chat_id, DEFAULT_MODEL)


def set_user_model(chat_id, model):
    """Установить модель пользователя"""
    user_settings[chat_id] = model


def call_openai_api(model, messages, max_tokens=1000):
    """Универсальная функция вызова OpenAI API с правильными параметрами"""
    if model == "gpt-5":
        # GPT-5 требует max_completion_tokens и не поддерживает температуру
        return client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=max_tokens
        )
    else:
        # Остальные модели используют стандартные параметры
        return client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )


def create_menu_keyboard():
    """Создать клавиатуру главного меню"""
    markup = types.InlineKeyboardMarkup(row_width=1)

    btn_new_chat = types.InlineKeyboardButton(
        "🔄 Начать новый чат",
        callback_data="new_chat"
    )
    btn_select_model = types.InlineKeyboardButton(
        "🤖 Выбрать модель",
        callback_data="select_model"
    )

    markup.add(btn_new_chat, btn_select_model)
    return markup


def create_model_keyboard(current_model):
    """Создать клавиатуру выбора модели"""
    markup = types.InlineKeyboardMarkup(row_width=1)

    for model_id, model_info in MODELS.items():
        checkmark = "✅ " if model_id == current_model else ""
        btn_text = f"{checkmark}{model_info['name']} - {model_info['speed']}"
        btn = types.InlineKeyboardButton(
            btn_text,
            callback_data=f"model_{model_id}"
        )
        markup.add(btn)

    btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")
    markup.add(btn_back)

    return markup


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    chat_id = message.chat.id
    current_model = get_user_model(chat_id)
    model_name = MODELS[current_model]["name"]

    welcome_text = f"""
Привет! Я ChatGPT бот с поддержкой разных моделей!

Текущая модель: {model_name}

Доступные команды:
/start или /help - показать это сообщение
/menu - открыть меню настроек
/new - начать новый диалог
/image <описание> - создать изображение 🎨

Что я умею:
📝 Отвечать на текстовые сообщения
🖼 Анализировать изображения (отправь фото)
🎨 Генерировать изображения (команда /image)
💬 Поддерживать контекст разговора
⚡ Отвечать очень быстро!

Просто отправь мне сообщение или фото!
    """
    bot.reply_to(message, welcome_text.strip())


@bot.message_handler(commands=['new'])
def new_conversation(message):
    """Обработчик команды /new - очистка истории"""
    chat_id = message.chat.id
    clear_chat_history(chat_id)
    bot.reply_to(message, "История диалога очищена. Начинаем новый разговор!")


@bot.message_handler(commands=['menu'])
def show_menu(message):
    """Обработчик команды /menu - показать меню"""
    chat_id = message.chat.id
    current_model = get_user_model(chat_id)
    model_name = MODELS[current_model]["name"]

    menu_text = f"""
⚙️ Меню настроек

Текущая модель: {model_name}

Выберите действие:
    """
    markup = create_menu_keyboard()
    bot.send_message(chat_id, menu_text.strip(), reply_markup=markup)


@bot.message_handler(commands=['image', 'generate'])
def generate_image(message):
    """Обработчик команды /image - генерация изображения"""
    chat_id = message.chat.id

    # Получаем текст после команды
    command_parts = message.text.split(maxsplit=1)

    if len(command_parts) < 2:
        bot.reply_to(message,
            "🎨 Для генерации изображения укажите описание:\n\n"
            "Пример: /image кот в космосе\n"
            "Или: /generate робот читает книгу")
        return

    prompt = command_parts[1]

    # Показываем, что бот работает
    status_message = bot.reply_to(message, "🎨 Генерирую изображение... Это может занять ~10 секунд.")

    try:
        # Генерируем изображение
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt

        # Удаляем статусное сообщение
        bot.delete_message(chat_id, status_message.message_id)

        # Отправляем изображение
        bot.send_photo(chat_id, image_url,
            caption=f"🎨 Изображение готово!\n\n📝 Ваш запрос: {prompt}\n\n💡 Улучшенный промпт: {revised_prompt[:200]}...")

    except Exception as e:
        error_message = f"Произошла ошибка при генерации изображения: {str(e)}"
        print(error_message)
        bot.edit_message_text(
            "❌ Извините, произошла ошибка при генерации изображения. Попробуйте другой запрос.",
            chat_id,
            status_message.message_id
        )


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Обработчик фотографий"""
    chat_id = message.chat.id

    # Показываем, что бот печатает
    bot.send_chat_action(chat_id, 'typing')

    try:
        # Получаем самое большое фото (последнее в списке)
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)

        # Скачиваем фото
        file_url = f'https://api.telegram.org/file/bot{TG_BOT_TOKEN}/{file_info.file_path}'
        photo_response = requests.get(file_url)

        # Конвертируем в base64
        photo_base64 = base64.b64encode(photo_response.content).decode('utf-8')

        # Получаем caption (если есть)
        caption = message.caption if message.caption else "Что на этом изображении?"

        # Загружаем историю чата
        history = load_chat_history(chat_id)

        # Добавляем сообщение пользователя с изображением
        history.append({
            "role": "user",
            "content": [
                {"type": "text", "text": caption},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{photo_base64}"
                    }
                }
            ]
        })

        # Получаем модель пользователя и отправляем запрос в OpenAI
        user_model = get_user_model(chat_id)
        response = call_openai_api(user_model, history, max_tokens=1000)

        # Получаем ответ
        assistant_message = response.choices[0].message.content

        # Добавляем ответ в историю
        history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Сохраняем историю
        save_chat_history(chat_id, history)

        # Отправляем ответ пользователю
        bot.reply_to(message, assistant_message)

    except Exception as e:
        error_message = f"Произошла ошибка при обработке изображения: {str(e)}"
        print(error_message)
        bot.reply_to(message, "Извините, произошла ошибка при анализе изображения. Попробуйте снова или используйте /new для начала нового диалога.")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    """Обработчик текстовых сообщений"""
    chat_id = message.chat.id
    user_text = message.text

    # Показываем, что бот печатает
    bot.send_chat_action(chat_id, 'typing')

    try:
        # Загружаем историю чата
        history = load_chat_history(chat_id)

        # Добавляем сообщение пользователя
        history.append({
            "role": "user",
            "content": user_text
        })

        # Получаем модель пользователя и отправляем запрос в OpenAI
        user_model = get_user_model(chat_id)
        response = call_openai_api(user_model, history, max_tokens=1000)

        # Получаем ответ
        assistant_message = response.choices[0].message.content

        # Добавляем ответ в историю
        history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Сохраняем историю
        save_chat_history(chat_id, history)

        # Отправляем ответ пользователю
        bot.reply_to(message, assistant_message)

    except Exception as e:
        error_message = f"Произошла ошибка: {str(e)}"
        print(error_message)
        bot.reply_to(message, "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте команду /new для начала нового диалога.")


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Обработчик нажатий на кнопки меню"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    try:
        if call.data == "new_chat":
            # Очистка истории
            clear_chat_history(chat_id)
            bot.answer_callback_query(call.id, "✅ История очищена!")
            bot.edit_message_text(
                "✅ История диалога очищена. Начинаем новый разговор!",
                chat_id,
                message_id
            )

        elif call.data == "select_model":
            # Показать выбор модели
            current_model = get_user_model(chat_id)
            model_text = "🤖 Выберите модель:\n\n"

            for model_id, model_info in MODELS.items():
                status = "✅ Активна" if model_id == current_model else ""
                model_text += f"• {model_info['name']}\n"
                model_text += f"  Скорость: {model_info['speed']}\n"
                model_text += f"  {model_info['description']}\n"
                if status:
                    model_text += f"  {status}\n"
                model_text += "\n"

            markup = create_model_keyboard(current_model)
            bot.edit_message_text(model_text, chat_id, message_id, reply_markup=markup)

        elif call.data.startswith("model_"):
            # Выбор модели
            selected_model = call.data.replace("model_", "")

            if selected_model in MODELS:
                set_user_model(chat_id, selected_model)
                model_name = MODELS[selected_model]["name"]

                bot.answer_callback_query(call.id, f"✅ Модель изменена на {model_name}")

                # Обновляем сообщение с новой активной моделью
                model_text = "🤖 Выберите модель:\n\n"
                for model_id, model_info in MODELS.items():
                    status = "✅ Активна" if model_id == selected_model else ""
                    model_text += f"• {model_info['name']}\n"
                    model_text += f"  Скорость: {model_info['speed']}\n"
                    model_text += f"  {model_info['description']}\n"
                    if status:
                        model_text += f"  {status}\n"
                    model_text += "\n"

                markup = create_model_keyboard(selected_model)
                bot.edit_message_text(model_text, chat_id, message_id, reply_markup=markup)

        elif call.data == "back_to_menu":
            # Вернуться в главное меню
            current_model = get_user_model(chat_id)
            model_name = MODELS[current_model]["name"]

            menu_text = f"""
⚙️ Меню настроек

Текущая модель: {model_name}

Выберите действие:
            """
            markup = create_menu_keyboard()
            bot.edit_message_text(menu_text.strip(), chat_id, message_id, reply_markup=markup)

    except Exception as e:
        print(f"Error in callback handler: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")


if __name__ == '__main__':
    print("Бот запущен и готов к работе!")
    print(f"История чатов сохраняется в: {HISTORY_DIR.absolute()}")

    # Запускаем бота в режиме polling
    bot.infinity_polling()
