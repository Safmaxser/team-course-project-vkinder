import os
import threading
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from datetime import date
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN_BOT = os.getenv('TOKEN_BOT')
TOKEN_USER = os.getenv('TOKEN_USER')


class UserData:
    def __init__(self):
        self.number_position = 0
        self.age_from = None
        self.age_to = None
        self.sex_id = 0
        self.city_id = None
        self.offset = 0


def user_data(id_user, users):
    try:
        return users[id_user]
    except KeyError:
        users[id_user] = UserData()
        return users[id_user]


def buttons(name_button):
    if name_button == 'search_my':
        return 'Искать по моим данным'
    elif name_button == 'search_select':
        return 'Искать по выборочным данным'
    elif name_button == 'favorites':
        return 'Избранные'
    elif name_button == 'blacklist':
        return 'Чёрный список'
    elif name_button == 'start_over':
        return 'Начать сначала'
    elif name_button == 'start_search':
        return 'Начать поиск'
    elif name_button == 'next':
        return 'Дальше'
    elif name_button == 'back':
        return 'Назад'
    elif name_button == 'add_favorites':
        return 'Добавить в избранные'
    elif name_button == 'add_blacklist':
        return 'Добавить в чёрный список'
    else:
        return ''


def keyboard_add(keyboard_name):
    color_main = VkKeyboardColor.PRIMARY
    keyboard = VkKeyboard()
    if keyboard_name == 'main':
        keyboard.add_button(buttons('search_my'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('search_select'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('favorites'), color=color_main)
        keyboard.add_button(buttons('blacklist'), color=color_main)
    elif keyboard_name == 'search':
        keyboard.add_button(buttons('start_search'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('start_over'), color=color_main)
    elif keyboard_name == 'look_user_begin':
        keyboard.add_button(buttons('next'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('add_favorites'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('add_blacklist'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('start_over'), color=color_main)
    elif keyboard_name == 'look_user':
        keyboard.add_button(buttons('back'), color=color_main)
        keyboard.add_button(buttons('next'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('add_favorites'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('add_blacklist'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('start_over'), color=color_main)
    else:
        return keyboard.get_empty_keyboard()
    return keyboard.get_keyboard()


def calculate_age(date_birth):
    today = date.today()
    my_date = datetime.strptime(date_birth, '%d.%m.%Y').date()
    age = today.year - my_date.year - ((today.month, today.day) <
                                       (my_date.month, my_date.day))
    return age


class VKAPIBot:
    def __init__(self, token_bot, token_user):
        self.token_bot = token_bot
        self.token_user = token_user
        self.vk_user_api = None
        self.longpoll = None
        self.vk_bot_api = None
        self.users_data = {}

    def _send_message(self, id_user, message_text, keyboard_name=None):
        try:
            self.vk_bot_api.messages.send(
                user_id=id_user,
                random_id=get_random_id(),
                keyboard=keyboard_add(keyboard_name),
                message=message_text)
        except:
            print("Ошибка отправки сообщения у id" + id_user)

    def _send_attachment(self, id_user, url_text):
        try:
            self.vk_bot_api.messages.send(
                user_id=id_user,
                random_id=get_random_id(),
                attachment=url_text)
        except:
            print("Ошибка отправки сообщения у id" + id_user)

    def open_session(self):
        vk_session_bot = vk_api.VkApi(token=self.token_bot)
        self.vk_bot_api = vk_session_bot.get_api()
        self.longpoll = VkLongPoll(vk_session_bot)
        self.vk_user_api = vk_api.VkApi(token=self.token_user).get_api()

    def processing_message(self, id_user, message_text):
        data = user_data(id_user, self.users_data)
        if message_text == buttons('start_over'):
            data.number_position = 0
        elif message_text == buttons('favorites'):
            # Выводить из БД
            pass

        if data.number_position == 0:
            data.age_from = None
            data.age_to = None
            data.sex_id = 0
            data.city_id = None
            data.offset = 0
            if message_text == buttons('search_my'):
                my_user = self.vk_user_api.users.get(
                    user_ids=id_user, fields=['bdate', 'city', 'sex'])[0]
                if (my_user.get('sex', 0) > 0 and
                        my_user.get('bdate', None) is not None and
                        my_user.get('city', {}).get('id', None) is not None):
                    data.age_from = calculate_age(my_user['bdate']) - 5
                    data.age_to = data.age_from + 10
                    data.sex_id = 2 if my_user['sex'] == 1 else 1
                    data.city_id = my_user['city']['id']
                    self._send_message(id_user,
                                       'Данные приняты! Начать поиск?',
                                       'search')
                    data.number_position = 20
                else:
                    self._send_message(id_user,
                                       'Ваших личных данных не хватает для поиска! '
                                       'Попробуйте другой режим '
                                       '"Искать по выборочным данным"!',
                                       'main')
            elif message_text == buttons('search_select'):
                data.number_position = 11
                self._send_message(id_user, 'Введите возраст для поиска!'
                                            'Пример: 18-40 или 20',
                                   'navigation')
            else:
                self._send_message(id_user,
                                   'Тебя приветствует бот! Для поиска знакомств! '
                                   'Выбери дальнейшее действие!', 'main')
        elif data.number_position == 11:
            list_age = message_text.split('-')
            if 0 < len(list_age) <= 2:
                for age in list_age:
                    try:
                        int(age)
                    except ValueError:
                        self._send_message(id_user,
                                           'Возраст введён не корректно! '
                                           'Повторите попытку!',
                                           'navigation')
                        break
                else:
                    data.age_from = list_age[0]
                    if len(list_age) == 1:
                        data.age_to = list_age[0]
                    else:
                        data.age_to = list_age[1]
                    data.number_position = 12
                    self._send_message(id_user,
                                       'Введите пол который хотите найти! '
                                       'Например: муж или жен',
                                       'navigation')
            else:
                self._send_message(id_user, 'Возраст введён не корректно! '
                                            'Повторите попытку!', 'navigation')
        elif data.number_position == 12:
            try:
                data.sex_id = ['жен', 'муж'].index(message_text.lower())
                self._send_message(id_user,
                                   'Введите город, которую хотите найти! '
                                   'Например: Москва', 'navigation')
                data.number_position = 13
            except ValueError:
                self._send_message(
                    id_user, 'Пол введён не коректно! Повторите попытку! '
                             'Например: муж или жен', 'navigation')
        elif data.number_position == 13:
            list_cities = (
                self.vk_user_api.database.getCities(
                    q=message_text, count=5).get('items', []))
            if len(list_cities) == 0:
                self._send_message(id_user, 'Поиск не дал результатов! '
                                            'Повторите попытку! '
                                            'Например: Москва', 'navigation')
            else:
                for city in list_cities:
                    self._send_message(id_user, f'id = {city.get("id", "")} - '
                                                f'{city.get("title", "")} '
                                                f'{city.get("area", "")}'
                                                f'{city.get("region", "")} ',
                                       'navigation')
                self._send_message(id_user,
                                   f'Введите ID нужного города! Например: '
                                   f'{list_cities[0].get("id", "1")}',
                                   'navigation')
                data.number_position = 14
        elif data.number_position == 14:
            if len(self.vk_user_api.database.getCitiesById(
                    city_ids=message_text)) == 1:
                data.city_id = message_text
                self._send_message(id_user, 'Данные приняты! Начать поиск?',
                                   'search')
                data.number_position = 20
            else:
                self._send_message(id_user, 'ID города введён не коректно! '
                                            'Повторите попытку! Например: 73',
                                   'navigation')
        elif data.number_position == 20:
            if message_text == buttons('next'):
                data.offset += 1
            elif message_text == buttons('back'):
                if data.offset > 0:
                    data.offset -= 1
            elif message_text == buttons('add_favorites'):
                # Помечать в БД
                pass
            elif message_text == buttons('add_blacklist'):
                # Помечать в БД
                pass

            search_results = self.vk_user_api.users.search(
                count=1, offset=data.offset, sex=data.sex_id, status=1,
                age_from=data.age_from, age_to=data.age_to, has_photo=1)
            user = search_results['items'][0]
            result_name = f'{user["first_name"]} {user["last_name"]}'

            selected_photos = []
            photos_user = self.vk_user_api.photos.get(
                owner_id=user['id'], album_id='profile', extended=1)['items']
            if data.offset == 0:
                keyboard_user = 'look_user_begin'
            else:
                keyboard_user = 'look_user'
            for photo in photos_user:
                selected_photos.append((photo.get('likes', {'count': 0}).
                                        get('count'), photo['id']))
            attachment_list = []
            for num, photo in enumerate(sorted(selected_photos)):
                attachment_list.append(f'photo{user["id"]}_{photo[1]}')
                if num == 2:
                    break
            self._send_message(id_user, result_name, keyboard_user)
            self._send_message(id_user, f'https://vk.com/id{user["id"]}',
                               keyboard_user)
            self._send_attachment(id_user, ','.join(attachment_list))
        else:
            self._send_message(id_user, 'Какая-то ошибка! Попробуйте снова!')

    def listen_stream(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    threading.Thread(
                        target=self.processing_message,
                        args=(event.user_id, event.text)).start()


if __name__ == '__main__':
    vk_bot = VKAPIBot(TOKEN_BOT, TOKEN_USER)
    while True:
        vk_bot.open_session()
        vk_bot.listen_stream()
