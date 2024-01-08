from django.shortcuts import redirect
from project_Tg.settings import PROXY_URL


def index(request):
    if request.method == 'GET':
        return redirect(PROXY_URL)