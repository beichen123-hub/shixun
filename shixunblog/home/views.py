import logging

from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from home.models import *

# from audioop import reverse

# Create your views here.
logger = logging.getLogger("django_log")


class IndexView(View):
    def get(self, request):
        # 1、获取所有的文字分类
        acs = ArticleCategory.objects.all()

        # 2、获取用户点击的分类id
        cat_id = request.GET.get('cat_id', 1)

        # 3、被选中的文章分类
        try:
            ac = ArticleCategory.objects.get(id=cat_id)
        except ArticleCategory.DoesNotExist:
            logger.error('分类id不存在')
            return render(request, 'index.html', context={'msg': '分类id不存在'})

        # 4、根据被选中的分类信息查询该分类下的文字
        arts = Article.objects.filter(category=ac)

        # 4、获取分页参数
        page_index = request.GET.get('page_index', 1)  # 页码
        page_size = request.GET.get('page_size', 1)  # 页容量
        # 6、创建分页器
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # 导入django分页插件
        # Paginator(待分页的对象, 页容量)
        pages = Paginator(arts, page_size)  # 对查询到的数据对象articles进行分页，设置超过指定页容量就分页

        try:
            list = pages.page(page_index)  # 获取当前页面的记录
        except PageNotAnInteger:
            list = pages.page(1)  # 如果用户输入的页面不是整数时，显示第1页的内容
        except EmptyPage:
            list = pages.page(pages.num_pages)  # 如果用户输入的页数不在系统的页码列表中时,显示最后一页的内容
        # 4、组织数据传递给模板
        context = {
            'categories': acs,
            'category': ac,
            'articles': list,
            'cat_id':cat_id
        }
        return render(request, 'index.html', context=context)


class DetailView(View) :
    def get(self, request):
        # 1、获取文章id
        art_id = request.GET.get('art_id')
        # 2、根据文章id查询文章信息
        try:
            art = Article.objects.get(id=art_id)
        except Article.DoesNotExist:
            return render(request,'404.html')
        # 2-1、浏览量的简单做法:只要被查询一次，那么就算- - 次访问
        art.total_views += 1
        art.save()
        # 2-2、重新查询文章信息，按照浏览量降序排序(热门标签)
        hot_tags = Article.objects.values('tags').order_by('-total_views').distinct()[:9]
        # 2-3、最新文章
        new_arts = Article.objects.order_by('-create_time')[:2]
        # 2-4、获取所有评论信息
        comm = Comment.objects.filter(article=art).order_by('-created_time')
        # 3、返回页面
        context = {
            'article': art,
            'hot_tags': hot_tags,
            'new_arts': new_arts,
            'comms': comm
        }
        print(hot_tags,new_arts)
        return render(request,'detail.html', context=context)
    def post(self,request):
        # 1、获取已登录用户信息
        user = request.user
        # 2、判断用户是否登录
        if user and user.is_authenticated:
            # 3、登录用户才可以接收form数据
            # 3-1、接收评论数据
            art_id = request.POST.get('art_id')
            content = request.POST.get('content')
            # 3-2、验证文章是否存在.
            try:
                art = Article.objects.get(id=art_id)
            except Article.DoesNotExist:
                return HttpResponseBadRequest('该文章不存在')
            # 3-3、保存评论数据
            Comment.objects.create(content=content, article=art, user=user)
            # 3-4、 修改文章的评论数量
            art.comments_count += 1
            art.save()
            # 刷新当前页面
            req_url = request.path + '?art_id=' + art_id
            return redirect(req_url)
        else:
            # 4、未登录用户则跳转到登录页面.
            return redirect(reverse('users:login'))

