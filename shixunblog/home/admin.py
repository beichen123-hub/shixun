from django.contrib import admin

from home.models import *

# Register your models here.
# Register your models here.
# 凡是在这里注册的模型，都会被django自带的后台所管理
# 注册文章模型
admin.site.register(ArticleCategory)