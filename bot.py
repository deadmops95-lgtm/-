import os
import random
import telebot
from google import genai
from google.genai import types as genai_types
from telebot import types

# Токен вашего Telegram-бота
TOKEN = "8449752382:AAHrLDNWaRQkFlkJldiqbzJ3e2cLW7QKt9c"

# Ваш API-ключ от Google AI Studio (Gemini)
GEMINI_API_KEY = "AQ.Ab8RN6LTHk5DZql5j-7s4mGkMA8c4JYL_C1c_lj66VhvIV8dAw"

bot = telebot.TeleBot(TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

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
      "🤖☠️ **Нейросетевой гороскоп с жестким сарказмом запущен!**\n\nИскусственный"
      " интеллект прямо сейчас придумает для тебя едкое предсказание. Выбирай"
      " свой знак:",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("sign_"))
def callback_inline(call):
  sign = call.data.split("_")[1]

  bot.answer_callback_query(call.id, "ИИ придумывает гадости...")

  # Промпт (запрос) для нейросети
  prompt = (
      f"Напиши короткий, очень саркастичный, едкий и смешной гороскоп на"
      f" сегодня для знака зодиака {sign}. Используй черный юмор, иронию,"
      f" высмей типичные слабости этого знака. Не пиши лишних вступлений,"
      f" сразу текст предсказания (объемом в 2-3 предложения)."
  )

  try:
    # Запрос к Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    prediction = response.text
  except Exception as e:
    prediction = (
        "Звезды сегодня молчат, потому что ИИ устал от твоих запросов. Попробуй"
        " позже."
    )

  # Отправляем результат пользователю
  bot.send_message(
      call.message.chat.id,
      f"🔥 **Гороскоп для {sign}:**\n\n{prediction}\n\n*Хочешь еще порцию"
      " боли? Жми /start*",
      parse_mode="Markdown",
  )


print("Бот с ИИ успешно запущен!")
bot.polling(none_stop=True)
