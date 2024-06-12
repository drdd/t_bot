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

def toText(filename):
    audio_file = open(filename, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcription.text


def getAnswer(text):
    # model="gpt-4o"
    assistant = client.beta.assistants.create(
        name="MyAssistant",
        instructions="You are an AI assistant. Answer user queries.",
        tools=[{"type": "code_interpreter"}],
        model="gpt-3.5-turbo"
    )
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=text
    )
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    status = run.status
    s_time = time.time()
    while status != "completed":
        if status == 'failed':
            raise Exception(f"Ошибка: {run.last_error}")
        if status == 'expired':
            raise Exception("Провал")
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread.id)
        status = run.status
        end_time = time.time() - s_time
        if end_time > 60: # 2 minutes
            client.beta.threads.runs.cancel(run_id=run.id, thread_id=thread.id)
            raise Exception("Слишком долго")

    return client.beta.threads.messages.list(thread_id=thread.id).data[0].content[0].text.value

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
        filename_q = "a_" + str(msg.chat.id) + "_" + str(msg.from_user.id) + str(calendar.timegm(time.gmtime())) + ".mp3"
        filename_a = "q_" + str(msg.chat.id) + "_" + str(msg.from_user.id) + str(calendar.timegm(time.gmtime())) + ".mp3"
        file_info = await bot.get_file(msg.voice.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        with open(filename_q, 'wb') as audio_file:
            audio_file.write(downloaded_file.getvalue())

        m = await bot.send_animation(chat_id=msg.chat.id, animation=FSInputFile("wait.gif"))

        toVoice(filename_a, getAnswer(toText(filename_q)))

        await bot.delete_message(chat_id=msg.chat.id, message_id = m.message_id)

        await bot.send_audio(chat_id=msg.chat.id, audio=FSInputFile(filename_a))

        try:
            if os.path.isfile(filename_q):
                os.remove(filename_q)
            if os.path.isfile(filename_a):
                os.remove(filename_a)
        finally:
            pass
    else:
        await msg.answer(f"Я управляюсь голосом. Отправь мне голосовое.")


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())