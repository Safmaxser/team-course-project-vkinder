import json
import os
import threading
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from datetime import date
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN_BOT = os.getenv('TOKEN_BOT')
TOKEN_USER = os.getenv('TOKEN_USER')

vk_session_bot = vk_api.VkApi(token=TOKEN_BOT)
vk_bot_api = vk_session_bot.get_api()
longpoll = VkLongPoll(vk_session_bot)
vk_session_user = vk_api.VkApi(token=TOKEN_USER)
vk_user_api = vk_session_user.get_api()


def send_message(id_user, message_text, keyboard_name='empty'):
    try:
        with open('keyboard_bot.json', 'r', encoding='UTF-8') as f:
            json_data = json.load(f)
        keyboard_add = json.dumps(json_data.get(keyboard_name),
                                  ensure_ascii=False, indent=2)
        vk_bot_api.messages.send(
             user_id=id_user,
             random_id=get_random_id(),
             keyboard=keyboard_add,
             message=message_text)
    except:
        print("Ошибка отправки сообщения у id" + id_user)


def send_attachment(id_user, url_text):
    try:
        vk_bot_api.messages.send(
            user_id=id_user,
            random_id=get_random_id(),
            attachment=url_text)
    except:
        print("Ошибка отправки сообщения у id" + id_user)


# Временно, надо в БД
number_position = 0
age_from = None
age_to = None
sex_id = 0
city_id = None
offset = 0


def processing_message(id_user, message_text):
    # Временно, надо в БД
    global number_position
    global age_from
    global age_to
    global sex_id
    global city_id
    global offset

    if message_text == 'в начало':
        number_position = 0
    elif message_text == 'избранные':
        # Выводить из БД
        pass

    if number_position == 0:
        age_from = None
        age_to = None
        sex_id = 0
        city_id = None
        offset = 0
        if message_text == 'искать по моим данным':
            my_user = vk_user_api.users.get(user_ids=id_user,
                                            fields=['bdate', 'city', 'sex'])[0]
            if (my_user.get('sex', 0) > 0 and
                    my_user.get('bdate', None) is not None and
                    my_user.get('city', {}).get('id', None) is not None):
                today = date.today()
                my_date = datetime.strptime(my_user['bdate'], '%d.%m.%Y').date()
                age = today.year - my_date.year - ((today.month, today.day) <
                                                   (my_date.month, my_date.day))
                age_from = age - 5
                age_to = age + 5
                if my_user['sex'] == 1:
                    sex_id = 2
                else:
                    sex_id = 1
                city_id = my_user['city']['id']
                send_message(id_user, 'Данные приняты! Начать поиск?',
                             'search')
                number_position = 20
            else:
                send_message(id_user,
                             'Ваших личных данных не хватает для поиска! '
                             'Попробуйте другой режим '
                             '"Искать по выборочным данным"!',
                             'main')
        elif message_text == 'искать по выборочным данным':
            number_position = 11
            send_message(id_user, 'Введите возраст для поиска!'
                                  'Пример: 18-40 или 20', 'navigation')
        else:
            send_message(id_user,
                         'Тебя приветствует бот! Для поиска знакомств! '
                         'Выбери дальнейшее действие!', 'main')
    elif number_position == 11:
        list_age = message_text.split('-')
        if 0 < len(list_age) <= 2:
            for age in list_age:
                try:
                    int(age)
                except ValueError:
                    send_message(id_user, 'Возраст введён не корректно! '
                                          'Повторите попытку!', 'navigation')
                    break
            else:
                age_from = list_age[0]
                if len(list_age) == 1:
                    age_to = list_age[0]
                else:
                    age_to = list_age[1]
                number_position = 12
                send_message(id_user, 'Введите пол! Например: муж или жен',
                             'navigation')
        else:
            send_message(id_user, 'Возраст введён не корректно! '
                                  'Повторите попытку!', 'navigation')
    elif number_position == 12:
        try:
            sex_id = ['жен', 'муж'].index(message_text)
            send_message(id_user, 'Введите город, которую хотите найти! '
                                  'Например: Москва', 'navigation')
            number_position = 13
        except ValueError:
            send_message(id_user, 'Пол введён не коректно! Повторите попытку! '
                                  'Например: муж или жен', 'navigation')
    elif number_position == 13:
        list_cities = (vk_user_api.database.getCities(q=message_text, count=5).
                       get('items', []))
        if len(list_cities) == 0:
            send_message(id_user, 'Поиск не дал результатов! '
                                  'Повторите попытку! '
                                  'Например: Москва', 'navigation')
        else:
            for city in list_cities:
                send_message(id_user, f'id = {city.get("id", "")} - '
                                      f'{city.get("title", "")} '
                                      f'{city.get("area", "") }'
                                      f'{city.get("region", "")} ',
                             'navigation')
            send_message(id_user, f'Введите ID нужного города! Например: '
                                  f'{list_cities[0].get("id", "1")}',
                         'navigation')
            number_position = 14
    elif number_position == 14:
        if len(vk_user_api.database.getCitiesById(city_ids=message_text)) == 1:
            city_id == int(message_text)
            send_message(id_user, 'Данные приняты! Начать поиск?',
                         'search')
            number_position = 20
        else:
            send_message(id_user, 'ID города введён не коректно! '
                                  'Повторите попытку! Например: 73',
                         'navigation')
    elif number_position == 20:
        if message_text == 'дальше':
            offset +=1
        elif message_text == 'назад':
            if offset > 0:
                offset -= 1
        elif message_text == 'в избраное':
            # Помечать в БД
            pass

        search_results = vk_user_api.users.search(count=1, offset=offset,
                                                  sex=sex_id, status=1,
                                                  age_from=age_from,
                                                  age_to=age_to,
                                                  has_photo=1)
        user = search_results['items'][0]
        result_name = f'{user["first_name"]} {user["last_name"]}'

        selected_photos = []
        photos_user = vk_user_api.photos.get(owner_id=user['id'],
                                             album_id='profile',
                                             extended=1)['items']
        if offset == 0:
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
        send_message(id_user, result_name, keyboard_user)
        send_message(id_user, f'https://vk.com/id{user["id"]}', keyboard_user)
        send_attachment(id_user, ','.join(attachment_list))
    else:
        send_message(id_user, 'Какая-то ошибка! Поробуйте снова!')


if __name__ == '__main__':
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                threading.Thread(
                    target=processing_message,
                    args=(event.user_id, event.text.lower())).start()