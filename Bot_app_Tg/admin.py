from django.contrib import admin, messages
from django.utils.safestring import mark_safe

from .models import *
from .tasks import *


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_content', 'get_html_photo', 'publish', 'created_at')
    list_editable = ('publish',)  # Список полей, которые можно редактировать прямо со страницы списка
    search_fields = ('title',)
    list_filter = ('created_at', 'publish')
    fields = ('title', 'content', 'photo', 'get_html_photo', 'publish')
    readonly_fields = ('get_html_photo',)
    list_per_page = 20  # сколько записей на одной странице
    save_on_top = True  # кнопки "Сохранить" и "Сохранить внизу и верху
    admin.site.empty_value_display = 'По умолчанию'
    
    def short_content(self, obj):
        return obj.content[:300]  # Возвращаем первые 300 символов

    short_content.short_description = 'текст'

    def get_html_photo(self, object):
        if object.photo:
            return mark_safe(f"<img src='{object.photo.url}' width=150")

    get_html_photo.short_description = 'изображение'


class UserAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'gender', 'user_name', 'average_score', 'online', 'last_visit', 'time_update', 'is_blocked')  # Список полей, которые будут выведены
    search_fields = ('chat_id', 'last_visit', 'time_update', 'user_name')  # Список полей, по которым будет работать механизм поиска
    list_editable = ('is_blocked', 'gender')  # Список полей, которые можно редактировать прямо со страницы списка
    list_filter = ('last_visit', 'time_update', 'gender', 'online')  # фильтр справа
    # fields = ('chat_id', 'gender', 'is_blocked')  # Список полей, которые будут отображаться для редактирования
    readonly_fields = ('user_name', 'last_visit', 'time_update', 'average_score', 'online')  #  Список полей, которые будут отображаться только для чтения.
    list_per_page = 10  # сколько записей на одной странице
    save_on_top = True  # кнопки "Сохранить" и "Сохранить внизу и верху

    admin.site.empty_value_display = 'По умолчанию'

    actions = ['send_newsletter']

    @admin.action(description='Отправить рассылку')
    def send_newsletter(self, request, queryset):
        chats_id = queryset.values_list('chat_id', flat=True)  # все кого выбрали

        user_profile = UserProfile.objects.filter(publish=True).first()
        if user_profile is not None:
            id_value = user_profile.id

            fields = ('content', 'photo')
            data = UserProfile.objects.filter(id=id_value).values(*fields)

            text = "Рассылка отправлена успешно."

            for entry in data:
                content = entry['content']
                photo = entry['photo']

            if not content:
                messages.error(request, "Поле контента является обязательным.")

            else:
                if not photo:
                    for user in chats_id:
                        send_message.delay(user, content)
                    messages.success(request, text)
                else:
                    for user in chats_id:
                        send_photo.delay(user, photo, content)
                    messages.success(request, text)
        else:
            # Обработка случая, когда не найден ни один объект UserProfile, удовлетворяющий условию
            messages.error(request, "В таблици рассылка не выбранна ")


class QueueAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'gender', 'time_queued')
    search_fields = ('chat_id', 'time_queued')
    list_filter = ('time_queued',)  # фильтр
    readonly_fields = ('id', 'chat_id', 'gender', 'time_queued')

    def has_add_permission(self, request):
        # Запрещаем добавление новых пользователей
        return False

    def get_actions(self, request):
        # Удаляем действия по добавлению новых пользователей из админ-панели
        actions = super().get_actions(request)
        if 'add_selected' in actions:
            del actions['add_selected']
        if 'add' in actions:
            del actions['add']
        return actions


class ChatAdmin(admin.ModelAdmin):
    list_display = ('chat_one', 'chat_two', 'created_at')
    search_fields = ('chat_one', 'chat_two', 'created_at')
    list_filter = ('created_at',)  # фильтр
    readonly_fields = ('id', 'chat_one', 'chat_two', 'created_at')

    def has_add_permission(self, request):
        # Запрещаем добавление новых пользователей
        return False

    def get_actions(self, request):
        # Удаляем действия по добавлению новых пользователей из админ-панели
        actions = super().get_actions(request)
        if 'add_selected' in actions:
            del actions['add_selected']
        if 'add' in actions:
            del actions['add']
        return actions


admin.site.register(User, UserAdmin),
admin.site.register(Queue, QueueAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

admin.site.site_title = 'Моя админ-панель'
admin.site.site_header = 'Админ-панель: Анонимный чат бот'