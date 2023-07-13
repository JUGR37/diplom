# импорты
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

    def get_feedback(self, par, mes, user_id):
        if self.params[par] is None:
            self.message_send(user_id, mes)
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                    result = event.text
                    return result

    # def get_photos(self, user_id, worksheets):
    #     worksheet = worksheets.pop()
    #     if not data_store.check_user(data_store.engine, user_id, worksheet['id']):
    #         data_store.add_user(data_store.engine, user_id, worksheet['id'])
    #         photos = self.vk_tools.get_photos(worksheet['id'])
    #         photo_string = ''
    #         for photo in photos:
    #             photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
    #             return f'имя: {worksheet["name"]} ссылка: vk.com/{worksheet["id"]}', photo_string


    # обработка событий / получение сообщений

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''логика для получения данных о пользователе'''
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'Привет, {self.params["name"]}')
                    if self.params['sex'] is None:
                        if self.get_feedback('sex', 'Кого ищем? 1-женщину, 2- мужчину', event.user_id) == '2':
                            self.params.update({'sex': 1})
                        elif self.get_feedback('sex', 'Кого ищем? 1-женщину, 2- мужчину', event.user_id) == '1':
                            self.params.update({'sex': 2})
                        else:
                            self.message_send(event.user_id,
                                          'Введите только 1 или 2')
                    if self.params['city'] is None:
                        self.params.update({'city': self.get_feedback('city', 'Сообщите город, в котором ищем пару', event.user_id).lower()})
                    # break
                    if self.params['year'] is None:
                        self.params.update({'year': self.vk_tools._bdate_toyear(self.get_feedback('year', 'Укажите дату вашего рождения: дд.мм.гггг', event.user_id))})

                            # try:
                            #     datetime.strptime(
                            #         self.get_feedback('year', 'Укажите дату вашего рождения: дд.мм.гггг', event.user_id),
                            #         '%d.%m.%Y')
                            # except ValueError:
                            #     self.message_send(event.user_id, 'Неверный формат даты, должно быть ДД.ММ.ГГГГ')
                            # else:
                            #     self.params.update({'year': self.vk_tools._bdate_toyear(
                            #         self.get_feedback('year', 'Укажите дату вашего рождения: дд.мм.гггг', event.user_id))})

                    self.message_send(event.user_id, f'{self.params["name"]}, напишите "поиск" и мы начинаем искать!')



                elif event.text.lower() == 'поиск':
                    '''логика для поиска анкет'''
                    self.message_send(event.user_id, 'Начинаем поиск')
                    if self.worksheets:
                        # print(f'1: {self.get_photos(event.user_id, self.worksheets)[0]}')
                        # print(f'1: {self.get_photos(event.user_id, self.worksheets)[1]}')
                        worksheet = self.worksheets.pop()
                        if not data_store.check_user(data_store.engine, event.user_id, worksheet['id']):
                            data_store.add_user(data_store.engine, event.user_id, worksheet['id'])
                            photos = self.vk_tools.get_photos(worksheet['id'])
                            photo_string = ''
                            for photo in photos:
                                photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

                    else:
                        self.worksheets = self.vk_tools.search_worksheet(self.params, self.offset)
                        # print(self.get_photos(event.user_id, self.worksheets)[0])
                        # print(self.get_photos(event.user_id, self.worksheets)[1])
                        worksheet = self.worksheets.pop()
                        if not data_store.check_user(data_store.engine, event.user_id, worksheet['id']):
                            data_store.add_user(data_store.engine, event.user_id, worksheet['id'])
                            photos = self.vk_tools.get_photos(worksheet['id'])
                            photo_string = ''
                            for photo in photos:
                                photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                    self.offset += 10


                    self.message_send(
                        event.user_id,
                        f'имя: {worksheet["name"]} ссылка: vk.com/{worksheet["id"]}',
                        attachment=photo_string)

                elif event.text.lower() == 'пока':
                    self.message_send(event.user_id, 'До новых встреч')
                else:
                    self.message_send(event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    # data_store.Base.metadata.drop_all(data_store.engine)
    data_store.Base.metadata.create_all(data_store.engine)
    bot_interface =BotInterface(comunity_token, access_token)
    bot_interface.event_handler()