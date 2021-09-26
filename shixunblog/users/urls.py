#!/usr/bin/python
# -*- coding:utf-8 -*-
# @workbench    :ASUS
# @author  : BeiChen
# email    :192201393@qq.com
# @time    : 2021/9/26 9:52
# @function: the script is used to do something.
# IDE      : PyCharm 
# project name:shixunblog
from django.urls import path
from users.views import RegisterView, ImageView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('imagecode/', ImageView.as_view(), name='imagecode'),
]