import json

from home.models import *


def common_hottages_news(request):
    news_artcle = Article.objects.order_by("-create_time")[0:2]
    hot_tags = Article.objects.values("tags").order_by("-total_views").distinct()[0:9]
    # 读取cookie中的用户信息
    if 'login_name' in request.COOKIES:
        username = request.COOKIES.get('login_name')
        username = json.loads(username)
    else: # 如果没有读取到该cookie，那么久给个空字符串
        username = ""
    return {"newsartcle": news_artcle, "hotTags": hot_tags, "username": username}