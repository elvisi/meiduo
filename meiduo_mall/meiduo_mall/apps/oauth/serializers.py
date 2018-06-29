from django_redis import get_redis_connection
from rest_framework import serializers

from oauth.models import OAuthQQUser
from users.models import User


class OAuthQQUserSerializer(serializers.Serializer):
    """QQ登陆用户的序列化器"""
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, data):
        # 检验access_token 并取出openID
        access_token = data['access_token']
        openid = OAuthQQUser.check_save_qq_token(access_token)
        if not openid:
            raise serializers.ValidationError('无效的access_token')

        # 这里的数据保存到create方法中
        data['openid'] = openid

        # 检验短信验证码
        mobile = data['mobile']
        sms_code = data['sms_code']
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('短信验证码错误')

        # 如果用户存在，检查用户密码
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
            password = data['password']
            if not user.check_password(password):
                raise serializers.ValidationError('密码错误')
            # 保存user,提供给create方法中使用
            data['user'] = user
        return data  # 这里的data,作为create()的第二个参数validated_data

    def create(self, validated_data):
        user = validated_data.get('user')
        if not user:
            # 手机号不存在，表示以前没有美多账号，创建美多账号(username默认是手机号)
            user = User.objects.create_user(
                username=validated_data['mobile'],
                password=validated_data['password'],
                mobile=validated_data['mobile'],
            )
        openid = validated_data.get('openid')
        # 手机号存在，则直接进行openid和user绑定，往OAuthQQUser模型添加记录
        OAuthQQUser.objects.create(
            openid=openid,
            user=user
        )
        return user
