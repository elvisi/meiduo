from django.db import models
from meiduo_mall.utils.models import BaseModel
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSerializer
from django.conf import settings  # 导入当前系统配置
from itsdangerous import BadData

# Create your models here.
from oauth import constants


class OAuthQQUser(BaseModel):
    user = models.ForeignKey('users.User',on_delete=models.CASCADE,verbose_name='用户')
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ用户登陆信息'
        verbose_name_plural = 'verbose_name'

    @staticmethod
    def generate_save_qq_token(openid):
        """用于保存qq和美多账号的绑定的access_token"""
        # 创建临时令牌的对象
        # serializer = Serializer(秘钥, 有效期秒)
        serializer = TJWSerializer(settings.SECRET_KEY, constants.SAVE_QQ_TOKEN_EXPRIES)
        # serializer.dumps(数据), 返回bytes类型
        token = serializer.dumps({'openid': openid})
        # 生成的token令牌是一个bytes类型的，要进行处理
        token = token.decode()
        return token

    @staticmethod
    def check_save_qq_token(access_token):
        """检查qq和美多账号的绑定的access_token"""
        # serializer = Serializer(秘钥, 有效期秒)
        serializer = TJWSerializer(settings.SECRET_KEY, constants.SAVE_QQ_TOKEN_EXPRIES)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            return data.get('openid')