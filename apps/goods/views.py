from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from Mixin.login_require import LoginRequireMixin
from django.views.generic import View
from .models import GoodsType, GoodsSKU, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner
from django_redis import get_redis_connection
from django.core.cache import cache

# Create your views here.


# def index(request):
#     """首页"""
#     return render(request, 'index.html')


class Goods(LoginRequireMixin, View):
    """商品类"""
    def get(self, request):
        """首页"""
        # 获取首页数据
        context = cache.get('index_page_data')

        if context is None:
            types = GoodsType.objects.all()
            goodsBanners = IndexGoodsBanner.objects.all().order_by('index')
            promotionbanners = IndexPromotionBanner.objects.all().order_by('index')
            # types_all = []
            for type in types:
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
                type.image_banners = image_banners
                type.title_banners = title_banners
                # types_all.append(type)

            context = {
                'types': types,
                'goodsBanners': goodsBanners,
                'promotionbanners': promotionbanners}

            print('开始设置缓存')
            cache.set('index_page_data', context, 3600)
            print('结束设置缓存')

        user = request.user

        cart_count = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        context.update(cart_count=cart_count)
        return render(request, 'index.html', context)


class DetailView(View):
    """详情页"""
    def get(self, request, goods_id):
        # 获取种类明细
        # 尝试获取商品信息
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist as e:
            return redirect(reverse('goods:index'))
        # 获取全部商品类型
        types = GoodsType.objects.all()
        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取购物车数量
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
            # 添加浏览记录
            history_key = 'history_%d' % user.id
            # 删除原有记录
            conn.lrem(history_key, 0, goods_id)
            # 添加浏览记录
            conn.lpush(history_key, goods_id)
            # 只留5个
            conn.ltrim(history_key, 0, 4)
        context = {'sku': sku, 'types': types,
                   'new_skus': new_skus,
                   'cart_count': cart_count}
        return render(request, 'detail.html', context)


class ListView(View):
    """列表页面"""
    def get(self, request, type_id, page):
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist as e:
            return redirect(reverse('goods:index'))
        # 判断排列方式
        types = GoodsType.objects.all()
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('-price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('id')

        new_skus = GoodsSKU.objects.filter(type=type).order_by('create_time')[:2]

        user = request.user
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        paginator = Paginator(skus, 2)
        # 获取第page页的内容
        try:
            page = int(page)
        except Exception:
            page = 1

        if page > paginator.num_pages:
            page = 1

        skus_page = paginator.page(page)
        # 小于5页只显示全部
        # 如果当前是前三页，显示1-5
        # 如果当前页是后三页，显示最后5页
        # 其他情况，显示当前页的前两也和后两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        else:
            pages = range(page-2, page+3)
        context = {'type': type, 'types': types,
                   'skus_page': skus_page,
                   'cart_count': cart_count,
                   'new_skus': new_skus,
                   'pages': pages,
                   'sort': sort}

        return render(request, 'list.html', context)



