import logging  # 导入logging包
import re  # 导入正则表达式包
from random import randint  # 导入随机数包

from django.contrib import auth
from django.contrib.auth import login  # 实现状态保持
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DataError  # 导入数据库异常包
from django.http.response import HttpResponseBadRequest
from django.http.response import JsonResponse  # 导入Json返回值包
from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection  # 导入redis

from home.models import ArticleCategory, Article
from libs.captcha.captcha import captcha  # 导入验证码
from libs.tongxun.sms import CCP  # 导入容联运包
from users.models import User  # 导入用户包
from utils.response_code import RETCODE  # 导入自定义相应码

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
        # 2.1、验证参数是否齐全
        if not all([mobile, password, password2, sms_code]):
            return HttpResponseBadRequest('缺少必要参数')
        # 2.2、验证手机号格式是否正确
        if not re.match('^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号码错误或格式不正确')
        # 2.3、验证密码是否符合格式
        if not re.match('^[0-9a-zA-Z]{8,20}$', password) or not re.match('^[0-9a-zA-Z]{8,20}$', password):
            return HttpResponseBadRequest('密码长度、格式不正确。长度8-20，必须是数字、字母')
        # 2.4 验证密码和确认密码是否一致
        if password != password2:
            return HttpResponseBadRequest('两次输入的密码不一致')
        # 2.5、验证短信验证码是否和redis中一致
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

        resp = redirect(reverse('home:index'))
        # 设置cookie以方便首页中用户信息进行判断和用户新的展示
        resp.set_cookie('is_login', True)
        # 通过cookie传递登录用户名，过期时间为1天
        resp.set_cookie('login_name', user.username, max_age=1 * 24 * 3600)
        # 4、返回响应跳转到指定页面
        # redirect是进行页面重定向
        # reverse是可以通过namespace:name来获取视图所对应的路由
        return resp
        # return HttpResponseRedirect('/')
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


# 登录
class LoginView(View):
    '''
           实现思路：
           1、接收提交参数
           2、验证参数
            2-1、手机号码是否符合规则
            2-2、密码是否符合规则
           3、用户认证登录
           4、状态保持
           5、根据用户选择的是否记住登录状态进行判断
           6、设置cookie信息，为首页显示服务
           7、跳转到首页
           :param request:
           :return:
           '''
    def get(self,request):
        return render(request,'login.html')


    def post(self,request):
        # 接收提交参数
        mobile=request.POST.get("mobile")
        password=request.POST.get("password")
        remember=request.POST.get("remember")
        if not all([mobile,password]):
            return render(request,'login.html',{'msg':'参数不齐全'})
        # 手机号码是否符合规则
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return render(request,'login.html',{'msg':'手机号码格式不正确'})
        # 密码是否符合规则
        if not re.match('^[a-z0-9A-Z]{8,20}$',password):
            return render(request,'login.html',{'msg':'密码格式不正确'})
        # 使用django系统自带的用户认证代码，将会返回一个user对象，如果账号密码正确就还返回该对象否则返回None
        return_user = auth.authenticate(mobile=mobile, password=password)
        print(return_user)
        if return_user is None:
            return render(request,'login.html',{'msg':'账号或密码错误'})
        request.session['name'] = return_user
        # 状态保持
        login(request, return_user)
        print('sss')
        # print(login(request, return_user))
        # 6、设置cookie信息，为首页显示服务
        # 根据匿名登录跳转参数next，跳转到指定页面
        next_page = request.GET.get('next')
        if next_page:
            resp = redirect(next_page)
        else:
            resp = redirect(reverse('home:index'))
        # 根据用户选择的是否记住登录状态进行判断
        if remember != 'on':

            resp.set_cookie('is_login',True)
            resp.set_cookie('login_name',return_user.username)
            request.session.set_expiry(0)
        else:
            resp.set_cookie('is_login', True,max_age=14*24*3600)
            resp.set_cookie('login_name', return_user.username,max_age=14*24*3600)
            request.session.set_expiry(None)#设置session的过期时间为默认值

        return resp


# 退出登录视图


class LogoutView(View):
    def get(self, request):
        '''
        实现思路：
        1、清除session数据
        2、删除cookie数据
        3、跳转到首页
        :param request:
        :return:
        '''
        # 实现思路：
        # 1、清楚session数据
        # logout(request)
        request.session.flush()
        # resp = redirect(reverse('home:index'))
        # print('ssss')
        # resp.delete_cookie('is_login')
        # resp.delete_cookie('login_name')
        # 2、删除cookie数
        # 3、跳转到首页
        # return resp
        return redirect(reverse('home:index'))


# 忘记密码
class ForgetPasswordView(View):
    def get(self, request):
        return render(request, "forgetpassword.html")

    def post(self, request):
        '''
        实现思路：
        1、接受数据
        2、验证数据
            2.1、判断参数是否齐全
            2.2、手机号是否符合规则
            2.3、判断密码是否符合规则
            2.4、判断确认密码是否一致
            2.5、判断短信验证码是否正确
        3、根据手机号码进行用户信息查询
        4、如果手机号查询出用户信息则进行用户密码的修改
        5、如果手机号没有查询出用户信息，则进行新用户的创建
        6、进行也买你跳转，跳转到登录页面
        7、返回响应
        :param request:
        :return:
        '''
        # 1、接受数据
        mobile = request.POST.get("mobile")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        sms_code = request.POST.get("sms_code")
        # 2、验证参数是否齐全
        # 2.1、判断参数是否齐全
        if not all([mobile, password, password2, sms_code]):
            return HttpResponseBadRequest('缺少必要参数')
            # return render(request, 'forget_password.html', {'msg':'缺少必要参数'})
        # 2.2、手机号是否符合规则
        if not re.match('^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号格式不正确')
        # 2.3、判断密码是否符合规则
        if not re.match('^[0-9a-zA-Z]{8,20}$', password):
            return HttpResponseBadRequest('密码格式不正确')
        # 2.4、判断确认密码是否一致
        if password != password2:
            return HttpResponseBadRequest('两次密码输入不一致')
        # 2.5、判断短信验证码是否正确
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s' % mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码过期')
        try:
            if redis_sms_code.decode() != sms_code:
                return HttpResponseBadRequest('验证码错误')
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('验证码错误')

        # 3、根据手机号码进行用户信息查询
        user = User.objects.filter(mobile=mobile).first()
        # 4、如果手机号查询出用户信息则进行用户密码的修改
        # 5、如果手机号没有查询出用户信息，则进行新用户的创建
        if user is None:
            try:
                User.objects.create_user(username=mobile, mobile=mobile, password=password)
            except Exception as e:
                logger.error(e)
                return HttpResponseBadRequest('注册失败')
        else:
            try:
                # 调用系统user对象的set_password()进行修改密码，该方法会对密码进行加密
                user.set_password(password)
                user.save()
            except Exception as e:
                logger.error(e)
                return HttpResponseBadRequest('修改密码失败')
        # 6、进行页面跳转，跳转到登录页面
        resp = redirect(reverse('users:login'))
        return resp


'''
LoginRequiredMixin:封装了判断用户是否登录的操作
1、待验证视图需要继承该类即可，他会自动验证身份信息
2、如果用户未登录，那么就是匿名用户，当访问该视图是，会自动进行跳转到默认登录地址
3、需要在setting中设置默认登录地址访问LOGIN_URL = '/login/'
4、在登录该视图的post方法中，判断next有值跳转
'''


# 用户中心
class UserCenterView(LoginRequiredMixin, View):
    def get(self, requset):
        # 需要判断用户是否登录，根据用户是否登录的结果，决定用户是否可以访问用户中心
        # if not requset.user.is_authenticated:     # 判断用户是否登录，如果通过登录验证则返回true，否则返回false
        #     return redirect(reverse('users:login'))
        userinfo = requset.user
        context = {
            'username': userinfo.username,
            'mobile': userinfo.mobile,
            'avatar': userinfo.avatar.url if userinfo.avatar else None,
            'user_desc': userinfo.user_desc,
        }
        return render(requset, 'usercenter.html', context=context)

    def post(self, request):
        userinfo = request.user
        username = request.POST.get('username')
        user_desc = request.POST.get('desc')
        avatar = request.FILES.get('avatar')
        try:
            userinfo.username = username
            userinfo.user_desc = user_desc
            if avatar:
                userinfo.avatar = avatar
            userinfo.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('修改用户信息失败')
        # 3、更新cookie中的username
        # 4、刷新当前页面（重定向操作）
        resp = redirect(reverse('users:usercenter'))
        resp.set_cookie('login_name', userinfo.username)
        # 5、返回相应
        return resp


class WriteBlogView(LoginRequiredMixin, View):
    def get(self, requset):
        if requset.session.get('name'):

            # 获取所有分类信息
            categories = ArticleCategory.objects.all()
            context = {
                'list': categories
            }
            return render(requset, 'writeblog.html', context=context)

        return redirect(reverse('home:index'))


    def post(self, request):
        '''
        实现思路：
        1、接收数据
        2、验证数据
        3、数据入库
        4、跳转到指定页面
        :param request:
        :return:
        '''
        # 1、接收数据
        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        tags = request.POST.get('tags')
        sumary = request.POST.get('sumary')
        content = request.POST.get('content')
        user = request.user
        print(avatar, title, category_id, sumary, tags, content)
        # 2、验证数据
        # 2-1、参数齐全验证
        if not all([avatar, title, category_id, sumary, content]):
            return HttpResponseBadRequest('参数不齐全')
        # 2-2、判断分类id
        try:
            category = ArticleCategory.objects.filter(pk=category_id).first()
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有该分类信息')
        # 3、数据入库
        try:
            Article.objects.create(
                author=user,
                avatar=avatar,
                category=category,
                tags=tags,
                sumary=sumary,
                content=content,
                title=title
            )
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('发布失败，请稍后重试')
        # 4、跳转到指定页面
        return redirect(reverse('home:index'))
