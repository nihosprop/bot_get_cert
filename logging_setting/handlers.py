import logging
import asyncio
import re

import aiohttp

logger = logging.getLogger(__name__)

class TelegramAsyncHandler(logging.Handler):
    """
    A class for sending logs to Telegram.
    Args:
        bot_token: Token of the Telegram bot.
        chat_id: ID of the chat where the logs will be sent.
        thread_id: ID of the thread where the logs will be sent.
        loop: Event loop.
    Returns:
        None
    """
    def __init__(self, bot_token: str, chat_id: str, thread_id: str,
                 loop=None):
        
        super().__init__()
        
        # TODO: transfer var 'admins' to .env
        self.admins = ['@Shinobiwin']
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.chat_id = int(chat_id)
        self.thread_id = int(thread_id)
        self.session: aiohttp.ClientSession | None = None
        self.loop = loop or asyncio.get_event_loop()
        
    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    def emit(self, record):

        log_level = record.levelno
        temp_data = re.sub(r'[\[\]]', '', record.message)
        end_data = re.split(r'[:-]', temp_data)
        text, tg_id, tg_username, num_cert, name_cert, course_data = end_data
        num_course, *_ = course_data.split()

        text_result = (f'{text.rstrip(' TG_ID')}:{tg_username}\n'
               f'N-{num_cert}({num_course} курс)\n{name_cert}')

        admins = self.admins if (
                self.admins and log_level >= logging.ERROR) else ''
        
        self.loop.call_soon_threadsafe(asyncio.create_task,
                                  self._send(text=text_result,
                                             admins=admins))
    
    async def _send(self, text: str, admins: list[str] = None):
        try:
            await self._ensure_session()
            
            admins = '🚨' + ','.join(admins) + '\n\n' if admins else ''
            
            request_data = {
                "chat_id": self.chat_id,
                "message_thread_id": self.thread_id,
                "text": f'{admins}{text}'}
            
            logger.debug(f"Отправка запроса в Telegram API: {self.api_url}")
            logger.debug(f"Данные запроса: {request_data}")
            
            async with self.session.post(self.api_url,
                                         data=request_data) as resp:
                response = await resp.text()
                logger.debug(f"Ответ от Telegram API: {resp.status} - {response}")
                if resp.status != 200:
                    logger.error(f"Ошибка при отправке: {resp.status}"
                               f":{response}")
        except Exception as e:
            print(f"Ошибка отправки лога в Telegram: {e}")
    
    async def aclose(self):
        if self.session and not self.session.closed:
            await self.session.close()
