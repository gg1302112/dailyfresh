from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.generic import View
from django.core.urlresolvers import reverse
from django_redis import get_redis_connection
from goods.views import GoodsSKU
from user.views import Address
from order.models import OrderInfo, OrderGoods
from Mixin.login_require import LoginRequireMixin
from datetime import datetime
from django.db import transaction
# Create your views here.


class OrderPlaceView(LoginRequireMixin, View):
    """提交订单"""
    def post(self, request):
        # 验证用户信息
        user = request.user
        # 获取post提交过来的ajax信息
        sku_ids = request.POST.getlist('sku_ids')
        if not sku_ids:
            return redirect(reverse('cart:show'))

        # 校验参数
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        skus = []
        total_amount = 0
        total_count = 0
        for sku_id in sku_ids:
            # 获取商品
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist as e:
                return redirect(reverse('cart:show'))

            count = conn.hget(cart_key, sku_id)
            amount = int(count)*sku.price
            total_amount += amount
            total_count += int(count)
            sku.count = count
            sku.amount = amount
            skus.append(sku)

        # 获取地址信息
        sku_ids = ','.join(sku_ids)
        addrs = Address.objects.filter(user_id=user.id)
        tran_costs = 10
        true_pay = tran_costs + total_amount

        context = {'skus': skus,
                   'addrs': addrs,
                   'total_amount': total_amount,
                   'total_count': total_count,
                   'true_pay': true_pay,
                   'tran_costs': tran_costs,
                   'sku_ids': sku_ids}

        return render(request, 'place_order.html', context)


# 地址的addr_id， 支付的方法pay_method， 商品的sku_ids （字符串格式）
class OrderCommitView(View):
    """订单提交"""
    @transaction.atomic
    def post(self, request):
        # 判断是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请登录'})

        # 获取post提交的ajax信息
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        # 验证数据的完整性
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不全'})
        # 验证地址是否存在
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist as e:
            return JsonResponse({'res': 2, 'errmsg': '地址不存在'})
        # 验证支付方式
        if pay_method not in OrderInfo.PAY_METHOD_VERIFY.keys():
            return JsonResponse({'res': 3, 'errmsg': '支付方式不正确'})

        # 验证商品
        sku_ids = sku_ids.split(',')
        print(sku_ids)
        # 将信息存入mysql
        # todo 获取要存入的信息 order_id，total_count， total_price，transit_price
        # 获取订单id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
        print(order_id)
        total_count = 0
        total_price = 0
        transit_price = 10
        # 插入一个订单
        save_id = transaction.savepoint()
        try:
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)
            # 将每一个商品信息插入OrderGoods中
            # todo 获取order， sku，count，price
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            for sku_id in sku_ids:
                sku_id = int(sku_id)
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist as e:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
                count = conn.hget(cart_key, sku_id)
                count = int(count)
                if count > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '库存不足'})
                price = sku.price*count
                sku.stock -= count
                sku.sales += count
                sku.save()
                total_count += count
                total_price += price
                OrderGoods.objects.create(order=order,
                                          sku=sku,
                                          count=count,
                                          price=price)
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '订单提交失败'})

        conn.hdel(cart_key, *sku_ids)

        return JsonResponse({'res': 5, 'msg': '提交成功'})
