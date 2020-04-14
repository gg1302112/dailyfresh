from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from goods.models import GoodsSKU

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
        print(y_count)
        if y_count:
            count += int(y_count)
        conn.hset(cart_key, sku_id, count)
        cart_count = conn.hlen(cart_key)
        print(cart_count)
        return JsonResponse({'res': 5, 'cart_count': cart_count, 'msg': '添加成功'})
