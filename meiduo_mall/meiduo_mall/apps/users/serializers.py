from rest_framework import serializers
import re
from django_redis import get_redis_connection

from .models import User
from rest_framework_jwt.settings import api_settings
from .utils import get_user_by_account


class CreateUserSerializer(serializers.ModelSerializer):
    """创建用户序列化器"""
    password2 = serializers.CharField(label='确认密码', required=True, allow_null=False, allow_blank=False, write_only=True)
    sms_code = serializers.CharField(label='短信验证码', required=True, allow_null=False, allow_blank=False, write_only=True)
    allow = serializers.CharField(label='同意协议', required=True, allow_null=False, allow_blank=False, write_only=True)
    token = serializers.CharField(label='token登录状态', read_only=True)

    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号码格式错误')
        return value

    def validate_allow(self, value):
        """检验用户是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, data):
        # 判断两次密码

        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断短信验证码
        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']

        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_data):
        """创建用户"""
        # 移除数据库模型类中不存在的属性
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        user = super().create(validated_data)

        # 调用Django的认证系统加密密码
        user.set_password(validated_data['password'])
        user.save()

        # 1.生成一个token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  #载荷的配置
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER   # 生成token的配置

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        # 2.把token作为user模型对象的属性返回给前端
        user.token = token

        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', 'token')
        extra_kwargs = {
            'id': {'read_only': True}, 'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的用户名',
                    'max_length': '仅允许8-20个字符的用户名',
                }
            }

        }

class CheckSMSCodeSerializer(serializers.Serializer):
    """校验短信验证码和账号名的序列化器"""
    sms_code = serializers.CharField(label='短信验证码', min_length=6, max_length=6)
    def validate(self, attrs):
        sms_code = attrs['sms_code']
        # 根据用户名获取用户模型对象
        account = self.context['view'].kwargs.get('account')
        user = get_user_by_account(account)
        if user is None:
            raise serializers.ValidationError("不存在的用户名")

        # 校验短信验证码
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % user.mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if sms_code != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        # 把当前对象作为序列化器的属性传递给视图中序列化对象
        self.user = user
        return attrs


class ResetPasswordSerializer(serializers.ModelSerializer):
    """重置密码序列化器"""

    # 定义字段
    password2 = serializers.CharField(label='确认密码', write_only=True)
    access_token = serializers.CharField(label='重置密码的access_token', write_only=True)

    def validate(self, attrs):
        """校验数据"""
        # 判断两次密码
        access_token = attrs['access_token']
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码输入不一致')
        # 校验重置密码的access_token是否有效
        allow = User.check_set_password_token(access_token)
        if not allow:
            raise serializers.ValidationError('无效的access——token')

        return attrs


    def update(self, instance, validated_data):
        """
        更新密码
        :param instance:  当前pk值对应的user模型对象
        :param validated_data:  校验完成以后的数据
        :return: user对象
        """
        # 调用Django用户模型类的设置密码的方法
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


    # 更新
    class Meta:
        model = User
        fields = ('id', 'password', 'password2', 'access_token')
        extra_kwargs = {
            'password':{
                'write_only':True,
                'min_length':8,
                'max_length':20,
                'error_messages':{
                    'min_length':'仅允许8-20个字符的密码',
                    'max_length':'仅允许8-20个字符的密码',
                }

            }
        }





class UserDetailSerializer(serializers.ModelSerializer):
    """用户详细信息序列化器"""
    class Meta:
        model = User
        # email_active 记录邮箱的验证状态
        fields = ('id', 'username', 'mobile', 'email', 'email_active')



