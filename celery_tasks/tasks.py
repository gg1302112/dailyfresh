# 使用celery
from django.template import loader, RequestContext
from celery import Celery
from django.core.mail import send_mail
from dailyfresh import settings
from goods.models import GoodsType, IndexTypeGoodsBanner, IndexPromotionBanner, IndexGoodsBanner
import time
import os
# import django
# import sys
# sys.setrecursionlimit(1000000)
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()

app = Celery('celery_tasks.tasks', broker='redis://192.168.80.129:6379/8')


@app.task
def send_register_active_email(to_mail, username, token):
    """发送激活邮件"""
    subject = '你好天天生鲜'
    message = ''
    sender = settings.EMAIL_HOST_USER
    reciver = [to_mail]
    html_message = "<h1>天天生鲜<hi><br>%s欢迎来到天天生鲜，点击下面连接即可激活用户<a href='http://127.0.0.1:8000/user/active/%s'>http://127.0.0.1:8000/user/active/%s<a/>" % (
    username, token, token)
    send_mail(subject, message, sender, reciver, html_message=html_message)
    print('开始执行5秒钟')
    time.sleep(5)
    print('结束5秒钟')


@app.task
def get_static_index_html():
    """将页面静态化"""
    time.sleep(5)
    # 1.获取类型嘻嘻
    types = GoodsType.objects.all()
    # 2.获取轮播信息
    goodsBanner = IndexGoodsBanner.objects.all().order_by('index')
    # 3.获取活动信息
    promotionBanner = IndexPromotionBanner.objects.all().order_by('index')
    # 4.获取类型所包含的sku信息
    for type in types:
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        type.image_banner = image_banners
        type.title_banner = title_banners

    context = {
        'types': types,
        'goodsBanner': goodsBanner,
        'promotionBanner': promotionBanner
    }

    temp = loader.get_template('static_index.html')
    # context = RequestContext(request, context)
    static_index_html = temp.render(context)

    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)

