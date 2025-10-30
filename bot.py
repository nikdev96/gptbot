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

# Google Custom Search API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CX = os.getenv('GOOGLE_CX')

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
    "content": """You are a helpful assistant in a Telegram bot with access to real-time internet information.

IMPORTANT: You have access to the google_search function to find current information on the internet. When users ask about:
- Current weather, news, events
- Recent information, prices, schedules
- Any time-sensitive data
USE the google_search function to provide accurate, up-to-date answers based on the search results.

Format your responses using Markdown:
- Use **bold** for important words and key concepts
- Use `code` for technical terms, commands, or code snippets
- Use ```language for multi-line code blocks
- Use bullet points or numbered lists when listing items
- Use appropriate emojis sparingly and only when contextually relevant (e.g., 💡 for tips, ⚠️ for warnings, ✅ for confirmations, 📝 for notes, 🔍 for analysis)

Guidelines:
- Be concise and clear
- Structure your answers well
- Use emojis naturally, not in every sentence
- Make important information stand out with bold text
- ALWAYS use search results when provided - don't say you don't have access to real-time data"""
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


def google_search(query, num_results=5):
    """Поиск в Google через Custom Search API"""
    try:
        if not GOOGLE_API_KEY or not GOOGLE_CX or GOOGLE_CX == "your_search_engine_id_here":
            return "Google Search не настроен. Требуется GOOGLE_CX в .env файле."

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": query,
            "num": min(num_results, 10)  # API ограничивает до 10
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "items" not in data:
            return f"Ничего не найдено по запросу: {query}"

        results = []
        for i, item in enumerate(data["items"][:num_results], 1):
            title = item.get("title", "Без названия")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            results.append(f"{i}. **{title}**\n{snippet}\n{link}")

        return "\n\n".join(results)

    except Exception as e:
        print(f"Google Search error: {e}")
        return f"Ошибка поиска: {str(e)}"


# Определение инструментов (tools) для Function Calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Searches the internet via Google for current, real-time information. Use this function when users ask about weather, news, current events, prices, schedules, recent developments, or any time-sensitive information. Returns search results with titles, snippets, and links.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query in English (translate if needed). Be specific and include relevant keywords like 'current weather Bangkok', 'latest news OpenAI', etc."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-10). Default is 3.",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def call_openai_api(model, messages, max_tokens=4000, use_tools=True):
    """Универсальная функция вызова OpenAI API с правильными параметрами"""
    if model == "gpt-5":
        # GPT-5 требует max_completion_tokens и не поддерживает температуру
        # GPT-5 - reasoning модель, нужно больше токенов для размышлений + ответа
        params = {
            "model": model,
            "messages": messages,
            "max_completion_tokens": max_tokens
        }
        if use_tools:
            params["tools"] = TOOLS
            params["tool_choice"] = "auto"
        return client.chat.completions.create(**params)
    else:
        # Остальные модели используют стандартные параметры
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens
        }
        if use_tools:
            params["tools"] = TOOLS
            params["tool_choice"] = "auto"
        return client.chat.completions.create(**params)


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
👋 *Привет! Я ChatGPT бот*

Текущая модель: *{model_name}*

*📋 Доступные команды:*
`/start` или `/help` - показать это сообщение
`/menu` - открыть меню настроек
`/new` - начать новый диалог
`/image` - создать изображение 🎨

*✨ Что я умею:*
📝 Отвечать на текстовые сообщения
🖼 Анализировать изображения (отправь фото)
🎨 Генерировать изображения
💬 Поддерживать контекст разговора
⚡ Отвечать очень быстро!

💡 Просто отправь мне сообщение или фото!
    """
    bot.reply_to(message, welcome_text.strip(), parse_mode='Markdown')


@bot.message_handler(commands=['new'])
def new_conversation(message):
    """Обработчик команды /new - очистка истории"""
    chat_id = message.chat.id
    clear_chat_history(chat_id)
    bot.reply_to(message, "✅ История диалога очищена. Начинаем новый разговор!", parse_mode='Markdown')


@bot.message_handler(commands=['menu'])
def show_menu(message):
    """Обработчик команды /menu - показать меню"""
    chat_id = message.chat.id
    current_model = get_user_model(chat_id)
    model_name = MODELS[current_model]["name"]

    menu_text = f"""
⚙️ *Меню настроек*

Текущая модель: *{model_name}*

Выберите действие:
    """
    markup = create_menu_keyboard()
    bot.send_message(chat_id, menu_text.strip(), reply_markup=markup, parse_mode='Markdown')


@bot.message_handler(commands=['image', 'generate'])
def generate_image(message):
    """Обработчик команды /image - генерация изображения"""
    chat_id = message.chat.id

    # Получаем текст после команды
    command_parts = message.text.split(maxsplit=1)

    if len(command_parts) < 2:
        bot.reply_to(message,
            "🎨 Для генерации изображения укажите описание:\n\n"
            "Пример: `/image кот в космосе`\n"
            "Или: `/generate робот читает книгу`",
            parse_mode='Markdown')
        return

    prompt = command_parts[1]

    # Показываем, что бот работает
    status_message = bot.reply_to(message, "🎨 *Генерирую изображение...*\n\n⏱ Это может занять ~10 секунд", parse_mode='Markdown')

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
        caption_text = f"🎨 *Изображение готово!*\n\n📝 *Ваш запрос:* {prompt}\n\n💡 *Улучшенный промпт:*\n{revised_prompt[:200]}..."
        bot.send_photo(chat_id, image_url, caption=caption_text, parse_mode='Markdown')

    except Exception as e:
        error_message = f"Произошла ошибка при генерации изображения: {str(e)}"
        print(error_message)
        bot.edit_message_text(
            "❌ *Ошибка генерации изображения*\n\nПопробуйте изменить описание или повторить попытку позже.",
            chat_id,
            status_message.message_id,
            parse_mode='Markdown'
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
        response = call_openai_api(user_model, history)

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
        try:
            bot.reply_to(message, assistant_message, parse_mode='Markdown')
        except Exception as markdown_error:
            # Если Markdown не работает, отправляем без форматирования
            print(f"Markdown error: {markdown_error}")
            bot.reply_to(message, assistant_message)

    except Exception as e:
        error_message = f"Произошла ошибка при обработке изображения: {str(e)}"
        print(error_message)
        import traceback
        traceback.print_exc()
        bot.reply_to(message,
            "⚠️ *Ошибка анализа изображения*\n\n"
            "Попробуйте:\n"
            "• Отправить изображение ещё раз\n"
            "• Использовать `/new` для нового диалога",
            parse_mode='Markdown')


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
        print(f"[DEBUG] Using model: {user_model}")
        print(f"[DEBUG] History messages count: {len(history)}")

        response = call_openai_api(user_model, history)

        print(f"[DEBUG] Response type: {type(response)}")
        print(f"[DEBUG] Response.choices: {response.choices if hasattr(response, 'choices') else 'No choices'}")

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Проверяем, хочет ли модель вызвать функцию
        if tool_calls:
            print(f"[DEBUG] Tool calls detected: {len(tool_calls)}")

            # Добавляем ответ модели с tool_calls в историю
            history.append({
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            })

            # Выполняем вызовы функций
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"[DEBUG] Calling function: {function_name} with args: {function_args}")

                if function_name == "google_search":
                    function_response = google_search(**function_args)
                else:
                    function_response = f"Неизвестная функция: {function_name}"

                print(f"[DEBUG] Function response: {function_response[:200]}...")

                # Добавляем результат функции в историю
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_response
                })

            # Делаем второй запрос с результатами функций
            second_response = call_openai_api(user_model, history, use_tools=False)
            assistant_message = second_response.choices[0].message.content
        else:
            # Обычный ответ без tool calls
            assistant_message = response_message.content

        print(f"[DEBUG] Raw assistant_message: '{assistant_message}' (type: {type(assistant_message)})")

        # Проверяем, что ответ не пустой
        if not assistant_message or assistant_message.strip() == "":
            print(f"[ERROR] Empty response from OpenAI. Full response: {response}")
            assistant_message = "Извините, я не смог сгенерировать ответ. Попробуйте еще раз."

        print(f"[DEBUG] Assistant message length: {len(assistant_message) if assistant_message else 0}")
        print(f"[DEBUG] Assistant message preview: {assistant_message[:100] if assistant_message else 'None'}")

        # Добавляем финальный ответ в историю (если не было tool calls)
        if not tool_calls:
            history.append({
                "role": "assistant",
                "content": assistant_message
            })
        else:
            # Если были tool calls, добавляем финальный ответ
            history.append({
                "role": "assistant",
                "content": assistant_message
            })

        # Сохраняем историю
        save_chat_history(chat_id, history)

        # Отправляем ответ пользователю
        try:
            bot.reply_to(message, assistant_message, parse_mode='Markdown')
        except Exception as markdown_error:
            # Если Markdown не работает, отправляем без форматирования
            print(f"Markdown error: {markdown_error}")
            bot.reply_to(message, assistant_message)

    except Exception as e:
        error_message = f"Произошла ошибка: {str(e)}"
        print(error_message)
        import traceback
        traceback.print_exc()
        bot.reply_to(message,
            "⚠️ *Ошибка обработки сообщения*\n\n"
            "Попробуйте:\n"
            "• Переформулировать вопрос\n"
            "• Использовать `/new` для нового диалога",
            parse_mode='Markdown')


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
            model_text = "🤖 *Выберите модель:*\n\n"

            for model_id, model_info in MODELS.items():
                status = "✅ *Активна*" if model_id == current_model else ""
                model_text += f"• *{model_info['name']}*\n"
                model_text += f"  Скорость: `{model_info['speed']}`\n"
                model_text += f"  {model_info['description']}\n"
                if status:
                    model_text += f"  {status}\n"
                model_text += "\n"

            markup = create_model_keyboard(current_model)
            bot.edit_message_text(model_text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')

        elif call.data.startswith("model_"):
            # Выбор модели
            selected_model = call.data.replace("model_", "")

            if selected_model in MODELS:
                set_user_model(chat_id, selected_model)
                model_name = MODELS[selected_model]["name"]

                bot.answer_callback_query(call.id, f"✅ Модель изменена на {model_name}")

                # Обновляем сообщение с новой активной моделью
                model_text = "🤖 *Выберите модель:*\n\n"
                for model_id, model_info in MODELS.items():
                    status = "✅ *Активна*" if model_id == selected_model else ""
                    model_text += f"• *{model_info['name']}*\n"
                    model_text += f"  Скорость: `{model_info['speed']}`\n"
                    model_text += f"  {model_info['description']}\n"
                    if status:
                        model_text += f"  {status}\n"
                    model_text += "\n"

                markup = create_model_keyboard(selected_model)
                bot.edit_message_text(model_text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')

        elif call.data == "back_to_menu":
            # Вернуться в главное меню
            current_model = get_user_model(chat_id)
            model_name = MODELS[current_model]["name"]

            menu_text = f"""
⚙️ *Меню настроек*

Текущая модель: *{model_name}*

Выберите действие:
            """
            markup = create_menu_keyboard()
            bot.edit_message_text(menu_text.strip(), chat_id, message_id, reply_markup=markup, parse_mode='Markdown')

    except Exception as e:
        print(f"Error in callback handler: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")


if __name__ == '__main__':
    print("Бот запущен и готов к работе!")
    print(f"История чатов сохраняется в: {HISTORY_DIR.absolute()}")

    # Запускаем бота в режиме polling
    bot.infinity_polling()
