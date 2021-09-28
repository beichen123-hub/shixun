from django.db import models

# 导入系统抽象类用户
from django.contrib.auth.models import AbstractUser


# Create your models here.

class User(AbstractUser):
    # 手机号
    # max_length:手机号长度11位；unique：手机号是唯一的；blank:手机号为必填项
    mobile = models.CharField(max_length=11, unique=True, blank=False)

    # 头像信息
    # upload_to:上传文件地址为：avatar文件夹下以年月日方式命名文件；blank:头像不是必填项
    avatar = models.ImageField(upload_to='avatar/%Y%m%d/', blank=True)

    # 简介信息
    # max_length:简介长度500；blank：用户简介不是必填项
    user_desc = models.CharField(max_length=500, blank=True)
    USERNAME_FIELD = "mobile"

    class Meta:
        db_table = 'tb_users'  # 修改表名
        verbose_name = '用户管理'  # admin 后台显示
        verbose_name_plural = verbose_name  # admin 后台显示

    def __str__(self):
        return self.mobile