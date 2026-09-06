import random
import telebot
from telebot import types

TOKEN = "8449752382:AAHrLDNWaRQkFlkJldiqbzJ3e2cLW7QKt9c"

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

PREDICTIONS = [
    "Сегодня отличный день для новых начинаний и смелых идей!",
    "Звезды советуют уделить время отдыху и расслаблению в кругу близких.",
    "Возможны неожиданные приятные финансовые сюрпризы.",
    "Отличный момент, чтобы проявить лидерские качества на работе или учебе.",
    "Прислушайтесь к своей интуиции — она подскажет верный ответ в сложной ситуации.",
    "День принесет много энергии. Направьте ее на спорт или творчество.",
    "Будьте открыты для общения: сегодня вы можете встретить интересного человека.",
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
      "✨ Привет! Я бот-гороскоп.\n\nВыбери свой знак зодиака ниже, чтобы узнать"
      " предсказание на сегодня:",
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("sign_"))
def callback_inline(call):
  sign = call.data.split("_")[1]
  prediction = random.choice(PREDICTIONS)

  bot.answer_callback_query(call.id)
  bot.send_message(
      call.message.chat.id,
      f"🔮 **Гороскоп для {sign} на сегодня:**\n\n{prediction}\n\n*Хочешь"
      " узнать еще? Напиши /start*",
      parse_mode="Markdown",
  )


print("Бот успешно запущен и ждет сообщения...")
bot.polling(none_stop=True)
