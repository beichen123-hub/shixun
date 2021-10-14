#!/usr/bin/python
# -*- coding:utf-8 -*-
# @workbench    :ASUS
# @author  : BeiChen
# email    :192201393@qq.com
# @time    : 2021/9/27 11:00
# @function: the script is used to do something.
# IDE      : PyCharm 
# project name:shixunblog
from django.urls import path

from home.views import IndexView, DetailView

urlpatterns = [

    path('',IndexView.as_view(), name='index'),
    # path('detail/index.html',IndexView.as_view(), name='index'),
    path('detail/',DetailView.as_view(), name='detail'),

]