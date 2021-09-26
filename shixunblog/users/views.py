from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
# Create your views here.
from libs.captcha.captcha import captcha


class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

# 验证码视图
class ImageView(View):
    def get(self, request):
        '''
        步骤：
        1、接收前端传递过来的uuid
        2、判断uuid失分获取到
        3、通过调用captcha来生成图片验证码（返回：图片内容和图片二进制）
        4、将图片内容保存到redis中。uuid作为key，图片内容作为值，同时还需要设置一个过期时间
        5、返回图片给前端
        :param request:
        :return:
        '''

        # 1、接收前端传递过来的uuid
        uuid = request.GET.get('uuid')
        # 2、判断uuid失分获取到
        if uuid is None:
            return HttpResponseBadRequest('没有获取到uuid')
        # 3、通过调用captcha来生成图片验证码（返回：图片内容和图片二进制）
        txt, image = captcha.generate_captcha()
        # 4、将图片内容保存到redis中。uuid作为key，图片内容作为值，同时还需要设置一个过期时间
        redis_conn = get_redis_connection('default')
        # name:数据key，这里采用img前缀：uuid
        # time:300秒后过期
        # value：对应key的值
        redis_conn.setex(name='img:%s' % uuid, time=300, value=txt)
        # 5、返回图片给前端
        return HttpResponse(image, content_type='image/jpeg')