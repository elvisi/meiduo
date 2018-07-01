from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSerializer
from django.conf import settings  # 导入当前系统配置
from itsdangerous import BadData

from users import constants


class User(AbstractUser):
    """用户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    email_active = models.BooleanField(default=False,verbose_name='邮箱的激活状态')

    class Meta:
        db_table = "tb_users"
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name

    def generate_sms_code_token(self):
        """使用itsdangerous生成发送验证码响应的assecc_token"""

        # 创建临时令牌的对象
        # serializer = Serializer(秘钥, 有效期秒)
        serializer = TJWSerializer(settings.SECRET_KEY, 300)
        # serializer.dumps(数据), 返回bytes类型
        token = serializer.dumps({'mobile': self.mobile})
        # 生成的token令牌是一个bytes类型的，要进行处理
        token = token.decode()
        return token


    @staticmethod
    def check_sms_code_token( access_token):
        """校验发送短信的access_token"""
        # serializer = Serializer(秘钥, 有效期秒)
        serializer = TJWSerializer(settings.SECRET_KEY, 300)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            return data.get('mobile')

    def generate_set_password_token(self):
        """使用itsdangerous生成重置密码需要的access_token"""

        # 创建临时令牌的对象
        # serializer = Serializer(秘钥, 有效期秒)
        serializer = TJWSerializer(settings.SECRET_KEY, 300)
        # serializer.dumps(数据), 返回bytes类型
        token = serializer.dumps({'user_id': self.id})
        # 生成的token令牌是一个bytes类型的，要进行处理
        token = token.decode()
        return token

    @staticmethod
    def check_set_password_token( access_token):
        """校验发送短信的access_token"""
        # serializer = Serializer(秘钥, 有效期秒)
        serializer = TJWSerializer(settings.SECRET_KEY, 300)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            return data.get('user_id')

    def generate_verify_email_token(self):
        """使用itsdangerous生成验证邮箱的access_token"""

        # 创建临时令牌的对象
        # serializer = Serializer(秘钥, 有效期秒)
        serializer = TJWSerializer(settings.SECRET_KEY, constants.VERIFY_EMAIL_TOKEN_EXPIRES)
        # serializer.dumps(数据), 返回bytes类型
        token = serializer.dumps({'user_id': self.id, 'email':self.email})
        # 生成的token令牌是一个bytes类型的，要进行处理
        token = token.decode()
        return token

    @staticmethod
    def check_verify_email_token(access_token):
        """校验激活邮件的access_token"""
        # serializer = Serializer(秘钥, 有效期秒)
        serializer = TJWSerializer(settings.SECRET_KEY, constants.VERIFY_EMAIL_TOKEN_EXPIRES)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            # 获取用户
            email = data.get('email')
            user_id = data.get('user_id')
            try:
                user = User.objects.get(id=user_id,email=email)
            except User.DoesNotExist:
                return None

            return user
