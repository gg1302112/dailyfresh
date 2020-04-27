from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout
from .models import User, Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from django.http import HttpResponse
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from dailyfresh import settings
from celery_tasks.tasks import send_register_active_email
from Mixin.login_require import LoginRequireMixin
from django_redis import get_redis_connection
from django.core.mail import send_mail
import re
# Create your views here.


# def register(request):
#     """注册页"""
#     if request.method == 'GET':
#         return render(request, 'register.html')
#     else:
#         # 接受数据
#         username = request.POST.get('user_name')
#         password = request.POST.get('pwd')
#         email = request.POST.get('email')
#         allow = request.POST.get('allow')
#         cpassword = request.POST.get('cpwd')
#         # 数据校验
#         if not all([username, password, email]):
#             # 数据不完整
#             return render(request, 'register.html', {'errmsg': '数据不完整'})
#         # 判断密码输入是否相同
#         if password != cpassword:
#             return render(request, 'register.html', {'errmsg': '两次密码不相同'})
#         # 判断邮箱格式
#         if not re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#             return render(request, 'register.html', {'errmsg': '邮箱格式错误'})
#         # 判断是否勾选协议
#         if allow != 'on':
#             return render(request, 'register.html', {'errmsg': '还未勾选协议'})
#         # 进行业务处理，进行用户注册
#         try:
#             User.objects.get(username='%s' % username)
#             return render(request, 'register.html', {'errmsg': '用户名重复'})
#         except Exception:
#             user = User.objects.create_user(username, email, password)
#             user.is_active = 0
#             user.save()
#             url = reverse('goods:index')
#         return redirect(url)


class Register(View):
    """注册类"""

    def get(self, request):
        """返回注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        # 接受数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        cpassword = request.POST.get('cpwd')
        # 数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 判断密码输入是否相同
        if password != cpassword:
            return render(request, 'register.html', {'errmsg': '两次密码不相同'})
        # 判断邮箱格式
        if not re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式错误'})
        # 判断是否勾选协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '还未勾选协议'})
        # 进行业务处理，进行用户注册
        try:
            User.objects.get(username='%s' % username)
            return render(request, 'register.html', {'errmsg': '用户名重复'})
        except Exception:
            user = User.objects.create_user(username, email, password)
            user.is_active = 0
            user.save()

        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()
        # 发送邮件
        # subject = '你好天天生鲜'
        # message = ''
        # sender = settings.EMAIL_HOST_USER
        # reciver = [email]
        # html_message = "<h1>天天生鲜<hi><br>%s欢迎来到天天生鲜，点击下面连接即可激活用户<a href='http://127.0.0.1:8000/user/active/%s'>http://127.0.0.1:8000/user/active/%s<a/>" % (username, token, token)
        # send_mail(subject, message, sender, reciver, html_message=html_message)
        send_register_active_email.delay(email, username, token)
        url = reverse('goods:index')
        return redirect(url)


class ActiveView(View):
    """激活使用"""
    def get(self, request, token):
        # 获取加密Serializer实例
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            # 加载访问token
            info = serializer.loads(token)
            user_id = info['confirm']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链路已过期
            return HttpResponse('链路激活已过期')



class LoginView(View):
    """登录"""
    def get(self, request):
        """登录页面"""
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """登录验证"""
        # 获取post提交的数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')
        # 验证数据跳转

        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        # 认证用户
        user = authenticate(username=username, password=password)
        if user is not None:
            # the password verified for the user
            if user.is_active:
                # 保存session
                login(request, user)
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                return response
            else:
                # 还未认证
                return render(request, 'login.html', {'errmsg': '还未认证请去认证'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


class LogoutView(View):
    """登出视图"""
    def get(self, request):
        """登出页面"""
        logout(request)
        return redirect(reverse('goods:index'))


class UserinfoView(LoginRequireMixin, View):
    """用户信息视图"""
    def get(self, request):
        """个人信息页面"""
        # print(request.user.is_authenticated())
        user = request.user
        address = Address.objects.get_default_address(user)
        con = get_redis_connection('default')
        history_key = 'history_%d' % user.id
        goods_id = con.lrange(history_key, 0, 4)
        goods_li = []
        for good_id in goods_id:
            good = GoodsSKU.objects.get(id=good_id)
            if int(good_id) == good.id:
                goods_li.append(good)
        context = {'page': 'info',
                   'address': address,
                   'goods_li': goods_li}

        return render(request, 'user_center_info.html', context)


class UserorderView(LoginRequireMixin, View):
    """订单信息视图"""
    def get(self, request, page):
        """订单信息页面"""
        user = request.user
        orders = OrderInfo.objects.get(user=user)

        return render(request, 'user_center_order.html', {'page': 'order'})


class AddressView(LoginRequireMixin, View):
    """地址视图"""
    def get(self, request):
        """收获地址页面"""
        # 获取地址信息
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=1)
        # except Address.DoesNotExist:
        #     address = ""
        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        """创建地址信息"""
        # 接收表单提交的信息
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        user = request.user
        # 判断表单信息
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '信息不完整请补全信息'})
        if not re.match('^1(3|5|7|8)[0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '电话号码不正确'})
        # try:
        #     address = Address.objects.get(user=user, is_default=1)
        # except Address.DoesNotExist:
        #     address = ""

        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default
                               )
        return redirect(reverse('user:address'))