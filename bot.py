import asyncio
import os
import random
import sqlite3
import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8542022207:AAHc-j-B51pRwZSJHblIs33OTGD0eUvzYo0"
ADMIN_USERNAME = "Prokudin95"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Вспомогательная функция для авто-удаления сообщений через N секунд в группах
async def safe_delete_message(message: types.Message, delay: int = 15):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        coins INTEGER DEFAULT 100,
        pokeballs INTEGER DEFAULT 5,
        potions INTEGER DEFAULT 2,
        last_bonus TEXT DEFAULT '',
        last_lottery TEXT DEFAULT ''
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_pokemons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        pokemon_name TEXT,
        pokemon_id INTEGER,
        level INTEGER DEFAULT 1,
        hp INTEGER DEFAULT 100,
        max_hp INTEGER DEFAULT 100,
        photo_url TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gyms (
        gym_id INTEGER PRIMARY KEY,
        gym_name TEXT,
        holder_id INTEGER,
        holder_name TEXT,
        pokemon_name TEXT
    )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM gyms")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO gyms VALUES (1, 'Стадион Канто (Огонь)', NULL, 'Вакантно', '-')")
        cursor.execute("INSERT INTO gyms VALUES (2, 'Стадион Джото (Вода)', NULL, 'Вакантно', '-')")
        cursor.execute("INSERT INTO gyms VALUES (3, 'Стадион Хоэнн (Трава)', NULL, 'Вакантно', '-')")
        
    conn.commit()
    conn.close()

init_db()

def is_admin(user_username: str) -> bool:
    if not user_username:
        return False
    return user_username.lower() == ADMIN_USERNAME.lower()

# --- КЛАВИАТУРА ---
def main_menu_keyboard():
    kb = [
        [types.KeyboardButton(text="🗺 Исследовать карту"), types.KeyboardButton(text="🎒 Мой инвентарь")],
        [types.KeyboardButton(text="⚔️ Стадионы (Арена)"), types.KeyboardButton(text="👥 Мои покемоны")],
        [types.KeyboardButton(text="🏪 Магазин"), types.KeyboardButton(text="🏆 Рейтинг")],
        [types.KeyboardButton(text="🎁 Ежедневный бонус"), types.KeyboardButton(text="🎰 Лотерея")],
        [types.KeyboardButton(text="⚔️ PvP Дуэль"), types.KeyboardButton(text="🐉 Рейд на Босса")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
    conn.close()
    
    msg = await message.answer(
        f"Привет, {message.from_user.first_name}! Добро пожаловать в мир Покемонов!\n"
        "Играй прямо в чатах: лови покемонов, качай их, участвуй в рейдах и захватывай стадионы!",
        reply_markup=main_menu_keyboard()
    )
    # Если бот добавлен в группу, можно автоматически удалять приветствие через время
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(msg, 20))

# --- РАСШИРЕННЫЕ АДМИН-КОМАНДЫ ДЛЯ @Prokudin95 ---
@dp.message(Command("add_money"))
async def cmd_add_money(message: types.Message):
    if not is_admin(message.from_user.username):
        return await message.answer("У вас нет прав администратора.")
    args = message.text.split()
    if len(args) < 3:
        return await message.answer("Использование: /add_money [ID_юзера] [сумма]")
    target_id, amount = int(args[1]), int(args[2])
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, target_id))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Админ-права: Пользователю {target_id} добавлено {amount} монет.")

@dp.message(Command("add_item"))
async def cmd_add_item(message: types.Message):
    if not is_admin(message.from_user.username):
        return await message.answer("У вас нет прав администратора.")
    # /add_item [ID] [pokeballs/potions] [кол-во]
    args = message.text.split()
    if len(args) < 4:
        return await message.answer("Использование: /add_item [ID] [pokeballs или potions] [количество]")
    target_id, item_type, amount = int(args[1]), args[2], int(args[3])
    
    if item_type not in ["pokeballs", "potions"]:
        return await message.answer("Доступные предметы: pokeballs или potions")
        
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {item_type} = {item_type} + ? WHERE user_id = ?", (amount, target_id))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Админ-права: Пользователю {target_id} добавлено {amount} шт. ({item_type}).")

@dp.message(Command("give_all"))
async def cmd_give_all(message: types.Message):
    if not is_admin(message.from_user.username):
        return await message.answer("У вас нет прав администратора.")
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("Использование: /give_all [текст награды]")
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + 500, pokeballs = pokeballs + 10, potions = potions + 5")
    conn.commit()
    conn.close()
    await message.answer(f"📦 Массовая выдача всем игрокам!\nНаграда: {args[1]} (+500 монет, +10 покеболов, +5 зелий)")

# --- БАЗА ПОКЕМОНОВ (СТАТИЧНЫЕ КАРТИНКИ ВМЕСТО ГИФОК) ---
POKEMON_DATABASE = [
    # 1 пок
    (1, "Bulbasaur", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/1.png", 2, "Ivysaur", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/2.png"),
    (4, "Charmander", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/4.png", 5, "Charmeleon", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/5.png"),
    (7, "Squirtle", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/7.png", 8, "Wartortle", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/8.png"),
    (25, "Pikachu", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png", 26, "Raichu", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/26.png"),
    (150, "Mewtwo", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/150.png", 0, "", ""),
    # 2 пок
    (152, "Chikorita", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/152.png", 0, "", ""),
    (155, "Cyndaquil", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/155.png", 0, "", ""),
    (158, "Totodile", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/158.png", 0, "", ""),
    # 3 пок
    (252, "Treecko", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/252.png", 0, "", ""),
    (255, "Torchic", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/255.png", 0, "", ""),
    (258, "Mudkip", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/258.png", 0, "", ""),
    # 4 пок
    (387, "Turtwig", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/387.png", 0, "", ""),
    (390, "Chimchar", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/390.png", 0, "", ""),
    (393, "Piplup", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/393.png", 0, "", ""),
    # 5 пок
    (495, "Snivy", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/495.png", 0, "", ""),
    (498, "Tepig", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/498.png", 0, "", ""),
    (501, "Oshawott", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/501.png", 0, "", "")
]

# --- ИССЛЕДОВАНИЕ КАРТЫ ---
@dp.message(F.text == "🗺 Исследовать карту")
async def explore_map(message: types.Message):
    user_id = message.from_user.id
    event = random.choice(["pokemon", "pokemon", "coins", "empty"])
    
    if event == "coins":
        conn = sqlite3.connect("pokemon_bot.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET coins = coins + 35 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        msg = await message.answer("🗺 Вы нашли тайник и получили **35 монет**! 🪙")
        if message.chat.type != "private":
            asyncio.create_task(safe_delete_message(message, 5))
            asyncio.create_task(safe_delete_message(msg, 15))
        return
    
    if event == "empty":
        msg = await message.answer("🗺 Вы бродили по высокой траве, но никого не встретили.")
        if message.chat.type != "private":
            asyncio.create_task(safe_delete_message(message, 5))
            asyncio.create_task(safe_delete_message(msg, 15))
        return

    poke = random.choice(POKEMON_DATABASE)
    poke_id, poke_name, poke_photo = poke[0], poke[1], poke[2]
    
    kb = [[types.InlineKeyboardButton(text="🎯 Бросить покебол", callback_data=f"catch_{poke_id}")]]
    sent_msg = await message.answer_photo(
        photo=poke_photo,
        caption=f"⚡️ Дикий **{poke_name}** преградил вам путь в чате!",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(message, 5))

@dp.callback_query(F.data.startswith("catch_"))
async def catch_pokemon(callback: types.CallbackQuery):
    poke_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    poke_data = next((p for p in POKEMON_DATABASE if p[0] == poke_id), None)
    if not poke_data:
        return await callback.answer("Ошибка покемона", show_alert=True)
    
    poke_name, poke_photo = poke_data[1], poke_data[2]
    
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT pokeballs FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if not res or res[0] <= 0:
        conn.close()
        return await callback.answer("❌ У вас нет покеболов! Купите их в магазине.", show_alert=True)
    
    cursor.execute("UPDATE users SET pokeballs = pokeballs - 1 WHERE user_id = ?", (user_id,))
    
    if random.random() < 0.7:
        cursor.execute("INSERT INTO user_pokemons (user_id, pokemon_name, pokemon_id, level, hp, max_hp, photo_url) VALUES (?, ?, ?, 1, 100, 100, ?)",
                       (user_id, poke_name, poke_id, poke_photo))
        conn.commit()
        conn.close()
        await callback.message.edit_caption(caption=f"🎉 Успех! Вы поймали **{poke_name}** в коллекцию!")
    else:
        conn.commit()
        conn.close()
        await callback.message.edit_caption(caption=f"💨 О нет! **{poke_name}** вырвался и убежал...")
    
    # Автоудаление сообщения поимки через 20 секунд в чатах
    asyncio.create_task(safe_delete_message(callback.message, 20))
    await callback.answer()

# --- МОИ ПОКЕМОНЫ И ЭВОЛЮЦИЯ ---
@dp.message(F.text == "👥 Мои покемоны")
async def show_my_pokemons(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, pokemon_name, pokemon_id, level, hp, max_hp FROM user_pokemons WHERE user_id = ?", (user_id,))
    pokemons = cursor.fetchall()
    conn.close()
    
    if not pokemons:
        msg = await message.answer("У вас пока нет покемонов. Исследуйте карту!")
        if message.chat.type != "private":
            asyncio.create_task(safe_delete_message(message, 5))
            asyncio.create_task(safe_delete_message(msg, 15))
        return
    
    text = ["🎒 **Ваша команда покемонов:**\n"]
    kb = []
    for pid, p_name, poke_id, p_lvl, p_hp, p_max_hp in pokemons:
        text.append(f"🆔 ID#{pid} | **{p_name}** (Ур. {p_lvl} | HP: {p_hp}/{p_max_hp})\n")
        kb.append([types.InlineKeyboardButton(text=f"⬆️ Прокачать {p_name} (ID:{pid})", callback_data=f"lvlup_{pid}")])
        
        p_info = next((p for p in POKEMON_DATABASE if p[0] == poke_id), None)
        if p_info and p_info[3] > 0 and p_lvl >= 3:
            kb.append([types.InlineKeyboardButton(text=f"✨ Эволюция в {p_info[4]} (Нужен 3 ур.)", callback_data=f"evolu_{pid}")])

    msg = await message.answer("".join(text), reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(message, 5))
        asyncio.create_task(safe_delete_message(msg, 30))

@dp.callback_query(F.data.startswith("lvlup_"))
async def level_up_pokemon(callback: types.CallbackQuery):
    poke_db_id = int(callback.data.split("_")[1])
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE user_pokemons SET level = level + 1, max_hp = max_hp + 25, hp = max_hp + 25 WHERE id = ?", (poke_db_id,))
    conn.commit()
    cursor.execute("SELECT pokemon_name, level FROM user_pokemons WHERE id = ?", (poke_db_id,))
    res = cursor.fetchone()
    conn.close()
    
    await callback.answer(f"Покемон {res[0]} прокачан до {res[1]} уровня!", show_alert=True)
    await callback.message.edit_text(f"✅ Покемон **{res[0]}** успешно прокачан до **{res[1]}** уровня!")
    asyncio.create_task(safe_delete_message(callback.message, 15))

@dp.callback_query(F.data.startswith("evolu_"))
async def evolve_pokemon(callback: types.CallbackQuery):
    poke_db_id = int(callback.data.split("_")[1])
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT pokemon_id, level FROM user_pokemons WHERE id = ?", (poke_db_id,))
    poke = cursor.fetchone()
    
    if not poke or poke[1] < 3:
        conn.close()
        return await callback.answer("Для эволюции нужен минимум 3 уровень!", show_alert=True)
    
    p_info = next((p for p in POKEMON_DATABASE if p[0] == poke[0]), None)
    if not p_info or p_info[3] == 0:
        conn.close()
        return await callback.answer("У этого покемона нет эволюции.", show_alert=True)
        
    new_id, new_name, new_photo = p_info[3], p_info[4], p_info[5]
    cursor.execute("UPDATE user_pokemons SET pokemon_id = ?, pokemon_name = ?, photo_url = ?, max_hp = max_hp + 50, hp = max_hp + 50 WHERE id = ?",
                   (new_id, new_name, new_photo, poke_db_id))
    conn.commit()
    conn.close()
    
    sent = await callback.message.answer_photo(
        photo=new_photo,
        caption=f"✨ Потрясающе! Ваш покемон успешно эволюционировал в **{new_name}**!"
    )
    asyncio.create_task(safe_delete_message(sent, 20))
    await callback.answer()

# --- ИНВЕНТАРЬ И ЗЕЛИЯ ---
@dp.message(F.text == "🎒 Мой инвентарь")
async def show_inventory(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins, pokeballs, potions FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return await message.answer("Сначала введите /start")
    
    coins, pokeballs, potions = user
    kb = []
    if potions > 0:
        kb.append([types.InlineKeyboardButton(text="🧪 Использовать зелье лечения (+50 HP)", callback_data="use_potion")])
        
    msg = await message.answer(
        f"🎒 **Ваш инвентарь:**\n\n"
        f"🪙 Монеты: {coins}\n"
        f"🔴 Покеболы: {pokeballs}\n"
        f"🧪 Зелья лечения: {potions}",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb) if kb else None
    )
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(message, 5))
        asyncio.create_task(safe_delete_message(msg, 20))

@dp.callback_query(F.data == "use_potion")
async def use_potion(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT potions FROM users WHERE user_id = ?", (user_id,))
    potions = cursor.fetchone()[0]
    if potions <= 0:
        conn.close()
        return await callback.answer("У вас нет зелий!", show_alert=True)
        
    cursor.execute("SELECT id, pokemon_name, hp, max_hp FROM user_pokemons WHERE user_id = ? AND hp < max_hp LIMIT 1", (user_id,))
    target = cursor.fetchone()
    
    if not target:
        conn.close()
        return await callback.answer("Все ваши покемоны полностью здоровы!", show_alert=True)
        
    p_id, p_name, p_hp, p_max_hp = target
    new_hp = min(p_max_hp, p_hp + 50)
    
    cursor.execute("UPDATE users SET potions = potions - 1 WHERE user_id = ?", (user_id,))
    cursor.execute("UPDATE user_pokemons SET hp = ? WHERE id = ?", (new_hp, p_id))
    conn.commit()
    conn.close()
    
    await callback.answer(f"Покемон {p_name} вылечен!", show_alert=True)
    await callback.message.edit_text(f"🧪 Покемон **{p_name}** восстановил здоровье до {new_hp}/{p_max_hp} HP!")
    asyncio.create_task(safe_delete_message(callback.message, 15))

# --- МАГАЗИН ---
@dp.message(F.text == "🏪 Магазин")
async def show_shop(message: types.Message):
    kb = [
        [types.InlineKeyboardButton(text="Купить 5 покеболов (50 монет)", callback_data="buy_pokeballs")],
        [types.InlineKeyboardButton(text="Купить 2 зелья (30 монет)", callback_data="buy_potions")]
    ]
    msg = await message.answer("🏪 **Магазин предметов:**\nВыберите товар:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(message, 5))
        asyncio.create_task(safe_delete_message(msg, 20))

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    coins = cursor.fetchone()[0]
    
    if action == "buy_pokeballs":
        if coins < 50:
            conn.close()
            return await callback.answer("❌ Не хватает монет!", show_alert=True)
        cursor.execute("UPDATE users SET coins = coins - 50, pokeballs = pokeballs + 5 WHERE user_id = ?", (user_id,))
        msg = "Куплено 5 покеболов!"
    elif action == "buy_potions":
        if coins < 30:
            conn.close()
            return await callback.answer("❌ Не хватает монет!", show_alert=True)
        cursor.execute("UPDATE users SET coins = coins - 30, potions = potions + 2 WHERE user_id = ?", (user_id,))
        msg = "Куплено 2 зелья лечения!"
        
    conn.commit()
    conn.close()
    await callback.answer(msg, show_alert=True)
    await callback.message.edit_text(msg)
    asyncio.create_task(safe_delete_message(callback.message, 15))

# --- ЕЖЕДНЕВНЫЙ БОНУС ---
@dp.message(F.text == "🎁 Ежедневный бонус")
async def daily_bonus(message: types.Message):
    user_id = message.from_user.id
    today = str(datetime.date.today())
    
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT last_bonus FROM users WHERE user_id = ?", (user_id,))
    last_bonus = cursor.fetchone()[0]
    
    if last_bonus == today:
        msg = await message.answer("🎁 Вы уже получали бонус сегодня! Приходите завтра.")
        if message.chat.type != "private":
            asyncio.create_task(safe_delete_message(message, 5))
            asyncio.create_task(safe_delete_message(msg, 10))
        return
        
    cursor.execute("UPDATE users SET coins = coins + 100, pokeballs = pokeballs + 3, last_bonus = ? WHERE user_id = ?", (today, user_id))
    conn.commit()
    conn.close()
    
    msg = await message.answer("🎉 Ежедневный бонус получен:\n🪙 **+100 монет**\n🔴 **+3 покебола**!")
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(message, 5))
        asyncio.create_task(safe_delete_message(msg, 15))

# --- ЛОТЕРЕЯ ---
@dp.message(F.text == "🎰 Лотерея")
async def lottery(message: types.Message):
    user_id = message.from_user.id
    today = str(datetime.date.today())
    
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT last_lottery FROM users WHERE user_id = ?", (user_id,))
    last_lottery = cursor.fetchone()[0]
    
    if last_lottery == today:
        msg = await message.answer("🎰 Вы уже крутили лотерею сегодня! Возвращайтесь завтра.")
        if message.chat.type != "private":
            asyncio.create_task(safe_delete_message(message, 5))
            asyncio.create_task(safe_delete_message(msg, 10))
        return
        
    cursor.execute("UPDATE users SET last_lottery = ? WHERE user_id = ?", (today, user_id))
    reward_type = random.choices(["coins", "pokeballs", "nothing"], weights=[50, 40, 10], k=1)[0]
    
    if reward_type == "coins":
        prize = random.randint(50, 200)
        cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (prize, user_id))
        text = f"🎰 Вы выиграли **{prize} монет**! 🪙"
    elif reward_type == "pokeballs":
        prize = random.randint(2, 6)
        cursor.execute("UPDATE users SET pokeballs = pokeballs + ? WHERE user_id = ?", (prize, user_id))
        text = f"🎰 Удача! Вы выиграли **{prize} покебола**! 🔴"
    else:
        text = "🎰 Эх, пустой сектор. В следующий раз повезет!"
        
    conn.commit()
    conn.close()
    msg = await message.answer(text)
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(message, 5))
        asyncio.create_task(safe_delete_message(msg, 15))

# --- PVP ДУЭЛЬ ---
@dp.message(F.text == "⚔️ PvP Дуэль")
async def pvp_duel(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT pokemon_name, level FROM user_pokemons WHERE user_id = ? ORDER BY level DESC LIMIT 1", (user_id,))
    my_poke = cursor.fetchone()
    if not my_poke:
        msg = await message.answer("У вас нет покемонов для дуэли! Сначала поймайте их на карте.")
        if message.chat.type != "private":
            asyncio.create_task(safe_delete_message(message, 5))
            asyncio.create_task(safe_delete_message(msg, 15))
        return
        
    cursor.execute("SELECT username FROM users WHERE user_id != ? ORDER BY RANDOM() LIMIT 1", (user_id,))
    rival = cursor.fetchone()
    rival_name = rival[0] if rival and rival[0] else "Элитный тренер"
    conn.close()
    
    win = random.choice([True, False])
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    
    if win:
        cursor.execute("UPDATE users SET coins = coins + 50 WHERE user_id = ?", (user_id,))
        result = f"🏆 В дуэли ваш **{my_poke[0]}** победил покемона тренера **@{rival_name}**!\nНаграда: **50 монет** 🪙!"
    else:
        result = f"💥 Ваш **{my_poke[0]}** проиграл в упорном бою тренеру **@{rival_name}**."
        
    conn.commit()
    conn.close()
    msg = await message.answer(result)
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(message, 5))
        asyncio.create_task(safe_delete_message(msg, 20))

# --- ИНТЕРЕСНАЯ ФИШКА ДЛЯ ЧАТОВ: РЕЙД НА МИРОВОГО БОССА ---
@dp.message(F.text == "🐉 Рейд на Босса")
async def world_boss_raid(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT pokemon_name, level FROM user_pokemons WHERE user_id = ? ORDER BY level DESC LIMIT 1", (user_id,))
    my_poke = cursor.fetchone()
    
    if not my_poke:
        msg = await message.answer("У вас нет покемонов для рейда на босса!")
        if message.chat.type != "private":
            asyncio.create_task(safe_delete_message(message, 5))
            asyncio.create_task(safe_delete_message(msg, 15))
        return
    conn.close()
    
    # Легендарный босс
    boss_name = "Легендарный Rayquaza"
    boss_photo = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/384.png"
    
    # Шанс победить зависит от уровня покемона
    success_chance = 0.3 + (my_poke[1] * 0.1) # Чем выше уровень, тем выше шанс
    win = random.random() < min(success_chance, 0.85)
    
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    
    if win:
        cursor.execute("UPDATE users SET coins = coins + 200, potions = potions + 2 WHERE user_id = ?", (user_id,))
        caption = f"🔥 ГРАНДИОЗНАЯ ПОБЕДА!\nВаш **{my_poke[0]}** (Ур.{my_poke[1]}) совладал с мощью босса **{boss_name}**!\nНаграда чата: **200 монет и 2 зелья**!"
    else:
        caption = f"💀 РЕЙД ПРОВАЛЕН...\nБосс **{boss_name}** оказался слишком силен для **{my_poke[0]}** (Ур.{my_poke[1]}). Прокачайте покемона и попробуйте снова!"
        
    conn.commit()
    conn.close()
    
    sent = await message.answer_photo(photo=boss_photo, caption=caption)
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(message, 5))
        asyncio.create_task(safe_delete_message(sent, 25))

# --- СТАДИОНЫ И РЕЙТИНГ ---
@dp.message(F.text == "⚔️ Стадионы (Арена)")
async def show_gyms(message: types.Message):
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT gym_id, gym_name, holder_name, pokemon_name FROM gyms")
    gyms = cursor.fetchall()
    conn.close()
    
    text = "🏟 **Список стадионов мира Покемонов:**\n\n"
    for gym_id, gym_name, holder_name, pokemon_name in gyms:
        text += f"🔹 **{gym_name}**\n👑 Лидер: {holder_name}\n🐾 Защитник: {pokemon_name}\n\n"
    
    kb = [
        [types.InlineKeyboardButton(text="Захватить Стадион 1", callback_data="gym_1")],
        [types.InlineKeyboardButton(text="Захватить Стадион 2", callback_data="gym_2")],
        [types.InlineKeyboardButton(text="Захватить Стадион 3", callback_data="gym_3")]
    ]
    msg = await message.answer(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(message, 5))
        asyncio.create_task(safe_delete_message(msg, 25))

@dp.callback_query(F.data.startswith("gym_"))
async def process_gym_battle(callback: types.CallbackQuery):
    gym_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, pokemon_name FROM user_pokemons WHERE user_id = ?", (user_id,))
    my_pokemons = cursor.fetchall()
    
    if not my_pokemons:
        conn.close()
        return await callback.answer("У вас нет покемонов для битвы!", show_alert=True)
    
    fighter = my_pokemons[0][1]
    cursor.execute("UPDATE gyms SET holder_id = ?, holder_name = ?, pokemon_name = ? WHERE gym_id = ?", 
                   (user_id, username, fighter, gym_id))
    conn.commit()
    conn.close()
    
    await callback.message.edit_text(f"🎉 Победа! Ваш покемон **{fighter}** захватил стадион и стал его новым Лидером!")
    asyncio.create_task(safe_delete_message(callback.message, 15))
    await callback.answer()

@dp.message(F.text == "🏆 Рейтинг")
async def show_rating(message: types.Message):
    conn = sqlite3.connect("pokemon_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, COUNT(p.id) as count 
        FROM users u 
        LEFT JOIN user_pokemons p ON u.user_id = p.user_id 
        GROUP BY u.user_id 
        ORDER BY count DESC 
        LIMIT 5
    """)
    top_users = cursor.fetchall()
    conn.close()
    
    text = "🏆 **Топ-5 тренеров чата:**\n\n"
    for idx, (uname, count) in enumerate(top_users, 1):
        name = uname if uname else "Тренер"
        text += f"{idx}. @{name} — {count} покемонов\n"
        
    msg = await message.answer(text)
    if message.chat.type != "private":
        asyncio.create_task(safe_delete_message(message, 5))
        asyncio.create_task(safe_delete_message(msg, 20))

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
