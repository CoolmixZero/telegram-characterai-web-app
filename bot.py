import asyncio
import logging
import sys
from datetime import datetime 
from os import getenv
from dotenv import load_dotenv

from pymongo import MongoClient
from amplitude import Amplitude, BaseEvent

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.web_app_info import WebAppInfo
from aiogram.utils.markdown import hbold

load_dotenv()
TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()

def get_database():
    CONNECTION_STRING = getenv("DATABASE_URL")
    client = MongoClient(CONNECTION_STRING)
    return client['user_list']



client = Amplitude(getenv("API_KEY"))

dbname = get_database()
user_collection = dbname["User"]

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Выберите персонажа", web_app=WebAppInfo(url="https://cfs-price-calculator.vercel.app/catalog"))
        ]
    ])
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!", reply_markup=markup)
    
    # amplitude event
    event = BaseEvent(event_type="Bot Started", user_id=str(message.from_user.id))
    client.track(event)
    
    # add user to mongodb 
    user = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "name": message.from_user.first_name,
        "surname": message.from_user.last_name,
        "createdAt": datetime.now()
    }
    user_collection.update_one(user, {'$set': user}, upsert=True)


@dp.message()
async def echo_handler(message: types.Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")


async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())