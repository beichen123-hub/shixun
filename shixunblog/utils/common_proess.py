#
# from home.models import Article, ArticleCategory
#
#
# def common_data(requst):
#     # categories = ArticleCategory.objects.all()
#     # # 2、接收用户点击的分类id
#     # cat_id = request.GET.get('cat_id', 1)
#     # # 3、根据分类id进行分类的查询
#     # try:
#     #     category = ArticleCategory.objects.get(id=cat_id)
#     # except ArticleCategory.DoesNotExist:
#     #     return HttpResponseBadRequest('此分类信息不存在')
#     # articles = Article.objects.filter(category=category)
#     hot_tags = Article.objects.values('tags').order_by('total_views').distinct()[:9]
#     new_arts = Article.objects.order_by('-create_time')[:2]
#     return {"hot_tags":hot_tags,"new_arts":new_arts}