from openai import OpenAI
from pathlib import Path
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


def toText(filename):
    audio_file = open(filename, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcription.text


def getAnswer(text):
    assistant = client.beta.assistants.create(
        name="MyAssistant",
        instructions="You are an AI assistant. Answer user queries.",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4o"
    )
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=text
    )
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    return run.choices[0].message["content"]


def toVoice(filename, input_text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=input_text
    )
    response.stream_to_file(filename)


load_dotenv()

client = OpenAI(api_key=getenv("OPENAI_API_KEY"))
bot = Bot(token=getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode='HTML'))
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
        filename_q = "a_" + str(msg.chat.id) + "_" + msg.from_user.id + str(calendar.timegm(time.gmtime())) + ".mp3"
        filename_a = "q_" + str(msg.chat.id) + "_" + msg.from_user.id + str(calendar.timegm(time.gmtime())) + ".mp3"
        file_info = await bot.get_file(msg.voice.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        with open(filename_q, 'wb') as audio_file:
            audio_file.write(downloaded_file.getvalue())
        toVoice(filename_a, getAnswer(toText(filename_q)))

        await bot.send_audio(chat_id=msg.chat.id, audio=FSInputFile(filename_a))
    else:
        await msg.answer(f"Я управляюсь голосом. Отправь мне голосовое.")


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())