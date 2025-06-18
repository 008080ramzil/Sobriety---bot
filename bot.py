#!/usr/bin/env python3
"""
Simplified 28-day Sobriety Challenge Telegram Bot
with physical exercise recommendations and better daily questions
"""

import json
import random
import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ai_motivator import generate_personalized_motivation, generate_urge_support_message, generate_reflection_prompt, test_ai_connection

# Bot configuration
API_TOKEN = '8138434558:AAF6TOL-K_LMAQiIIQvJmclLs9nGRc1ThO8'

# Initialize bot components
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
scheduler = AsyncIOScheduler()

# Data storage
user_data = {}
DATA_FILE = 'user_data.json'

# Load existing data
try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

def save_data():
    """Save user data to JSON file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=4, ensure_ascii=False)

# Day-specific motivations
MOTIVATIONS_BY_DAY = {
    1: "🧠 День 1: Ты сделал первый шаг. Уже через 24 часа начинают снижаться тревожность и давление.",
    2: "💧 День 2: Организм начинает вымывать токсины. Твои почки и печень работают активнее.",
    3: "😴 День 3: Сон может быть беспокойным — это нормально. Мозг адаптируется к жизни без алкоголя.",
    4: "🫀 День 4: Давление стабилизируется, сердечный ритм выравнивается. Ты стал спокойнее.",
    5: "🦷 День 5: Улучшается дыхание и состояние полости рта. Ты пахнешь лучше — факт!",
    6: "💪 День 6: Энергия начинает возвращаться. Даже если устаёшь — ты просыпаешься легче.",
    7: "🌙 День 7: Ты прожил неделю трезвости. Сон становится глубже, настроение стабильнее.",
    8: "🧼 День 8: Кожа становится чище, цвет лица — ровнее. Организм продолжает очищение.",
    9: "🫁 День 9: Улучшается насыщение кислородом. Ты дышишь легче и глубже.",
    10: "🧘 День 10: Эмоции становятся устойчивее. Ты всё больше управляешь собой.",
    11: "🌿 День 11: Уходит ощущение 'похмельной тревоги'. В теле — больше лёгкости.",
    12: "🧩 День 12: Память и внимание начинают восстанавливаться. Ты замечаешь детали.",
    13: "⚡ День 13: Меньше усталости в течение дня. Повышается физическая выносливость.",
    14: "❤️ День 14: Сердце работает ровно. Давление в норме. Ты стал бодрее и крепче.",
    15: "🧠 День 15: Центры удовольствия в мозге начинают функционировать естественно — без допинга.",
    16: "🔥 День 16: Жиросжигание активируется. Алкоголь больше не мешает метаболизму.",
    17: "💤 День 17: Ты спишь лучше. Во сне ты наконец-то реально восстанавливаешься.",
    18: "📈 День 18: Настроение всё чаще ровное. Ты чувствуешь стабильность внутри.",
    19: "🧽 День 19: Продолжается клеточная регенерация. Ты обновляешься изнутри.",
    20: "💡 День 20: Мозг работает быстрее. Появляется ясность, решения даются легче.",
    21: "🧘‍♂️ День 21: Эмоциональные качели почти исчезли. Ты больше хозяин своему состоянию.",
    22: "🌟 День 22: Самооценка растёт. Ты уважаешь себя за то, что держишься.",
    23: "🦾 День 23: Ты — пример силы. Уровень стресса заметно снижается.",
    24: "🧃 День 24: Желание пить уменьшается. Организм привыкает к естественной жизни.",
    25: "⚙️ День 25: Ты стал продуктивнее. Алкоголь больше не ворует твоё время и энергию.",
    26: "🪞 День 26: Люди замечают, что ты стал выглядеть лучше. Ты излучаешь уверенность.",
    27: "📚 День 27: Ты приобрёл навык, который может изменить всё. Самообладание — суперсила.",
    28: "🏆 День 28: Поздравляю! Ты сделал это. Новый ты — ясный, энергичный, сильный. Горжусь тобой!"
}

# Physical exercise recommendations
EXERCISE_RECOMMENDATIONS = [
    "Сделай 10 приседаний, 10 отжиманий от стены и постой 20 секунд в планке.",
    "Сделай 15 прыжков на месте, 10 скручиваний лёжа и глубокие вдохи-выдохи.",
    "Поставь руки на пояс, сделай круговые движения бёдрами и шеей по 10 раз.",
    "Сделай 10 выпадов вперёд, 10 махов руками и 30 секунд планки.",
    "Пройди по комнате с высоким подниманием коленей 1 минуту и улыбнись себе в зеркало.",
    "Включи любимую песню, танцуй под неё 3 минуты — без остановки!",
    "Сделай 10 медленных глубоких приседаний и потряси кистями рук 30 секунд.",
    "Постой на одной ноге по 20 секунд на каждую — это улучшает баланс и концентрацию.",
    "Сделай 20 шагов на месте с вытянутыми руками вверх.",
    "Прими позу ребёнка на полу (йога), посиди так 1 минуту. Затем потянись вверх."
]

# Daily questions sets
DAILY_QUESTIONS_MORNING = [
    "Как ты себя чувствуешь сегодня?",
    "Была ли у тебя сегодня тревожность?",
    "Есть ли чувство усталости сейчас?",
    "Ты ощущаешь прогресс?",
    "Хочется ли тебе сегодня выпить?"
]

DAILY_QUESTIONS_EVENING = [
    "Как твоё настроение сейчас?",
    "Ты доволен своим днём?",
    "Тебе удалось выполнить то, что запланировал?",
    "Есть ли сейчас раздражение или уныние?",
    "Ты чувствуешь уверенность в себе?"
]

# Response reactions
RESPONSE_REACTIONS = {
    "да": "Отлично! Двигайся дальше в том же духе!",
    "нет": "Попробуй не давить на себя. Завтра может быть легче.",
    "не очень": "Иногда так бывает. Сделай что-то приятное для себя.",
    "не особо": "Это нормально. Всё стабилизируется со временем."
}

# Create keyboard
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Статистика"), KeyboardButton(text="Желание выпить")],
            [KeyboardButton(text="AI мотивация"), KeyboardButton(text="AI вопрос")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# Initialize user data structure
def init_user_data(user_id: str):
    today = datetime.now().strftime('%Y-%m-%d')
    if user_id not in user_data:
        user_data[user_id] = {
            "start_date": today,
            "thoughts": [],
            "urges": [],
            "last_recommendation": None,
            "last_question_morning": None,
            "last_question_evening": None
        }
        save_data()

# Calculate current day
def get_current_day(user_id: str) -> int:
    if user_id not in user_data:
        return 0
    start_date = datetime.strptime(user_data[user_id]['start_date'], '%Y-%m-%d')
    current_day = (datetime.now() - start_date).days + 1
    return max(1, min(current_day, 28))

# Handlers
@router.message(Command("start"))
async def start_challenge(message: types.Message):
    user_id = str(message.from_user.id)
    init_user_data(user_id)
    
    if user_id in user_data:
        current_day = get_current_day(user_id)
        await message.answer(
            f"Ты начал 28-дневный трезвый челлендж. Я буду с тобой каждый день. 💪\n\n"
            f"Сегодня у тебя день {current_day}.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Ты уже начал челлендж. Не торопи события — новое задание будет завтра. ☝️",
            reply_markup=get_main_keyboard()
        )

@router.message(Command("мысль"))
async def record_thought(message: types.Message):
    user_id = str(message.from_user.id)
    init_user_data(user_id)
    
    text = message.text.replace('/мысль', '').strip()
    if text:
        user_data[user_id]['thoughts'].append({
            "date": datetime.now().strftime('%Y-%m-%d'),
            "text": text
        })
        save_data()
        await message.answer("Мысль сохранена. Я напомню об этом позже для вдохновения!")
    else:
        await message.answer("Напиши свою мысль после команды /мысль")

@router.message(Command("хочу"))
async def record_urge(message: types.Message):
    user_id = str(message.from_user.id)
    init_user_data(user_id)
    
    user_data[user_id]['urges'].append(datetime.now().strftime('%Y-%m-%d %H:%M'))
    save_data()
    await message.answer("Спасибо, я записал твоё желание. Мы сможем отследить, как часто это происходит.")

@router.message(F.text == "Желание выпить")
async def handle_urge_button(message: types.Message):
    user_id = str(message.from_user.id)
    init_user_data(user_id)
    
    # Log the urge
    user_data[user_id]['urges'].append(datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    current_day = get_current_day(user_id)
    recent_urges = len(user_data[user_id]['urges'])
    
    try:
        # Generate AI support message
        ai_support = generate_urge_support_message(current_day, recent_urges)
        support_text = f"💙 {ai_support}\n\n"
    except Exception as e:
        logging.error(f"AI urge support error: {e}")
        support_text = "💙 Это чувство пройдет. Ты уже прошел столько — ты справишься и сейчас.\n\n"
    
    # Give immediate exercise recommendation
    recommendation = random.choice(EXERCISE_RECOMMENDATIONS)
    user_data[user_id]['last_recommendation'] = recommendation
    save_data()
    
    await message.answer(
        f"📌 Желание записано. {support_text}"
        f"Попробуй: {recommendation}\n\n"
        f"Помогло ли это? Напиши: Да / Нет",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "Статистика")
async def show_statistics(message: types.Message):
    user_id = str(message.from_user.id)
    init_user_data(user_id)
    
    current_day = get_current_day(user_id)
    total_urges = len(user_data[user_id]['urges'])
    total_thoughts = len(user_data[user_id]['thoughts'])
    
    stats_message = f"📊 Твоя статистика:\n\n"
    stats_message += f"📅 День челленджа: {current_day}/28\n"
    stats_message += f"🎯 Прогресс: {(current_day/28)*100:.1f}%\n"
    stats_message += f"💭 Сохранено мыслей: {total_thoughts}\n"
    stats_message += f"🚨 Желаний выпить: {total_urges}\n"
    
    if current_day >= 7:
        stats_message += f"\n🌟 Ты прошел уже {current_day} дней! Это серьезное достижение!"
    elif current_day >= 3:
        stats_message += f"\n💪 {current_day} дня — отличное начало!"
    else:
        stats_message += f"\n🔥 Каждый день важен! Держись!"
    
    await message.answer(stats_message, reply_markup=get_main_keyboard())

@router.message(F.text == "AI мотивация")
async def ai_motivation(message: types.Message):
    user_id = str(message.from_user.id)
    init_user_data(user_id)
    
    await message.answer("🤖 Генерирую персональную мотивацию...")
    
    current_day = get_current_day(user_id)
    user_context = {
        'total_urges': len(user_data[user_id]['urges']),
        'total_thoughts': len(user_data[user_id]['thoughts'])
    }
    
    try:
        ai_message = generate_personalized_motivation(current_day, user_context)
        await message.answer(f"✨ {ai_message}", reply_markup=get_main_keyboard())
    except Exception as e:
        logging.error(f"AI motivation error: {e}")
        await message.answer("Извини, не могу сгенерировать мотивацию сейчас. Попробуй позже.", reply_markup=get_main_keyboard())

@router.message(F.text == "AI вопрос")
async def ai_question(message: types.Message):
    user_id = str(message.from_user.id)
    init_user_data(user_id)
    
    await message.answer("🤖 Генерирую вопрос для размышления...")
    
    current_day = get_current_day(user_id)
    
    try:
        ai_question = generate_reflection_prompt(current_day)
        await message.answer(f"🤔 {ai_question}", reply_markup=get_main_keyboard())
    except Exception as e:
        logging.error(f"AI question error: {e}")
        await message.answer("Извини, не могу сгенерировать вопрос сейчас. Попробуй позже.", reply_markup=get_main_keyboard())

@router.message()
async def handle_responses(message: types.Message):
    user_id = str(message.from_user.id)
    init_user_data(user_id)
    text = message.text.strip().lower()
    
    # Handle responses to exercise recommendations
    if text in ["да", "нет", "не очень", "не особо"]:
        reaction = RESPONSE_REACTIONS.get(text, "Спасибо за ответ!")
        await message.answer(reaction, reply_markup=get_main_keyboard())
        
        # If exercise didn't help, suggest another
        if text in ["нет", "не помогло"]:
            last_rec = user_data[user_id].get("last_recommendation")
            available_recs = [r for r in EXERCISE_RECOMMENDATIONS if r != last_rec]
            new_recommendation = random.choice(available_recs)
            user_data[user_id]['last_recommendation'] = new_recommendation
            save_data()
            
            await message.answer(
                f"Хорошо, тогда попробуй это: {new_recommendation}\n\nПомогло ли это? Да / Нет",
                reply_markup=get_main_keyboard()
            )
        elif text in ["да", "помогло"]:
            await message.answer("Рад это слышать! Ты молодец! ✨", reply_markup=get_main_keyboard())
    
    else:
        await message.answer(
            "Используй кнопки ниже или команды:\n"
            "• /start - начать челлендж\n"
            "• /мысль [текст] - сохранить мысль\n"
            "• /хочу - записать желание выпить\n"
            "• AI мотивация - персональная поддержка\n"
            "• AI вопрос - размышления для роста",
            reply_markup=get_main_keyboard()
        )

# Scheduled tasks
async def send_daily_motivation():
    for user_id in user_data:
        try:
            current_day = get_current_day(user_id)
            if current_day <= 28:
                # Try AI motivation first, fallback to predefined
                try:
                    user_context = {
                        'total_urges': len(user_data[user_id]['urges']),
                        'total_thoughts': len(user_data[user_id]['thoughts'])
                    }
                    ai_motivation = generate_personalized_motivation(current_day, user_context)
                    motivation = f"🤖 {ai_motivation}"
                except Exception as ai_error:
                    logging.error(f"AI motivation failed for {user_id}: {ai_error}")
                    motivation = MOTIVATIONS_BY_DAY.get(current_day, "Ты держишься отлично! Продолжай!")
                
                await bot.send_message(user_id, f"День {current_day} — {motivation}")
        except Exception as e:
            logging.error(f"Error sending motivation to {user_id}: {e}")

async def ask_morning_question():
    today = datetime.now().strftime('%Y-%m-%d')
    for user_id in user_data:
        try:
            if user_data[user_id].get("last_question_morning") != today:
                question = random.choice(DAILY_QUESTIONS_MORNING)
                await bot.send_message(user_id, f"🌅 {question}")
                user_data[user_id]['last_question_morning'] = today
        except Exception as e:
            logging.error(f"Error sending morning question to {user_id}: {e}")
    save_data()

async def ask_evening_question():
    today = datetime.now().strftime('%Y-%m-%d')
    for user_id in user_data:
        try:
            if user_data[user_id].get("last_question_evening") != today:
                question = random.choice(DAILY_QUESTIONS_EVENING)
                await bot.send_message(user_id, f"🌙 {question}")
                user_data[user_id]['last_question_evening'] = today
        except Exception as e:
            logging.error(f"Error sending evening question to {user_id}: {e}")
    save_data()

# Main function
async def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test AI connection
    if test_ai_connection():
        logging.info("AI motivator connected successfully")
    else:
        logging.warning("AI motivator connection failed - using fallback messages")
    
    # Register handlers
    dp.include_router(router)
    
    # Setup scheduler
    scheduler.add_job(send_daily_motivation, 'cron', hour=9, minute=0)
    scheduler.add_job(ask_morning_question, 'cron', hour=13, minute=0)
    scheduler.add_job(ask_evening_question, 'cron', hour=20, minute=0)
    scheduler.start()
    
    logging.info("Starting 28-day Sobriety Challenge Bot with AI Features...")
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
