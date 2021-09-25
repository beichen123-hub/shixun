"""shixunblog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

# 1、导入系统logging
import logging
# 2、创建日志器
logger = logging.getLogger('django_log')


from django.http import HttpResponse


def test_log(request):
    # 3、调用日志器记录日志
    logger.info('我是一条日志信息')
    return HttpResponse('日志记录测试')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', test_log)
]