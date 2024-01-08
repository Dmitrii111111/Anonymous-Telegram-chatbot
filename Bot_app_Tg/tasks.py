from project_Tg.celery import celery_app
import telebot
from django.conf import settings
from telebot.apihelper import ApiTelegramException

bot = telebot.TeleBot(settings.TOKEN)


@celery_app.task  # наша таска
def send_message(chat_id, text):
    try:
        bot.send_message(chat_id, text, parse_mode="html")
    except ApiTelegramException as e:
        if e.error_code == 403:
            pass


@celery_app.task
def send_photo(chat_id, photo_path, caption):
    try:
        photo_file = open(f'media/{photo_path}', 'rb')
        bot.send_photo(chat_id, photo=photo_file, caption=caption, parse_mode="html")
        photo_file.close()
    except ApiTelegramException as e:
        if e.error_code == 403:
            pass
        else:
            print(f'Ошибка при отправки: {e}')