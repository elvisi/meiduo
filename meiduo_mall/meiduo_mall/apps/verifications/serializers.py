from django_redis import get_redis_connection
from redis import RedisError
from rest_framework import serializers
from users.models import User

import logging
# 获取配置文件中定义的logger,用来记录日志
logger = logging.getLogger('django')


class ImageCodeCheckSerializer(serializers.Serializer):
    # 校验图形验证码的序列化器
    # 声明验证的规则
    image_code_id = serializers.UUIDField()
    # UUIDField专门用于校验UUID格式类型的字符串
    image_code = serializers.CharField(min_length=4,max_length=4)

    def validate(self, attrs):
        """校验"""
        image_code = attrs['image_code']
        image_code_id = attrs['image_code_id']
        # 从Redis中获取真实图片验证码
        redis_conn = get_redis_connection('verify_codes')
        real_image_code_text = redis_conn.get('img_%s'% image_code_id)
        # 如果根据当前的image_code_id获取不到值
        if not real_image_code_text:
            raise serializers.ValidationError('图片验证码无效')
        # 图形验证码只能使用一次，所以需要删除图片验证码
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            # 如果出现Redis异常，记录日志
            logger.error(e)

        # 比较图片验证码
        real_image_code_text = real_image_code_text.decode()
        if real_image_code_text.lower() != image_code.lower():
            raise serializers.ValidationError('图片验证码错误')

        # 判断是否在60s内发送过短信
        mobile = self.context['view'].kwargs.get('mobile')
        if mobile:
            send_flag = redis_conn.get('send_flag_%s' % mobile)
            # 如果Redis中有这个数据，则表示在60秒内发送过短信
            if send_flag:
                raise serializers.ValidationError('请求次数过于频繁')
        return attrs


class CheckSMSCodeTokenSerializer(serializers.Serializer):
    access_token = serializers.CharField(label='发送短信的临时令牌access_token',required=True)
    def validate(self, attrs):
        access_token = attrs['access_token']
        # 校验access_token
        mobile = User.check_sms_code_token(access_token)
        if mobile is None:
            raise serializers.ValidationError('用户不存在')

        redis_conn = get_redis_connection('verify_codes')
        # 校验当前手机号是否在60秒内发送过短信
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 如果Redis中有这个数据，则表示在60秒内发送过短信
        if send_flag:
            raise serializers.ValidationError('请求次数过于频繁')

        # 把手机号码作为序列化器的属性，可以通过视图在序列化器提取出来
        self.mobile = mobile

        return attrs


