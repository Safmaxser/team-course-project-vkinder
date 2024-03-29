import threading
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from datetime import date
from datetime import datetime
from vk_data import OperationsDB


class UserData:
    def __init__(self):
        self.number_position = 0
        self.age_from = None
        self.age_to = None
        self.sex_id = 0
        self.city_id = None
        self.offset = 0
        self.viewed_list = None
        self.viewed_position = -1
        self.viewed_type = None
        self.current_person = None


def buttons(name_button):
    if name_button == 'search_my':
        return 'Искать по моим данным'
    elif name_button == 'search_select':
        return 'Искать по выборочным данным'
    elif name_button == 'favorites':
        return 'Список избранных'
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
    elif name_button == 'del_favorites':
        return 'Убрать из избранные'
    elif name_button == 'del_blacklist':
        return 'Убрать из чёрный список'
    else:
        return ''


def keyboard_add(function=None, control=None):
    color_main = VkKeyboardColor.PRIMARY
    keyboard = VkKeyboard(one_time=False)
    if control == 'begin':
        keyboard.add_button(buttons('next'), color=color_main)
        keyboard.add_line()
    elif control == 'middle':
        keyboard.add_button(buttons('back'), color=color_main)
        keyboard.add_button(buttons('next'), color=color_main)
        keyboard.add_line()
    elif control == 'end':
        keyboard.add_button(buttons('back'), color=color_main)
        keyboard.add_line()
    if function == 'main':
        keyboard.add_button(buttons('search_my'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('search_select'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('blacklist'), color=color_main)
        keyboard.add_button(buttons('favorites'), color=color_main)
    elif function == 'search':
        keyboard.add_button(buttons('start_search'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('start_over'), color=color_main)
    elif function == 'look_user':
        keyboard.add_button(buttons('add_favorites'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('add_blacklist'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('start_over'), color=color_main)
    elif function == 'favorites':
        keyboard.add_button(buttons('del_favorites'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('add_blacklist'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('start_over'), color=color_main)
    elif function == 'blacklist':
        keyboard.add_button(buttons('del_blacklist'), color=color_main)
        keyboard.add_line()
        keyboard.add_button(buttons('add_favorites'), color=color_main)
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


def del_position_viewed(data: UserData):
    data.viewed_list.pop(data.viewed_position)
    if data.viewed_position > len(data.viewed_list)-1:
        data.viewed_position = len(data.viewed_list)-1


class VKAPIBot:
    def __init__(self, token_bot, token_user, db_vk: OperationsDB):
        self.token_bot = token_bot
        self.token_user = token_user
        self.db_vk = db_vk
        self.vk_user_api = None
        self.longpoll = None
        self.vk_bot_api = None
        self.users_data = {}

    def _send_message(self, id_user, message_text,
                      function=None, control=None):
        try:
            self.vk_bot_api.messages.send(
                user_id=id_user,
                random_id=get_random_id(),
                keyboard=keyboard_add(function=function, control=control),
                message=message_text)
        except:
            pass

    def _send_attachment(self, id_user, url_text):
        try:
            self.vk_bot_api.messages.send(
                user_id=id_user,
                random_id=get_random_id(),
                attachment=url_text)
        except:
            pass

    def open_session(self):
        vk_session_bot = vk_api.VkApi(token=self.token_bot)
        self.vk_bot_api = vk_session_bot.get_api()
        self.longpoll = VkLongPoll(vk_session_bot)
        self.vk_user_api = vk_api.VkApi(token=self.token_user).get_api()

    def _get_name_user(self, id_user):
        user = self.vk_user_api.users.get(user_ids=id_user)[0]
        return [user["first_name"], user["last_name"]]

    def _get_photos_user(self, id_user):
        selected_photos = []
        photos_user = self.vk_user_api.photos.get(
            owner_id=id_user, album_id='profile', extended=1)['items']
        for photo in photos_user:
            selected_photos.append((photo.get('likes', {'count': 0}).
                                    get('count'), photo['id']))
        attachment_list = []
        for num, photo in enumerate(sorted(selected_photos)):
            attachment_list.append(f'photo{id_user}_{photo[1]}')
            if num == 2:
                break
        return attachment_list

    def _user_data(self, id_user):
        try:
            self.users_data[id_user]
        except KeyError:
            self.users_data[id_user] = UserData()
        if not self.db_vk.exists_user(id_user):
            first_name, last_name = self._get_name_user(id_user)
            self.db_vk.add_user(
                id_vk=id_user, first_name=first_name, last_name=last_name)

    def _send_person(self, id_user, id_person, result_name=None,
                     **keyboard_type):
        if result_name:
            send_name = result_name
        else:
            send_name = ' '.join(self._get_name_user(id_person))
        self._send_message(id_user, send_name, **keyboard_type)
        self._send_message(
            id_user, f'https://vk.com/id{id_person}', **keyboard_type)
        self._send_attachment(
            id_user, ','.join(self._get_photos_user(id_person)))

    def _show_persons(self, id_user, data: UserData):
        if data.viewed_list:
            keyboard_type = {'function': data.viewed_type}
            if len(data.viewed_list) == 1:
                keyboard_type['control'] = ''
            elif data.viewed_position == 0:
                keyboard_type['control'] = 'begin'
            elif data.viewed_position == len(data.viewed_list) - 1:
                keyboard_type['control'] = 'end'
            else:
                keyboard_type['control'] = 'middle'
            id_person = data.viewed_list[data.viewed_position][0]
            self._send_person(id_user, id_person, **keyboard_type)
            data.current_person = id_person
        else:
            self._send_message(
                id_user, f'"{buttons(data.viewed_type)}" пуст!',
                function='main')

    def processing_message(self, id_user, message_text):
        self._user_data(id_user)
        data = self.users_data[id_user]
        if message_text == buttons('start_over'):
            data.number_position = 0
        elif message_text == buttons('search_my'):
            data.number_position = 1
        elif message_text == buttons('search_select'):
            data.number_position = 2
        elif message_text == buttons('start_search'):
            data.number_position = 20
        elif message_text == buttons('blacklist'):
            data.number_position = 31
        elif message_text == buttons('favorites'):
            data.number_position = 32

        if data.number_position == 0:
            data.__init__()
            self._send_message(
                id_user, 'Тебя приветствует бот! Для поиска знакомств! '
                         'Выбери дальнейшее действие!', function='main')
        elif data.number_position == 1:
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
                                   function='search')
            else:
                self._send_message(id_user,
                                   'Ваших личных данных не хватает для поиска! '
                                   'Попробуйте другой режим '
                                   '"Искать по выборочным данным"!',
                                   function='main')
        elif data.number_position == 2:
            data.number_position = 11
            self._send_message(id_user, 'Введите возраст для поиска!'
                                        'Пример: 18-40 или 20',
                               function='navigation')
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
                                           function='navigation')
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
                                       function='navigation')
            else:
                self._send_message(
                    id_user, 'Возраст введён не корректно! '
                             'Повторите попытку!', function='navigation')
        elif data.number_position == 12:
            try:
                data.sex_id = ['жен', 'муж'].index(message_text.lower())
                self._send_message(
                    id_user, 'Введите город, которую хотите найти! '
                             'Например: Москва', function='navigation')
                data.number_position = 13
            except ValueError:
                self._send_message(
                    id_user, 'Пол введён не коректно! Повторите попытку! '
                             'Например: муж или жен', function='navigation')
        elif data.number_position == 13:
            list_cities = (
                self.vk_user_api.database.getCities(
                    q=message_text, count=5).get('items', []))
            if len(list_cities) == 0:
                self._send_message(
                    id_user, 'Поиск не дал результатов! '
                             'Повторите попытку! '
                             'Например: Москва', function='navigation')
            else:
                for city in list_cities:
                    self._send_message(id_user, f'id = {city.get("id", "")} - '
                                                f'{city.get("title", "")} '
                                                f'{city.get("area", "")}'
                                                f'{city.get("region", "")} ',
                                       function='navigation')
                self._send_message(id_user,
                                   f'Введите ID нужного города! Например: '
                                   f'{list_cities[0].get("id", "1")}',
                                   function='navigation')
                data.number_position = 14
        elif data.number_position == 14:
            if len(self.vk_user_api.database.getCitiesById(
                    city_ids=message_text)) == 1:
                data.city_id = message_text
                self._send_message(id_user, 'Данные приняты! Начать поиск?',
                                   function='search')
            else:
                self._send_message(id_user, 'ID города введён не коректно! '
                                            'Повторите попытку! Например: 73',
                                   function='navigation')
        elif data.number_position == 20:
            if message_text == buttons('next'):
                data.offset += 1
            elif message_text == buttons('back'):
                if data.offset > 0:
                    data.offset -= 1
            elif message_text == buttons('add_favorites'):
                self.db_vk.add_favorites(id_user, data.current_person)
                return
            elif message_text == buttons('add_blacklist'):
                self.db_vk.add_blacklist(id_user, data.current_person)
                return
            keyboard_type = {'function': 'look_user'}
            if data.offset == 0:
                keyboard_type['control'] = 'begin'
            else:
                keyboard_type['control'] = 'middle'
            while True:
                search_results = self.vk_user_api.users.search(
                    count=1, offset=data.offset, sex=data.sex_id, status=1,
                    age_from=data.age_from, age_to=data.age_to, has_photo=1)
                person = search_results['items'][0]
                person_id = person['id']
                if not self.db_vk.exists_blacklist(id_user, person_id):
                    break
                else:
                    data.offset += 1
            result_name = f'{person["first_name"]} {person["last_name"]}'
            self._send_person(id_user, person_id, result_name, **keyboard_type)
            data.current_person = person_id
        elif data.number_position == 31:
            data.viewed_list = self.db_vk.get_blacklist(id_user)
            data.viewed_position = 0
            data.viewed_type = 'blacklist'
            self._show_persons(id_user, data)
            data.number_position = 40
            return
        elif data.number_position == 32:
            data.viewed_list = self.db_vk.get_favorites(id_user)
            data.viewed_position = 0
            data.viewed_type = 'favorites'
            self._show_persons(id_user, data)
            data.number_position = 40
            return
        elif data.number_position == 40:
            if message_text == buttons('next'):
                if data.viewed_position < len(data.viewed_list)-1:
                    data.viewed_position += 1
            elif message_text == buttons('back'):
                if data.viewed_position > 0:
                    data.viewed_position -= 1
            elif message_text == buttons('add_favorites'):
                self.db_vk.add_favorites(id_user, data.current_person)
                del_position_viewed(data)
            elif message_text == buttons('add_blacklist'):
                self.db_vk.add_blacklist(id_user, data.current_person)
                del_position_viewed(data)
            elif message_text == buttons('del_favorites'):
                self.db_vk.del_favorites(id_user, data.current_person)
                del_position_viewed(data)
            elif message_text == buttons('del_blacklist'):
                self.db_vk.del_blacklist(id_user, data.current_person)
                del_position_viewed(data)
            self._show_persons(id_user, data)
        else:
            self._send_message(id_user, 'Какая-то ошибка! Попробуйте снова!')

    def listen_stream(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    threading.Thread(
                        target=self.processing_message,
                        args=(event.user_id, event.text)).start()
