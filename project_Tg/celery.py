from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_Tg.settings')
# Загружаем настройки при запуске Django
celery_app = Celery('project_Tg')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()

# celery_newsletter = Celery('project_Tg')
# celery_newsletter = config_from_object('django.conf:settings', namespace='CELERY')
# celery_newsletter = autodiscover_tasks()
