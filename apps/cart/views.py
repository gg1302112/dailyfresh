from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from Mixin.login_require import LoginRequireMixin

# Create your views here.


class AddView(View):
    """添加购物车记录"""
    def post(self, request):
        count = request.POST.get('count')
        print(count)
        sku_id = request.POST.get('sku_id')
        print(sku_id)
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        if not all([count, sku_id]):
            return JsonResponse({'res': 1, 'errmsg': '数据不全'})

        try:
            count = int(count)
            print(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数量出错'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
            print(sku)
        except Exception as e:
            return JsonResponse({'res': 3, 'errmsg': '此商品不存在'})

        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '库存数量不足'})

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        print(cart_key)
        y_count = conn.hget(cart_key, sku_id)
        if y_count:
            count += int(y_count)
        conn.hset(cart_key, sku_id, count)
        cart_count = conn.hlen(cart_key)
        print(cart_count)
        return JsonResponse({'res': 5, 'cart_count': cart_count, 'msg': '添加成功'})


class CartInfoView(LoginRequireMixin, View):
    """获取购物车"""
    def get(self, request):
        """获取购物车页面"""
        # 获取用户
        user = request.user

        # 获取redis的连接
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_dict = conn.hgetall(cart_key)
        total_count = 0
        total_amount = 0
        skus = []
        for sku_id, count in cart_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            amount = sku.price*int(count)
            sku.count = count
            sku.amount = amount
            total_count += int(count)
            total_amount += amount
            skus.append(sku)
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
        }

        return render(request, 'cart.html', context)


class CartUpdateView(View):
    """更新购物车"""
    def post(self, request):
        count = request.POST.get('count')
        sku_id = request.POST.get('sku_id')

        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        if not all([count, sku_id]):
            return JsonResponse({'res': 1, 'errsmg': '数据不全'})

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errsmg': '商品数量出错'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '库存不足'})

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        conn.hset(cart_key, sku_id, count)
        values = conn.hvals(cart_key)
        total = 0
        for value in values:
            total += int(value)
        return JsonResponse({'res': 5, 'total': total, 'msg': '更新成功'})


class CartDeleteView(View):
    """删除sku信息"""
    def post(self, request):
        sku_id = request.POST.get('sku_id')
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录用户'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist as e:
            return JsonResponse({'res': 1, 'errmsg': '商品不存在'})

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        conn.hdel(cart_key, sku_id)

        total = 0
        values = conn.hvals(cart_key)
        for value in values:
            total += int(value)

        return JsonResponse({'res': 2, 'total': total, 'msg': '删除成功'})