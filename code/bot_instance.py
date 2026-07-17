"""Инициализация VK бота."""

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id


class VKBot:
    def __init__(self, config):
        self.token = config['vk_token']
        self.group_id = config['group_id']
        self.session = None
        self.api = None
        self.longpoll = None

    def connect(self):
        """Подключается к VK."""
        self.session = vk_api.VkApi(token=self.token)
        self.api = self.session.get_api()
        self.longpoll = VkBotLongPoll(self.session, self.group_id)
        return self

    def send_message(self, user_id, text):
        """Отправляет сообщение пользователю."""
        try:
            self.api.messages.send(
                user_id=user_id,
                message=text,
                random_id=get_random_id()
            )
            return True
        except Exception as e:
            print(f'VK send error: {e}')
            return False

    def listen(self):
        """Слушает входящие сообщения."""
        return self.longpoll.listen()

    def get_event_type(self):
        return VkBotEventType.MESSAGE_NEW
