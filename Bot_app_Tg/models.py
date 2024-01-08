import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.db.models import Q, Min
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.utils import timezone

from project_Tg.celery import celery_app


class User(models.Model):
    gen = [('male', 'Мужской'), ('female', 'Женский')]
    chat_id = models.CharField(max_length=255, unique=True, verbose_name="ID пользователя")  # уникальное поле
    gender = models.CharField(max_length=60, choices=gen, verbose_name="Пол")  #
    user_name = models.CharField(max_length=255, blank=True, verbose_name="@user_name")
    last_visit = models.DateTimeField(auto_now_add=True, verbose_name="Время первого посещения")  # время создание
    time_update = models.DateTimeField(auto_now=True, verbose_name="Время последнего посещения")  # время его последнего редактирование
    online = models.BooleanField(default=False, verbose_name="Online")  # флажок на online
    is_blocked = models.BooleanField(default=False, verbose_name="Блокировка")  # флажок на блокировку, по умол нет

    class Meta:
        verbose_name = 'Зарегистрированные пользователи'
        verbose_name_plural = 'Зарегистрированные пользователи'
        ordering = ['time_update']

    @property
    def average_score(self):  # высчитываем среднее арифм
        average = self.scores.aggregate(average=models.Avg('value'))['average']
        return round(average, 1) if average else 10

    average_score.fget.short_description = 'Бал пользователя'

    @staticmethod
    def set_online_status(chat_id, chat_two, status):  # статус online
        try:
            user1 = User.objects.get(chat_id=chat_id)
            user2 = User.objects.get(chat_id=chat_two)

            user1.online = status
            user1.save()

            user2.online = status
            user2.save()
        except ObjectDoesNotExist:
            print(f'Пользователь с chat_id {chat_id} не существует\n'
                  f'Пользователь с chat_id {chat_two} не существует')

    @staticmethod
    def user(chat_id):
        gender_dict = {'male': 'Мужской', 'female': 'Женский'}  # словарь для преобразования пола
        user = User.objects.get(chat_id=chat_id)
        count = Chat_false.objects.filter(Q(chat_sob=chat_id) | Q(chat_may=chat_id)).count()
        gender = gender_dict.get(user.gender, user.gender)  # Преобразуем пол пользователя с помощью словаря
        return [user.user_name, gender, user.average_score, count]

    @staticmethod
    def set_gender(chat_id, gender, user_name):  # этот метод используется для удаления дубликатов пользователей в базе данных
        user = User.objects.filter(chat_id=chat_id).first()
        if user is None:
            User.objects.create(chat_id=chat_id, gender=gender, user_name=user_name)  # и добавления новых данных о поле пользователя (если у пользователя нет дубликатов)

            # при регистрации накидываем 10 балов
            user = User.objects.get(chat_id=chat_id)
            # Создаем новый объект оценки (Score) при регистрации накидываем 10 балов
            new_score = Score(user=user, value=10)
            new_score.save()
            # присваеваем @user_name
            return True
        else:
            # обновляем поле time_update
            user.time_update = timezone.now()  # не забудьте импортировать timezone из django.utils
            user.save()  # сохраняем изменения
            return False

    @staticmethod
    def get_gender(chat_id):  # Эта функция используется для получения пола (gender) пользователя из базы данных,
        user = User.objects.filter(chat_id=chat_id).first()  # используя его идентификатор чата (chat_id)
        if user:
            return user.gender
        else:
            return False


class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scores', verbose_name="Пользователь")
    value = models.PositiveSmallIntegerField(verbose_name="Балы пользователей")

    @staticmethod
    def rate_user(chat_id, value):  # берем польз и ставим ему баллы
        # Вместо chat_id используем уникальный идентификатор пользователя, который мы сохраняем в поле chat_id
        user = User.objects.get(chat_id=chat_id)

        # Создаем новый объект оценки (Score)
        new_score = Score(user=user, value=value)
        new_score.save()

    @staticmethod
    @celery_app.task
    def delete_scores(user):
        # print(chat_id)
        # user = User.objects.get(chat_id=chat_id)
        # scores = user.scores.all().order_by('id')
        scores = Score.objects.filter(user=user).order_by('id')
        if scores.count() > 1:
            min_score_id = scores.aggregate(Min('id'))['id__min']
            scores.exclude(id=min_score_id).delete()

            # убираем блокировку
            blocked = User.objects.get(id=user)  # получить пользователя по indif
            blocked.is_blocked = False
            blocked.save()

###################### МЕТОД АВТО БЛОКИРОВКИ ##################################
@receiver(post_save, sender=Score)
def update_user_status(sender, instance, **kwargs):
    user = instance.user
    if user.average_score < 3:
        user.is_blocked = True
        user.save(update_fields=["is_blocked"])
        # print(user.__dict__)  # print(vars(user))
        # print(user.chat_id)
        users = user.pk  # можно передавать сразу id
        Score.delete_scores.apply_async(args=[users], eta=timezone.now() + datetime.timedelta(days=1))  # minutes=13
        # proverka.apply_async(args=[10], eta=timezone.now() + datetime.timedelta(minutes=2))

    else:
        user.is_blocked = False
        user.save(update_fields=["is_blocked"])
#########################################################


class Queue(models.Model):
    gen = [('male', 'Мужской'), ('female', 'Женский')]
    chat_id = models.CharField(max_length=255, verbose_name="ID пользователя")
    gender = models.CharField(max_length=60, choices=gen, verbose_name="Пол")
    time_queued = models.DateTimeField(auto_now_add=True, verbose_name="Время добавление в очередь")

    class Meta:
        verbose_name = 'Пользователи которые ищут собеседника'
        verbose_name_plural = 'Пользователи которые ищут собеседника'
        ordering = ['time_queued']

    @classmethod
    def add_queue(cls, chat_id, gender):  # функция delete_queue удаляет из таблицы queue все записи, связанные с указанным chat_id
        queue = cls(chat_id=chat_id, gender=gender)
        return queue.save()
    # Queue.add_queue(chat_id='123', gender='female') - так можно применить в коде бота

    @staticmethod
    def delete_queue(chat_id):  # функция delete_queue удаляет из таблицы queue все записи, связанные с указанным chat_id
        queue = Queue.objects.filter(chat_id=chat_id)
        if queue.exists():
            queue.delete()
            return True  # Если объект был найден и успешно удалён
        else:
            return False  # Если объект не найден

    @staticmethod
    def get_gender_chat(gender):  # функция get_gender_chat предназначена для получения информации о пользователе (идентификатор и пол) из очереди в базе данных,
        chat = Queue.objects.filter(gender=gender)[:1]  # соответствующей указанному полу (gender).
        if chat:
            user_info = [chat[0].chat_id, chat[0].gender]
            return user_info
        else:
            return [0]

    @staticmethod
    def get_chat():  # этот код выполняет выборку одной строки из таблицы "queue" базы данных и возвращает информацию о пользователе (второй и третий элемент строки) или возвращает [0],
        chat = Queue.objects.all()[:1]  # если таблица "queue" пуста.
        if chat:
            user_info = [chat[0].chat_id, chat[0].gender]
            return user_info
        else:
            return [0]


class Chat(models.Model):
    chat_one = models.CharField(max_length=255, verbose_name="ID 1 пользователя")
    chat_two = models.CharField(max_length=255, verbose_name="ID 2 пользователя")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время начала чат-сессии")

    class Meta:
        verbose_name = 'Чат-сессии'
        verbose_name_plural = 'Чат-сессии'
        ordering = ['created_at']

    @staticmethod
    def delete_chat(id_chat):
        chat = Chat.objects.filter(pk=id_chat)
        if chat.exists():
            chat.delete()
            return True  # Если объект был найден и успешно удалён
        else:
            return False  # Если объект не найден

        # return Chat.objects.filter(pk=id_chat).delete()

    @staticmethod
    def create_chat(chat_one, chat_two):  # Цель этого метода - создать новый объект "чат" (Chat), но это произойдет только если существуют объекты в очереди (Queue), связанные с переменной chat_two.
        queue = Queue.objects.filter(chat_id=chat_two)
        with transaction.atomic():
            if queue.exists():
                queue.delete()
                Chat.objects.create(chat_one=chat_one, chat_two=chat_two)
                return True
            else:
                return False

    @staticmethod
    def get_active_chat(chat_id):
        try:
            chat = Chat.objects.get(chat_one=chat_id)
            return [chat.id, chat.chat_two]
        except ObjectDoesNotExist:
            pass
        try:
            chat = Chat.objects.get(chat_two=chat_id)
            return [chat.id, chat.chat_one]
        except ObjectDoesNotExist:
            return False


class Chat_false(models.Model):
    chat_sob = models.CharField(max_length=30, verbose_name="ID собеседника")
    chat_may = models.CharField(max_length=30, verbose_name="ID мой")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время удаления чат-сессии")

    @staticmethod
    def chat_SOB(id_chat):
        chat = None  # добавить значения по умолчанию до блока try/except
        try:
            Id1 = Chat_false.objects.filter(chat_sob=id_chat).latest('created_at')
            chat = [Id1.id, int(Id1.chat_may)]
        except Chat_false.DoesNotExist:
            pass

        try:
            Id2 = Chat_false.objects.filter(chat_may=id_chat).latest('created_at')
            chat = [Id2.id, int(Id2.chat_sob)]
        except Chat_false.DoesNotExist:
            pass

        if chat != id_chat:
            return chat
        else:
            return None

    @staticmethod
    def delete_chat_false(id_chat):
        return Chat_false.objects.filter(pk=id_chat).delete()


class UserProfile(models.Model):
    title = models.CharField(max_length=150, blank=False, default='Напишите название статьи', verbose_name="имя статьи")
    content = models.TextField(verbose_name="текст")  # текстовое поле(более большое расширенное) данное поле может быть пустым
    photo = models.ImageField(blank=True, upload_to="photo/%Y/%m/%d/", verbose_name="изображение")  # хранит ссылку нашего изображения
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="время создания")
    publish = models.BooleanField(default=False, verbose_name="выбрать")  # флажок на выбор рассылки

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-created_at']