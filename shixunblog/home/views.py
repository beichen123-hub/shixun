import logging

from django.shortcuts import render
from django.views import View

from home.models import *

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

