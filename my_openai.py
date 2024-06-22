class OpenAiSupStruct:

    def __init__(self, client):
        self.client = client
        self.assistant = self.client.beta.assistants.create(
            name="T Bot assistant Grishka",
            instructions="Ты асистент Гришка и отвечаешь на вопросы.",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4o" #model="gpt-3.5-turbo"
        )

    async def run(self, filename_in):
        transcription = await self._toText(filename_in)
        ansver = await self._get_message(transcription.text)
        stream = await self._toVoice(ansver)
        return stream

    async def _toText(self, filename):
        audio_file = open(filename, "rb")
        transcription =  self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcription

    async def _toVoice(self, input_text):
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=input_text
        )
        return response

    async def _get_message(self, msg):
        message = ""
        try:
            thread = self.client.beta.threads.create()
            self.client.beta.threads.messages.create(thread_id=thread.id,
                                                      role="user",
                                                      content=msg)

            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread.id, assistant_id=self.assistant.id, poll_interval_ms=1000)

            if run.status == "completed":
                message = await self._get_text(run.thread_id)
                return message
            else:
                return run.status

            if run.status in ['expired', 'failed', 'cancelled', 'incomplete']:
                return run.status

        except Exception as e:
                return "Exception"

    async def _get_text(self, thread_id):
      messages = self.client.beta.threads.messages.list(thread_id=thread_id)
      cnt = messages.data[0].content[0].text

      anns = cnt.annotations
      for a in anns:
        cnt.value = cnt.value.replace(a.text, '')

      response = cnt.value
      return response