import os
from vk_bot import VKAPIBot
from vk_data import OperationsDB
from dotenv import load_dotenv

load_dotenv()
TOKEN_BOT = os.getenv('TOKEN_BOT')
TOKEN_USER = os.getenv('TOKEN_USER')
DB_DRIVER = os.getenv('DB_DRIVER')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_DATABASE = os.getenv('DB_DATABASE')
params_db = {'drive': DB_DRIVER, 'user': DB_USER, 'password': DB_PASSWORD,
             'connect_name': DB_HOST, 'port': DB_PORT, 'database': DB_DATABASE}


if __name__ == '__main__':
    with OperationsDB(**params_db) as vk_db:
        vk_bot = VKAPIBot(TOKEN_BOT, TOKEN_USER, vk_db)
        while True:
            vk_bot.open_session()
            vk_bot.listen_stream()
