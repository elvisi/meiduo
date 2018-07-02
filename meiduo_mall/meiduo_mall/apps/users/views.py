from django.shortcuts import render

# Create your views here.
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, GenericAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

import re

from users import constants
from users.models import User
from .utils import get_user_by_account
from verifications.serializers import ImageCodeCheckSerializer

from . import serializers


class UsernameCountView(APIView):
    """用户数量"""

    def get(self, request, username):
        """获取指定用户名数量"""
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }

        return Response(data)


class MobileCountView(APIView):
    """手机号数量"""

    def get(self, request, mobile):
        """获取指定手机号数量"""
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)


class UserView(CreateAPIView):
    """用户注册"""
    serializer_class = serializers.CreateUserSerializer


class SMSCodeTokenView(GenericAPIView):
    """根据用户账号名和验证码来获取发送短信的访问令牌"""
    serializer_class = ImageCodeCheckSerializer

    def get(self, request, account):
        # 1.校验图形验证码
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # 2.根据用户信息(手机号/用户名)来查询用户
        user = get_user_by_account(account)
        if user is None:
            return Response({"message": "用户不存在"}, status=status.HTTP_404_NOT_FOUND)
        # 3.生成一个access_token
        access_token = user.generate_sms_code_token()
        # 4.处理手机号码
        mobile = re.sub(r"(\d{3})\d{4}(\d{4})", r"\1****\2", user.mobile)
        # 5.返回响应信息
        return Response({
            'mobile': mobile,
            'access_token': access_token,
        })


class PasswordTokenView(GenericAPIView):
    """凭借短信验证码获取重置密码的access_token"""
    serializer_class = serializers.CheckSMSCodeSerializer

    def get(self, request, account):
        # 调用序列化器（根据当前用户的账号名，提取用户对象,校验短信验证码）
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # 生成access_token
        user = serializer.user
        access_token = user.generate_set_password_token()
        # 响应，返回ccess_token和user_id
        return Response({
            'user_id': user.id,
            'access_token': access_token,
        })


class PasswordView(UpdateAPIView):
    # 序列化器的作用
    # 1. 校验access_token
    # 2. 校验密码和确认密码是否一致
    # 3. 重置密码
    queryset = User.objects.all()
    serializer_class = serializers.ResetPasswordSerializer

    def post(self, request, pk):
        """
        凭借access_token进行密码重置
        :param pk: user_id
        :return: user
        """
        return self.update(request, pk)


# RetrieveAPIView 继承了 GenericAPIView、RetrieveModelMixin，
# 所以我们可以利用完成指定序列化，并且获取用户详情信息
# RetrieveAPIView 默认使用的使用需要地址中附带 pk
class UserDetailView(RetrieveAPIView):
    """用户详情"""
    serializer_class = serializers.UserDetailSerializer
    # 设置当前视图的登陆权限，只能是登陆后的用户才能访问
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    """发送激活邮件的视图类"""
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.EmailSerializer

    def get_object(self):
        return self.request.user


class VerifyEmailView(APIView):
    """判断激活邮件的token是否有效"""

    def get(self, request):
        # 获取token
        token = request.query_params.get('token')
        # 校验token
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message': '无效的token'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.email_active = True
            user.save()

            return Response({'message': 'OK'})


class AddressViewSet(ModelViewSet):
    """用户地址新增与修改"""
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def list(self, request, *args, **kwargs):
        """用户地址列表数据"""
        queryset = self.get_queryset()
        serializer = serializers.UserAddressSerializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        """保存用户地址数据"""
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """处理删除"""
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """设置默认地址"""
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """修改标题"""
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
