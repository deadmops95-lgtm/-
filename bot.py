import os
import random
import requests
import telebot
from telebot import types

# Токен вашего Telegram-бота
TOKEN = "8449752382:AAHrLDNWaRQkFlkJldiqbzJ3e2cLW7QKt9c"

# Ваш ключ Groq
GROQ_API_KEY = "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"

bot = telebot.TeleBot(TOKEN)

ZODIAC_SIGNS = [
    "♈️ Овен",
    "♉️ Телец",
    "♊️ Близнецы",
    "♋️ Рак",
    "♌️ Лев",
    "♍️ Дева",
    "♎️ Весы",
    "♏️ Скорпион",
    "♐️ Стрелец",
    "♑️ Козерог",
    "♒️ Водолей",
    "♓️ Рыбы",
]


@bot.message_handler(commands=["start"])
def send_welcome(message):
  markup = types.InlineKeyboardMarkup(row_width=2)
  buttons = [
      types.InlineKeyboardButton(sign, callback_data=f"sign_{sign}")
      for sign in ZODIAC_SIGNS
  ]
  markup.add(*buttons)

  bot.send_message(
      message.chat.id,
      "🤖☠️ **Бот с саркастичным гороскопом (через Groq) запущен!**\n\nВыбирай"
      " свой знак, чтобы узнать всю правду:",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("sign_"))
def callback_inline(call):
  sign = call.data.split("_")[1]
  bot.answer_callback_query(call.id, "Нейросеть генерирует яд...")

  prompt = (
      f"Напиши короткий, очень саркастичный, едкий и смешной гороскоп на"
      f" сегодня для знака зодиака {sign}. Используй черный юмор, иронию,"
      f" высмей типичные слабости этого знака. Не пиши лишних вступлений,"
      f" сразу текст предсказания (объемом в 2-3 предложения)."
  )

  prediction = ""
  try:
    # Запрос к Groq API
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
    }
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=data,
        headers=headers,
        timeout=10,
    )

    if response.status_code == 200:
      result = response.json()
      prediction = result["choices"][0]["message"]["content"]
    else:
      prediction = "Звезды временно в шоке от твоих запросов. Попробуй позже."
  except Exception as e:
    prediction = "Ошибка связи с космосом. Попробуй еще раз."

  bot.send_message(
      call.message.chat.id,
      f"🔥 **Гороскоп для {sign}:**\n\n{prediction}\n\n*Хочешь еще порцию"
      " боли? Жми /start*",
      parse_mode="Markdown",
  )


print("Бот через Groq успешно запущен!")
bot.polling(none_stop=True)
