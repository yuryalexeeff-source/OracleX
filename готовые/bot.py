import os
import random
import asyncio
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ====== Предсказания ======
tarot_cards = {
    "Маг": {"upright": "Начало нового проекта, энергия для действий, уверенность в себе.",
            "reversed": "Задержки, неправильное использование энергии, обман, сомнения."},
    "Императрица": {"upright": "Творчество, забота, рост и плодородие, гармония в семье.",
                    "reversed": "Лень, застой, отсутствие заботы и внимания, конфликты дома."},
    "Башня": {"upright": "Внезапные перемены, разрушение старого, очищение.",
              "reversed": "Отказ принимать перемены, сопротивление судьбе, страх нового."},
    "Солнце": {"upright": "Успех, радость, новые возможности, вдохновение.",
               "reversed": "Несерьёзное отношение, задержки успеха, неуверенность."},
    "Луна": {"upright": "Интуиция, тайны, скрытые факторы, творчество ночью.",
             "reversed": "Иллюзии, заблуждения, страхи, потеря направления."}
}

runes = {
    "Феху": "Богатство, ресурсы, успех в делах, изобилие и прибыль.",
    "Уруз": "Сила, энергия, здоровье, стойкость, упорство.",
    "Ансуз": "Общение, знания, советы мудрецов, вдохновение.",
    "Тейваз": "Смелость, победа в сражении, защита, честь.",
    "Йера": "Циклы, плоды усилий, прогресс, урожай и вознаграждение."
}

oracle = {
    "Путь": "Время новых начинаний, действуй смело, открывай новые горизонты.",
    "Баланс": "Нужно найти гармонию между делом и отдыхом, прислушайся к себе.",
    "Свет": "Оптимизм и вера приведут к успеху, будь честен с собой.",
    "Тень": "Будь осторожен, избегай обмана, обрати внимание на скрытые сигналы.",
    "Сила духа": "Держись своих принципов, даже если тяжело, внутренние ресурсы помогут."
}

# ====== Новые гадания ======
cards_deck = [f"{rank} {suit}" for suit in ["♥", "♦", "♣", "♠"] for rank in list(range(6, 11)) + ["J","Q","K","A"]]
dice_faces = [1,2,3,4,5,6]

# Бесконечные ответы
paper_answers = ["Да", "Нет", "Возможно", "Скоро", "Не сейчас", "Скорее всего", "Не могу сказать", "Определенно да", "Определенно нет", "Попробуй позже"]
matches_answers = ["Да", "Нет", "Скоро", "Не знаю", "Попробуй позже", "Скорее да", "Скорее нет"]
flower_answers = ["Любит", "Не любит", "Не уверен", "Скрывает чувства", "Влюблен по-своему", "Есть интерес", "Играет с чувствами"]
magic_ball_answers = ["Да", "Нет", "Скоро", "Попробуй снова", "Сомневаюсь"]
crystal_colors = ["Любовь", "Удача", "Здоровье", "Финансы", "Энергия"]
tea_patterns = ["лист", "сердце", "змейка", "спираль", "звезда"]
coin_faces = ["Орёл", "Решка"]

# ====== Гороскоп ======
astrology_signs = [
    "Овен","Телец","Близнецы","Рак","Лев","Дева",
    "Весы","Скорпион","Стрелец","Козерог","Водолей","Рыбы"
]

horoscope_phrases = {}
for sign in astrology_signs:
    horoscope_phrases[sign] = {
        "энергия": [
            "Сегодня вы полны энергии и сил.",
            "Вас ждут неожиданные приливы энергии.",
            "День благоприятен для активных действий."
        ],
        "работа": [
            "На работе возможны новые возможности.",
            "Сосредоточьтесь на важных проектах."
        ],
        "любовь": [
            "Романтические встречи возможны сегодня.",
            "Отношения могут выйти на новый уровень."
        ],
        "финансы": [
            "Финансовые дела стабилизируются.",
            "Будьте осторожны с расходами."
        ],
        "здоровье": [
            "Обратите внимание на физическую активность.",
            "Займитесь своим здоровьем и отдыхом."
        ]
    }

def generate_horoscope(sign):
    """Выбор гороскопа на день, меняется каждый день."""
    parts = horoscope_phrases.get(sign)
    if not parts:
        return "Гороскоп недоступен для этого знака."
    today = date.today()
    seed = hash(f"{sign}-{today}")
    random.seed(seed)
    selected = {category: random.choice(phrases) for category, phrases in parts.items()}
    text = f"♈ Гороскоп для {sign} на {today}:\n\n"
    text += "\n".join(selected.values())
    return text

# ====== Описания гаданий с подсказками ======
gadania_info = {
    "Таро": "🃏 Карты Таро показывают ключевые события вашей жизни.\nСовет: выберите 3 карты — Прошлое, Настоящее, Будущее.",
    "Руны": "⚡ Руны несут советы и предостережения.\nСовет: выберите 3 руны — Ситуация, Совет, Исход.",
    "Оракул": "🌟 Оракул помогает принять решения.\nСовет: выберите 1–3 карты.",
    "Игральные карты": "🂡 Отражают события и варианты развития.\nСовет: выберите 3 карты.",
    "Кости": "🎲 Показывают вероятные исходы через числа.\nСовет: бросьте 2 кубика.",
    "Кофейная гуща": "☕ Узоры раскрывают события.\nСовет: оставьте немного гущи и посмотрите на узор.",
    "Бумага": "📜 Даёт простой ответ.\nСовет: вытяните листок.",
    "Спички": "🔥 Даёт простой ответ.\nСовет: вытяните спичку.",
    "Ромашка": "🌼 'Любит/Не любит'.\nСовет: сорвите 5 лепестков.",
    "Астрология": "🌙 Прогноз для вашего знака.\nСовет: сначала выберите знак зодиака.",
    "Магический шар": "🔮 Дает ответы на вопросы.\nСовет: получите один ответ.",
    "Кристаллы": "💎 Раскрывают советы через цвет.\nСовет: выберите 1–3 кристалла.",
    "Чайные листья": "🍵 Узоры показывают события.\nСовет: выберите 1–3 узора.",
    "Монеты": "🪙 Подбрасывание даёт ответ.\nСовет: подбросьте монету."
}

dice_meaning = {1:"новое начало",2:"партнерство",3:"творчество",4:"трудности",5:"перемены",6:"успех"}
cards_meaning = {"♥":"эмоции и отношения","♦":"финансы и дела","♣":"творчество и работа","♠":"проблемы и препятствия"}

# ====== Анимация ======
async def shuffle_animation(query: Update.callback_query, theme: str):
    emojis_map = {
        "Таро": ["🃏", "🎴", "✨", "🔮"],
        "Руны": ["⚡", "🔺","🔻","🪨"],
        "Оракул": ["🌟","💫","🌑","🛡️"],
        "Игральные карты": ["🂡","🂱","🃁","🃑"],
        "Кости": ["🎲"],
        "Кофейная гуща": ["☕"],
        "Бумага": ["📜"],
        "Спички": ["🪵","🔥"],
        "Ромашка": ["🌼","🌸"],
        "Астрология": ["🌙","⭐","☀️"],
        "Магический шар": ["🔮","✨"],
        "Кристаллы": ["💎","🔹"],
        "Чайные листья": ["🍵","🌿"],
        "Монеты": ["🪙","⚪"]
    }
    emojis = emojis_map.get(theme, ["🔮"])
    for _ in range(5):
        line = "".join(random.choices(emojis, k=5))
        try:
            await query.edit_message_text(f"🌀 Подготовка гадания {theme}...\n{line}")
        except:
            pass
        await asyncio.sleep(0.5)

# ====== Раскрытие с итогами ======
async def reveal_cards(query: Update.callback_query, spread_type: str, detail=None):
    messages = []

    if spread_type == "Таро":
        cards = random.sample(list(tarot_cards.keys()), 3)
        positions = ["Прошлое", "Настоящее", "Будущее"]
        for i, card in enumerate(cards):
            orientation = random.choice(["🔼","🔽"])
            meaning = tarot_cards[card]["upright"] if orientation=="🔼" else tarot_cards[card]["reversed"]
            messages.append(f"🃏 {positions[i]}: *{card}* {orientation}\n{meaning}")
        messages.append("✨ Итог: обратите внимание на общую тенденцию карт.")

    elif spread_type == "Руны":
        chosen = random.sample(list(runes.keys()), 3)
        positions = ["Ситуация","Совет","Исход"]
        for i,rune in enumerate(chosen):
            orientation = random.choice(["🔺","🔻"])
            meaning = runes[rune] + (" (возможны трудности)" if orientation=="🔻" else "")
            messages.append(f"⚡ {positions[i]}: *{rune}* {orientation}\n{meaning}")
        messages.append("✨ Итог: обдумайте совет и общий результат.")

    elif spread_type == "Оракул":
        chosen = random.sample(list(oracle.keys()), 3)
        positions = ["Настоящее","Предостережение","Совет"]
        for i,key in enumerate(chosen):
            emoji = random.choice(["🌟","⚖️","💡","🌑","🛡️"])
            messages.append(f"{emoji} {positions[i]}: *{key}*\n{oracle[key]}")
        messages.append("✨ Итог: объедините советы и действуйте согласно им.")

    elif spread_type == "Игральные карты":
        selected_cards = [random.choice(cards_deck) for _ in range(3)]
        for i, card in enumerate(selected_cards):
            suit = card.split()[-1]
            meaning = cards_meaning.get(suit, "")
            messages.append(f"🂡 Карта {i+1}: *{card}* — {meaning}")
        messages.append("✨ Итог: ориентируйтесь на общую направленность карт.")

    elif spread_type == "Кости":
        rolls = [random.choice(dice_faces) for _ in range(2)]
        for i, roll in enumerate(rolls):
            messages.append(f"🎲 Кубик {i+1}: {roll} — {dice_meaning[roll]}")
        combined = " и ".join([dice_meaning[r] for r in rolls])
        messages.append(f"✨ Итог: общий прогноз — {combined}.")

    elif spread_type == "Кофейная гуща":
        chosen = [random.choice(tea_patterns) for _ in range(3)]
        pattern_meaning = {'лист':"важные новости",'сердце':"любовь",'змейка':"неожиданные события",'спираль':"духовное развитие",'звезда':"удача"}
        for i, pattern in enumerate(chosen):
            messages.append(f"☕ Узор {i+1}: *{pattern}* — {pattern_meaning[pattern]}")
        messages.append("✨ Итог: смотрите на общую картину узоров.")

    elif spread_type == "Астрология" and detail:
        messages.append(generate_horoscope(detail))

    elif spread_type == "Бумага":
        answer = random.choice(paper_answers)
        messages.append(f"📜 Ответ: *{answer}*")

    elif spread_type == "Спички":
        answer = random.choice(matches_answers)
        messages.append(f"🔥 Ответ: *{answer}*")

    elif spread_type == "Ромашка":
        results = [random.choice(flower_answers) for _ in range(5)]
        for i, answer in enumerate(results):
            messages.append(f"🌼 Лепесток {i+1}: {answer}")
        love_count = sum(1 for r in results if "Любит" in r)
        not_love_count = sum(1 for r in results if "Не любит" in r)
        if love_count > not_love_count:
            messages.append("💖 ✨ Итог: Любит")
        elif not_love_count > love_count:
            messages.append("💔 ✨ Итог: Не любит")
        else:
            messages.append("❔ ✨ Итог: Неопределённо")

    elif spread_type == "Магический шар":
        answer = random.choice(magic_ball_answers)
        messages.append(f"🔮 Ответ: *{answer}*")

    elif spread_type == "Кристаллы":
        chosen = [random.choice(crystal_colors) for _ in range(3)]
        for i, color in enumerate(chosen):
            messages.append(f"💎 Кристалл {i+1}: *{color}*")
        most_common = max(set(chosen), key=chosen.count)
        messages.append(f"✨ Итог: основной совет — {most_common}")

    elif spread_type == "Чайные листья":
        chosen = [random.choice(tea_patterns) for _ in range(3)]
        pattern_meaning = {'лист':"важные новости",'сердце':"любовь",'змейка':"неожиданные события",'спираль':"духовное развитие",'звезда':"удача"}
        for i, pattern in enumerate(chosen):
            messages.append(f"🍵 Узор {i+1}: *{pattern}* — {pattern_meaning[pattern]}")
        messages.append("✨ Итог: обратите внимание на общую картину узоров.")

    elif spread_type == "Монеты":
        face = random.choice(coin_faces)
        meaning = "успех" if face=="Орёл" else "трудности"
        messages.append(f"🪙 Монета: *{face}* — {meaning}")
        messages.append(f"✨ Итог: {meaning}")

    full_text = "\n\n".join(messages)
    keyboard = [
        [InlineKeyboardButton("Еще расклад 🔄", callback_data=f"play_{spread_type}")],
        [InlineKeyboardButton("Главное меню 🏠", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await query.edit_message_text(full_text, parse_mode="Markdown", reply_markup=reply_markup)
    except:
        try:
            await query.message.reply_text(full_text, parse_mode="Markdown", reply_markup=reply_markup)
        except:
            pass

# ====== Главное меню ======
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"Карты Таро 🃏", callback_data="info_Таро")],
        [InlineKeyboardButton("Руны ⚡", callback_data="info_Руны")],
        [InlineKeyboardButton("Оракул 🌟", callback_data="info_Оракул")],
        [InlineKeyboardButton("Игральные карты 🂡", callback_data="info_Игральные карты")],
        [InlineKeyboardButton("Кости 🎲", callback_data="info_Кости")],
        [InlineKeyboardButton("Кофейная гуща ☕", callback_data="info_Кофейная гуща")],
        [InlineKeyboardButton("Бумага 📜", callback_data="info_Бумага")],
        [InlineKeyboardButton("Спички 🔥", callback_data="info_Спички")],
        [InlineKeyboardButton("Ромашка 🌼", callback_data="info_Ромашка")],
        [InlineKeyboardButton("Гороскоп 🌙", callback_data="choose_sign")],
        [InlineKeyboardButton("Магический шар 🔮", callback_data="info_Магический шар")],
        [InlineKeyboardButton("Кристаллы 💎", callback_data="info_Кристаллы")],
        [InlineKeyboardButton("Чайные листья 🍵", callback_data="info_Чайные листья")],
        [InlineKeyboardButton("Монеты 🪙", callback_data="info_Монеты")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text("Выберите гадание:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            "🔮 Добро пожаловать, искатель истины!\n\n"
            "Я — твой персональный оракул.\n"
            "Нажми на одно из гаданий ниже, чтобы узнать больше и получить расклад:",
            reply_markup=reply_markup
        )

# ====== Обработка кнопок ======
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    try:
        await query.answer()
    except:
        pass

    data = query.data

    if data == "menu":
        await show_main_menu(update, context)
        return

    if data.startswith("info_"):
        gadanie = data.split("_")[1]
        info_text = gadania_info.get(gadanie, "Информация недоступна.")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Гадать 🔮", callback_data=f"play_{gadanie}")],
            [InlineKeyboardButton("Главное меню 🏠", callback_data="menu")]
        ])
        await query.edit_message_text(info_text, reply_markup=keyboard)
        return

    if data == "choose_sign":
        keyboard = [[InlineKeyboardButton(sign, callback_data=f"play_Астрология_{sign}")] for sign in astrology_signs]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите ваш знак зодиака:", reply_markup=reply_markup)
        return

    if data.startswith("play_"):
        parts = data.split("_")
        gadanie = parts[1]
        detail = parts[2] if len(parts) > 2 else None
        await shuffle_animation(query, gadanie)
        await reveal_cards(query, gadanie, detail)
        return

# ===== Запуск бота ======
if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Установите TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", show_main_menu))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен...")
    app.run_polling()
