import os


BASEDIR = os.path.dirname(os.getcwd())
PHOTO_PATH = os.path.join(BASEDIR, 'chat/chat/files/photo/')
FILES_PATH = os.path.join(BASEDIR, 'chat/chat/files/files/')
AVAILABLE_IMG_EXTENSTION = ['png', 'jpg', 'jpeg']
os.makedirs(PHOTO_PATH, exist_ok = True)
os.makedirs(FILES_PATH, exist_ok = True)


SECRET_KEY =  os.environ.get('POSTGRES_HOST', 'foo')

NEW_CHATS_PER_DAY_LIMIT = 15

POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', 5432)
DATABASE = os.environ.get('DATABASE', 'postgres')

MONOLITH_HOST = os.environ.get('MONOLITH_HOST', 'http://127.0.0.1')
MONOLITH_PORT = os.environ.get('MONOLITH_PORT', '8000')

MAIN_SERVER_URL = f'{MONOLITH_HOST}:{MONOLITH_PORT}'
