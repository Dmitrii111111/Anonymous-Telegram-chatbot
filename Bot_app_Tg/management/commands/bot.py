import time

from django.core.management.base import BaseCommand
from django.conf import settings

from Bot_app_Tg.models import *

import telebot
from telebot import types
import os


bot = telebot.TeleBot(settings.TOKEN, threaded=False)


class Command(BaseCommand):  # теперь можем запустить нашего бота по команде python manage.py bot
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        bot.enable_save_next_step_handlers(delay=2)  # Сохранение обработчиков
        bot.load_next_step_handlers()  # Загрузка обработчиков

        def donations():
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton(text='🤖пожертвование на развитие🤖', url='https://qiwi.com/n/ANONYMOUSCHAT')
            markup.row(btn1)
            return markup

        def user_bal():
            itm = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
            markup = types.InlineKeyboardMarkup(row_width=5)
            row = []
            for k, i in enumerate(itm, 1):
                # print(k)
                # print(i)
                item = types.InlineKeyboardButton(text=i, callback_data=str(k))
                row.append(item)
                if k % 5 == 0:  # Создаем новый ряд, когда индекс кнопки равен 5, 10, 15 и так далее
                    markup.add(*row)
                    row = []
            if row:  # Проверяем, есть ли еще кнопки, которые мы не добавили
                markup.add(*row)
            return markup

        def main_delete(message):
            # удаление со всех очередей и сессии
            # Queue.delete_queue(message.chat.id)
            chat_info = Chat.get_active_chat(message.chat.id)
            if chat_info is not False:
                Queue.delete_queue(message.chat.id)
                Chat.delete_chat(chat_info[0])
                bot.send_message(chat_info[1], '❌Собеседник покинул чат', reply_markup=main_menu())
                bot.send_message(message.chat.id, '❌Вы вышли из чата')
            else:
                pass

        def main_blocked(message):
            # блокировка пользователя
            indif = message.chat.id
            blocked = User.objects.get(chat_id=indif)  # получить пользователя по indif
            return blocked.is_blocked

        def main_account(message):
            smail = ['👩', '👨‍🦱', '⭐️', '😊', '💬']
            user_id = message.chat.id
            user = User.user(user_id)
            if user[1] == 'Женский':
                i = smail[0]
            else:
                i = smail[1]
            _text = '<b>Ваш аккаунт</b>\n\n' \
                    f'<em>Имя: {user[0]} {smail[3]}</em>\n' \
                    f'<em>Пол: {user[1]} {i}</em>\n' \
                    f'<em>Рейтинг: {user[2]} {smail[2]}</em>\n' \
                    f'<em>Кол-во завершенных чатов: {user[3]} {smail[4]}</em>\n\n' \
                    'Ваш рейтинг формируется на основе баллов, ' \
                    'которые вы можете присуждать другим участникам после анонимного чата. ' \
                    'Эти баллы влияют на общий балл каждого пользователя. ' \
                    'Если ваш рейтинг опустится ниже 3 баллов, ' \
                    'то ваш аккаунт будет заблокирован на сутки.'

            bot.send_message(user_id, _text, parse_mode="html", reply_markup=main_menu())

        def main_menu():
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('🔍Поиск собеседника')
            markup.add(item1)
            return markup

        def stop_dialog():
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('🔁Сказать свой профиль')
            item2 = types.KeyboardButton('/stop⛔️')
            markup.add(item1, item2)
            return markup

        def stop_search():
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('❌Остановить поиск')
            markup.add(item1)
            return markup

        @bot.message_handler(commands=['start'])
        def start(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('Я парень')
            item2 = types.KeyboardButton('Я девушка')
            markup.add(item1, item2)
            bot.send_message(message.chat.id,
                             'Привет, {0.first_name}! Добро пажаловать в анонимный чат! Укажите ваш пол.'.format(
                                 message.from_user), reply_markup=markup)

        @bot.message_handler(commands=['menu'])
        def menu(message):
            # удаление со всех очередей и сессии
            Queue.delete_queue(message.chat.id)
            main_delete(message)

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('🔍Поиск собеседника')
            item2 = types.KeyboardButton('👤Мой Аккаунт')
            item3 = types.KeyboardButton('❤️Поддержать бота')
            markup.add(item1)
            markup.add(item2)
            markup.add(item3)

            bot.send_message(message.chat.id, 'Меню', reply_markup=markup)

        @bot.message_handler(commands=['account'])
        def account(message):
            main_delete(message)

            main_account(message)

        @bot.message_handler(commands=['stop⛔️'])
        def stop(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('➡️Следующий диалог')
            item2 = types.KeyboardButton('/menu')
            item3 = types.KeyboardButton('Оценить предыдущего собеседника👍👎')
            markup.add(item1, item2)
            markup.add(item3)

            chat_info = Chat.get_active_chat(message.chat.id)

            if chat_info != False:
                # нужно взять из модели Chat и отправить в модель Chat_false
                Chat_false.objects.create(chat_sob=chat_info[1], chat_may=message.chat.id)  # заполнение табл Chat_false

                Chat.delete_chat(chat_info[0])

                User.set_online_status(message.chat.id, chat_info[1], False)  # передаем статус не онлаин(нужно ли нам индекатор online)

                bot.send_message(chat_info[1], '❌Собеседник покинул чат', reply_markup=markup)
                bot.send_message(message.chat.id, '❌Вы вышли из чата', reply_markup=markup)
            else:
                bot.send_message(message.chat.id, '❌Вы не начали чат!', reply_markup=markup)

        @bot.message_handler(content_types=['text'])
        def bot_message(message):
            try:
                if message.chat.type == 'private':
                    if message.text == '🔍Поиск собеседника' or message.text == '➡️Следующий диалог':
                        main_delete(message)

                        # блокировка пользователя (проверка если в БД заблок)
                        block = main_blocked(message)
                        if block == True:
                            bot.send_message(message.chat.id, 'Извините, вы заблокированы.', reply_markup=main_menu())

                        else:
                            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                            item1 = types.KeyboardButton('🔎Парень')
                            item2 = types.KeyboardButton('🔎Девушка')

                            markup.add(item1, item2)

                            bot.send_message(message.chat.id, 'Кого искать?', reply_markup=markup)

                    elif message.text == '❌Остановить поиск':
                        Queue.delete_queue(message.chat.id)
                        bot.send_message(message.chat.id, 'Поиск остановлен, нажмите /menu', reply_markup=main_menu())

                    elif message.text == '🔎Парень':
                        # блокировка пользователя
                        block = main_blocked(message)
                        if block == True:
                            bot.send_message(message.chat.id, 'Извините, вы заблокированы.', reply_markup=main_menu())

                        else:
                            Queue.delete_queue(message.chat.id)
                            main_delete(message)

                            user_info = Queue.get_gender_chat('male')
                            chat_two = user_info[0]
                            if Chat.create_chat(message.chat.id, chat_two) == False:
                                Queue.add_queue(message.chat.id, User.get_gender(message.chat.id))
                                bot.send_message(message.chat.id, '👻Поиск собеседника...', reply_markup=stop_search())
                            else:
                                User.set_online_status(message.chat.id, chat_two, True)  # передаем статус онлаин или нет

                                mess = '✨Собиседник найден! Чтобы остановить диолог, нажмите /stop⛔️'

                                bot.send_message(message.chat.id, mess, reply_markup=stop_dialog())
                                bot.send_message(chat_two, mess, reply_markup=stop_dialog())

                    elif message.text == '🔎Девушка':
                        # блокировка пользователя
                        block = main_blocked(message)
                        if block == True:
                            bot.send_message(message.chat.id, 'Извините, вы заблокированы.', reply_markup=main_menu())

                        else:
                            Queue.delete_queue(message.chat.id)
                            main_delete(message)

                            user_info = Queue.get_gender_chat('female')
                            chat_two = user_info[0]
                            if Chat.create_chat(message.chat.id, chat_two) == False:
                                Queue.add_queue(message.chat.id, User.get_gender(message.chat.id))
                                bot.send_message(message.chat.id, '👻Поиск собеседника...', reply_markup=stop_search())
                            else:
                                User.set_online_status(message.chat.id, chat_two, True)  # передаем статус онлаин или нет

                                mess = '✨Собиседник найден! Чтобы остановить диолог, нажмите /stop⛔️'

                                bot.send_message(message.chat.id, mess, reply_markup=stop_dialog())
                                bot.send_message(chat_two, mess, reply_markup=stop_dialog())

                    elif message.text == '🔁Сказать свой профиль':
                        chat_info = Chat.get_active_chat(message.chat.id)
                        if chat_info != False:
                            if message.from_user.username:
                                bot.send_message(chat_info[1], '@' + message.from_user.username)
                                bot.send_message(message.chat.id, '✅Вы отправили свой профиль')
                            else:
                                bot.send_message(message.chat.id, '❌Вы не указали свой username')
                        else:
                            bot.send_message(message.chat.id, '❌Вы не начали диолог')

                    elif message.text == 'Я парень':
                        user_name = '@' + message.from_user.username
                        if User.set_gender(message.chat.id, 'male', user_name):

                            bot.send_message(message.chat.id, '✅Ваш пол успешно добавлен!', reply_markup=main_menu())
                        else:
                            bot.send_message(message.chat.id, '❌Вы уже указали ваш пол, обратитесь в поддержку',
                                             reply_markup=main_menu())

                    elif message.text == 'Я девушка':
                        user_name = '@' + message.from_user.username
                        if User.set_gender(message.chat.id, 'female', user_name):
                            bot.send_message(message.chat.id, '✅Ваш пол успешно добавлен!', reply_markup=main_menu())
                        else:
                            bot.send_message(message.chat.id, '❌Вы уже указали ваш пол, обратитесь в поддержку',
                                             reply_markup=main_menu())

                    elif message.text == 'Оценить предыдущего собеседника👍👎':
                        bot.send_message(message.chat.id, 'Оцените собеседника по 10 бальной школе,\n'
                                                          'нажмите кнопку', reply_markup=user_bal())

                    elif message.text == '👤Мой Аккаунт':
                        main_delete(message)
                        main_account(message)

                    elif message.text == '❤️Поддержать бота':
                        text = ('Эта кнопка внизу 👇🏻 позволяет вам сделать пожертвование на развитие телеграм бота. ✨'
                                'Нажав на нее, вы сможете выбрать сумму пожертвования и отправить ее боту. '
                                'Ваше доброе пожертвование поможет улучшить функциональность бота, '
                                'добавить новые возможности и продолжить его развитие.\n\n'
                                'Спасибо за вашу невероятную поддержку! ❤️')
                        bot.send_message(message.chat.id, text, reply_markup=donations())

                    else:
                        if Chat.get_active_chat(message.chat.id) != False:
                            chat_info = Chat.get_active_chat(message.chat.id)
                            bot.send_message(chat_info[1], message.text)
                        else:
                            bot.send_message(message.chat.id, '❌Вы не начали диолог')

            except telebot.apihelper.ApiTelegramException as e:  # в случае ошибки
                raise

        @bot.callback_query_handler(func=lambda callback: True)
        def callback_message(callback):
            try:
                if callback.message:
                    if callback.data:  # Удостоверьтесь, что callback_data существует
                        # Используйте edit_message_text или edit_message_reply_markup тут
                        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                              text='✅')
                        # Если вы хотите просто удалить кнопки, а текст оставить неизменным, рекомендуется использовать edit_message_reply_markup:
                        # bot.edit_message_reply_markup(call.message.chat.id, message_id=call.message.message_id)

                button_number = int(callback.data)  # бал пользователя !!!

                chat_id = callback.message.chat.id  # chat.id пользователя

                try:
                    ID = Chat_false.chat_SOB(chat_id)  # id строки в БД и ID собеседника !!!
                except Exception as e:
                    print(f"Ошибка при получении данных из БД: {e}")
                    return

                Score.rate_user(ID[1], button_number)
                # Chat_false.delete_chat_false(ID[0])  # удаление данных из табл Chat_false

                bot.send_message(callback.message.chat.id, 'Нажмите /menu', reply_markup=main_menu())
            except Exception as e:
                print(f"Неизвестная ошибка: {e}")

        # для обменна голосовых сообщений
        @bot.message_handler(content_types='voice')
        def bot_voice(message):
            try:
                if message.chat.type == 'private':
                    chat_infa = Chat.get_active_chat(message.chat.id)
                    if chat_infa != False:
                        bot.send_voice(chat_infa[1], message.voice.file_id)
                    else:
                        bot.send_message(message.chat.id, '❌Вы не начали диолог')
            except telebot.apihelper.ApiTelegramException:
                bot.send_message(message.chat.id, '❌Ошибка')

        # для обменна фото конт
        @bot.message_handler(content_types=['photo'])
        def bot_photo(message):
            try:
                raw = message.photo[2].file_id
                name = raw + ".jpg"
                file_info = bot.get_file(raw)
                downloaded_file = bot.download_file(file_info.file_path)
                with open(name, 'wb') as new_file:
                    new_file.write(downloaded_file)
                img = open(name, 'rb')

                if message.chat.type == 'private':
                    chat_infa = Chat.get_active_chat(message.chat.id)
                    if chat_infa != False:
                        bot.send_photo(chat_infa[1], img)
                        img.close()  # Закрываем файл перед удалением
                        os.remove(name)  # Удаляем файл после отправки
                    else:
                        bot.send_message(message.chat.id, '❌Вы не начали диолог')
                        img.close()  # Закрываем файл перед удалением
                        os.remove(name)  # Удаляем файл после отправки
            except telebot.apihelper.ApiTelegramException:
                bot.send_message(message.chat.id, '❌Ошибка')

        # для обменна видео в круглешках
        @bot.message_handler(content_types=['video_note'])
        def send_video(message):
            try:
                raw = message.video_note.file_id
                name = raw + ".mp4"
                file_info = bot.get_file(raw)

                downloaded_file = bot.download_file(file_info.file_path)

                with open(name, 'wb') as new_file:
                    new_file.write(downloaded_file)
                video = open(name, 'rb')

                if message.chat.type == 'private':
                    chat_infa = Chat.get_active_chat(message.chat.id)
                    if chat_infa != False:
                        bot.send_video_note(chat_infa[1], video)
                        video.close()  # Закрываем файл перед удалением
                        os.remove(name)  # Удаляем файл после отправки
                    else:
                        bot.send_message(message.chat.id, '❌Вы не начали диолог')
                        video.close()  # Закрываем файл перед удалением
                        os.remove(name)  # Удаляем файл после отправки

            except telebot.apihelper.ApiTelegramException:
                bot.send_message(message.chat.id, '❌Ошибка')

        # # bot.polling(none_stop=True)
        # if __name__=='__bot__':
        while True:
            try:
                bot.polling(none_stop=True, timeout=90)
            except Exception as e:
                print(datetime.datetime.now(), e)
                time.sleep(5)
                continue
