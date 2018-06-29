from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from oauth.exceptions import QQAPIError
from oauth.models import OAuthQQUser
from oauth.utils import OAuthQQ
from oauth.serializers import OAuthQQUserSerializer


# Create your views here.


class OAuthQQView(APIView):
    def get(self, request):
        # 获取登陆页面中登陆成功以后的跳转地址
        next = request.query_params.get('state')
        if not next:
            next = '/'

        oauth_qq = OAuthQQ()
        # 组装QQ登陆url地址
        auth_url = oauth_qq.generate_qq_login_url(next)

        # 响应
        return Response({'auth_url': auth_url})


class OAuthQQUserView(GenericAPIView):
    """QQ登录用户的信息视图类"""
    serializer_class = OAuthQQUserSerializer

    def get(self, request):
        # 接收code
        code = request.query_params.get('code')
        if not code:
            return Response({'message': '缺失code'}, status=status.HTTP_400_BAD_REQUEST)

        oauth_qq = OAuthQQ()
        try:
            # 凭借code发起请求到QQ服务器获取access_token
            access_token = oauth_qq.get_qq_access_token(code)
            # 凭借access_token发起请求到QQ服务器获取openid
            openid = oauth_qq.get_qq_openid(access_token)

        except QQAPIError:
            return Response({'message': 'QQ服务异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        openid = oauth_qq.get_qq_openid(access_token)
        # 凭借openid到OAuthQQUser模型，判断是否是第一次使用QQ登录
        try:
            oauth_qq_user = OAuthQQUser.objects.get(openid=openid)
        except:
            # 第一次使用QQ登录,绑定qq和美多账号的关系
            # 因为绑定页面不能随便生成，所以提供一个itsdangerous 生成access_token
            token = OAuthQQUser.generate_save_qq_token(openid)
            return Response({'access_token':token})

        else:
            # 不是第一次使用QQ登录，返回登录的JWT token

            # 1.生成一个token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 载荷的配置
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 生成token的配置
            user = oauth_qq_user.user
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            return Response({
                'token': token,
                'username': user.username,
                'user_id': user.id,
            })


    def post(self, request):
        # post方法上传的数据，需要使用request.data 保存
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # 返回JWTtoken, username, user_id
        # 1.生成一个token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 载荷的配置
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 生成token的配置

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return Response({
            'token': token,
            'username': user.username,
            'user_id': user.id,
        })
