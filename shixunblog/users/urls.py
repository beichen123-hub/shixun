#!/usr/bin/python
# -*- coding:utf-8 -*-
# @workbench    :ASUS
# @author  : BeiChen
# email    :192201393@qq.com
# @time    : 2021/9/26 9:52
# @function: the script is used to do something.
# IDE      : PyCharm 
# project name:shixunblog
# 子应用路由
from django.urls import path
from users.views import * # 导入注册视图


urlpatterns = [
    # 参数1：路由
    # 参数2：视图函数
    # 参数3：路由名，方便通过reverse来获取路由
    path('register/',RegisterView.as_view(), name='register'),
    # 图片验证码路由
    path('imagecode/',ImageView.as_view(), name='imagecode'),
    # 短信验证码
    path('smscode/',SmsCodeView.as_view(), name='smscode'),
    path('login/',loginView.as_view(), name='login'),
    path('login.html/',loginView.as_view(), name='login'),
    path('logout/',logoutView.as_view(), name='logout'),
    path('forgetpassword/', ForgetPasswordView.as_view(),name='forgetpassword'),
]