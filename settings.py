import os


BASEDIR = os.path.dirname(os.getcwd())
PHOTO_PATH = os.path.join(BASEDIR, 'chat/chat/files/photo/')
FILES_PATH = os.path.join(BASEDIR, 'chat/chat/files/files/')
AVAILABLE_IMG_EXTENSTION = ['png', 'jpg', 'jpeg']
os.makedirs(PHOTO_PATH, exist_ok = True)
os.makedirs(FILES_PATH, exist_ok = True)

MAIN_SERVER_URL = 'http://127.0.0.1:8000'

SECRET_KEY = 'wa5kp7d)3vp5y#jb*m5y=#tt+c9tqzw#0c+21rp)w9o)(qn!5^'

NEW_CHATS_PER_DAY_LIMIT = 15
