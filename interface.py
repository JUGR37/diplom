# импорты
import sqlalchemy.exc
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

import core
from config import comunity_token, access_token
from core import VkTools
from datetime import datetime

import data_store

# отправка сообщений

class BotInterface():
    def __init__(self, comunity_token, access_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(access_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                        {'user_id': user_id,
                         'message': message,
                         'attachment': attachment,
                         'random_id': get_random_id()
                         }
                       )

    def get_feedback(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                result = event.text
                return result

    def get_photos(self, user_id, worksheet):
        if not data_store.check_user(data_store.engine, user_id, worksheet):
            data_store.add_user(data_store.engine, user_id, worksheet)
            photos = self.vk_tools.get_photos(worksheet)
            photo_string = ''
            for photo in photos:
                photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
            return photo_string

    # обработка событий / получение сообщений

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''логика для получения данных о пользователе'''
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'Привет, {self.params["name"]}')
                    if self.params['city'] is None:
                        self.message_send(event.user_id, 'Сообщите город, в котором ищем пару')
                        feedback = self.get_feedback()
                        self.params.update({'city': feedback.lower()})
                    if self.params['year'] is None:
                        self.message_send(event.user_id, 'Укажите дату вашего рождения: дд.мм.гггг')
                        feedback = self.get_feedback()
                        self.params.update({'year': self.vk_tools._bdate_toyear(feedback)})

                    self.message_send(event.user_id, f'{self.params["name"]}, напишите "поиск" и мы начинаем искать!')

                elif event.text.lower() == 'поиск':
                    '''логика для поиска анкет'''
                    self.message_send(event.user_id, 'Начинаем поиск')

                    if self.worksheets:
                        worksheet = self.worksheets.pop()
                        outcome = self.get_photos(event.user_id, worksheet['id'])


                    else:
                        self.worksheets = self.vk_tools.search_worksheet(self.params, self.offset)
                        worksheet = self.worksheets.pop()
                        outcome = self.get_photos(event.user_id, worksheet['id'])
                    self.offset += 10


                    if outcome:
                        self.message_send(
                        event.user_id,
                        f'имя: {worksheet["name"]} ссылка: vk.com/{worksheet["id"]}',
                        attachment=outcome
                       )
                    else:
                        self.message_send(
                            event.user_id,
                            f'имя: {worksheet["name"]}, эту анкету уже смотрели, введите еще раз "поиск"')

                elif event.text.lower() == 'пока':
                    self.message_send(event.user_id, 'До новых встреч')
                else:
                    self.message_send(event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    data_store.Base.metadata.create_all(data_store.engine)
    bot_interface =BotInterface(comunity_token, access_token)
    bot_interface.event_handler()