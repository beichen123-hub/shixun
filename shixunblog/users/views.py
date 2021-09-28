from django.shortcuts import render, HttpResponse, redirect
from django.views import View
from django.http.response import HttpResponseBadRequest
from libs.captcha.captcha import captcha    # 导入验证码
from django_redis import get_redis_connection   # 导入redis
from django.http.response import JsonResponse   # 导入Json返回值包
from utils.response_code import RETCODE  # 导入自定义相应码
import logging  # 导入logging包
from random import randint  # 导入随机数包
from libs.tongxun.sms import CCP     # 导入容联运包
import re   # 导入正则表达式包
from users.models import User   # 导入用户包
from django.db import DataError # 导入数据库异常包
from django.urls import reverse
from django.contrib.auth import login,authenticate

logger = logging.getLogger("django")

# Create your views here.
# CBV


# 注册视图
class RegisterView(View):
    # 注册页面展示
    def get(self, request):
        return render(request, "register.html")
    def post(self, request):
        """
        实现思路：
        1、接受用户数据
        2、验证数据
            2.1、参数是否齐全
            2.2、手机号格式是否正确
            2.3、密码是否符合格式
            2.4、密码和确认密码是否一致
            2.5、短信验证码是否和redis中的一致
        3、保存注册信息
        4、返回响应跳转到指定页面
        :param request:
        :return:
        """
        # 接收用户数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        sms_code = request.POST.get('sms_code')
        # 验证数据
        # 2.1、参数是否齐全
        if not all([mobile, password, password2, sms_code]):
            return HttpResponseBadRequest('缺少必要参数')
        # 2.2、手机号格式是否正确
        if not re.match('^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号码格式不正确')
        # 2.3、密码是否符合格式
        if not re.match('^[0-9a-zA-Z]{8,20}$', password) or not re.match('^[0-9a-zA-Z]{8,20}$', password):
            return HttpResponseBadRequest('密码长度、格式不正确。长度8-20，必须是数字、字母')
        # 2.4 面膜和确认密码是否一致
        if password != password2:
            return HttpResponseBadRequest('两次输入的密码不一致')
        # 2.5、短信验证码是否和redis中一致
        redis_conn = get_redis_connection('default')
        sms_code_redis = redis_conn.get('sms:%s' % mobile)
        if sms_code_redis is None:
            return HttpResponseBadRequest('短信验证码过期')
        try:
            # 删除验证码，避免恶意测试验证码
            redis_conn.delete('sms:%s' % mobile)
        except Exception as e:
            logger.error(e)
        if sms_code_redis.decode() != sms_code:
            return HttpResponseBadRequest('验证码错误')
        # 3、保存注册信息
        # create_user可是使用系统的方法对密码进行加密
        try:
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)
        except DataError as e:
            logger.error(e)
            return HttpResponseBadRequest('注册失败')
            # 实现状态保持
        login(request, user)
            # 4、返回响应跳转到指定页面
        # redirect是进行页面重定向
        # reverse是可以通过namespace:name来获取视图所对应的路由
        resp = redirect(reverse('home:index'))
        resp.set_cookie('is_login',True)
        resp.set_cookie('lohin_name', user.username, max_age=1 * 24 *3600)
        return resp
        # return HttpResponse('注册成功')




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

# 发送短信验证码视图
class SmsCodeView(View):
    def get(self, request):
        """
        实现思路：
        1、接收参数
        2、参数验证
            2.1 验证参数是否齐全
            2.2 图片验证码的验证
                连接redis,获取redis中图片验证码
                判断图片验证码未过期，我们获取之后就可以删除图片验证码
                比对图片验证码（忽略用户大小写）
        3、生成短信验证码
        4、保存短信验证码内容到redis中
        5、发送短信
        6、返回响应信息
        :param request:
        :return:
        """
        # 1、接受参数
        mobile = request.GET.get('mobile')
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        # 2、参数验证
        # 2.1 验证参数是否齐全
        if not all([mobile, image_code, uuid]):
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必要的参数'})
        # 2.2 图片验证码的验证
        # 连接redis,获取redis中图片验证码
        # 创建redis连接对象
        redis_conn = get_redis_connection('default')
        # 根据传来的图片uuid,获取redis中的image值
        redis_image_code = redis_conn.get('img:%s' % uuid)
        # 判断图片验证码是否存在
        if redis_image_code is None:
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码已过期'})
        # 如果图片验证码未过期，我们获取到之后就可以删除图片验证码
        try:
            # 删除图形验证码，避免恶意测试图形验证码
            redis_conn.delete('img:%s' % uuid)
        except Exception as e:
            logger.error(e)
        # 比对图片验证码（全部转为小写）redis中的数据是bytes类型
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码错误'})
        # 3、生成短信验证码：生成6位数验证码
        sms_code = '%06d' % randint(0, 999999)
        # 为了后期测试方便，我们可以把短信验证码记录到日志中
        logger.info(f'短信验证码: {sms_code}')
        # 4、保存短信验证码内容到redis中，保存时间1分钟
        redis_conn.setex('sms:%s' % mobile, 60, sms_code)
        # 5、发送短信
        CCP().send_template_sms(mobile, [sms_code, 1], 1)
        # 6、短信发送成功返回响应信息
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '短信发送成功'})


class loginView(View):
    def get(self,request):
        return render(request,"login.html")
    def post(self,request):
        username = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        if not all([username,password]):
            return render(request,template_name='login.html',context={'msg':'账号密码不能为空'})
        if not re.match('^1[3-9]\d{9}$',username):
            return render(request,template_name='login.html',context={'msg':'手机号码格式不正确'})
        if not re.match('^[a-z0-9A]{8,20}$',password):
            return render(request,template_name='login.html',context={'msg':'密码格式不正确'})
        return_user = authenticate(mobile=username,password=password)
        if return_user is None:
            return render(request, template_name='login.html', context={'msg':'账号或密码错误'})

        login(request, return_user)
        resp = redirect(reverse('home:index'))
        # 根据用户选择的是否记住登录状态进行判时
        if remember != "on":  # 用户没有勾选复选相
            resp.set_cookie('is_login', True)
            resp.set_cookie('login_name', return_user.username)
            request.session.set_expiry(0)
        else:
            # 设置2周内的 cookie
            resp.set_cookie('is_login',True, max_age=24*3600*14)
            resp.set_cookie('Login_name', return_user.username, max_age=24*3600*14)
            request.session.set_expiry(None)  # 表示设置默认时长,默认就是2周时间
        return resp