from openai import OpenAI
from pathlib import Path
import os
import time
import asyncio
from io import BytesIO
from aiogram import types, F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from os import getenv
from dotenv import load_dotenv, dotenv_values
from aiogram.client.bot import DefaultBotProperties
from aiogram.types.input_file import InputFile
from aiogram.types.input_media_audio import InputMediaAudio
from aiogram.types import FSInputFile

from my_openai import OpenAiSupStruct


router = Router()


@router.message(Command("start"))
async def start_handler(msg: Message):
    await msg.answer("Привет!")

@router.message()
async def message_handler(msg: Message):
    if msg.voice:
        import time
        import calendar
        str(calendar.timegm(time.gmtime()))
        filename_q = "q_" + str(msg.chat.id) + "_" + str(msg.from_user.id) + str(calendar.timegm(time.gmtime())) + ".mp3"
        filename_a = "a_" + str(msg.chat.id) + "_" + str(msg.from_user.id) + str(calendar.timegm(time.gmtime())) + ".mp3"
        file_info = await bot.get_file(msg.voice.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        with open(filename_q, 'wb') as audio_file:
            audio_file.write(downloaded_file.getvalue())

        m = await bot.send_animation(chat_id=msg.chat.id, animation=FSInputFile("wait.gif"))

        stream = await worker.run(filename_q)
        stream.stream_to_file(filename_a)

        await bot.delete_message(chat_id=msg.chat.id, message_id = m.message_id)

        await bot.send_voice(chat_id=msg.chat.id, voice=FSInputFile(filename_a))

        try:
            if os.path.isfile(filename_q):
                os.remove(filename_q)
            if os.path.isfile(filename_a):
                os.remove(filename_a)
        finally:
            pass
    else:
        await msg.answer(f"Я управляюсь голосом. Отправь мне голосовое.")


load_dotenv()

client = OpenAI(api_key=getenv("OPENAI_API_KEY"))
worker = OpenAiSupStruct(client)
bot = Bot(token=getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode='HTML'))

async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())