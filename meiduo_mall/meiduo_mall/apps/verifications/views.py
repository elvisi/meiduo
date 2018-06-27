import random

from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from rest_framework.generics import GenericAPIView

from meiduo_mall.libs.yuntongxun.sms import CCP
from verifications import constants, serializers
from celery_tasks.sms.tasks import send_sms_code


from meiduo_mall.libs.captcha.captcha import captcha


class ImageCodeView(APIView):
    """验证码视图类"""
    def get(self, request, image_code_id):
        # 1.生成验证码
        text, image = captcha.generate_captcha()
        # 2.把验证码文本信息保存到Redis;获取Redis的操作对象
        redis_conn = get_redis_connection("verify_codes")
        # 把验证码保存到rides中
        # setex('变量名'，'有效期[秒]'，'值'）
        redis_conn.setex('img_%s'% image_code_id,constants.IMAGE_CODE_REDIS_EXPIRES, text)
        # 3.返回验证码
        return HttpResponse(image,content_type='images/jpg')


class SMSCodeView(GenericAPIView):
    """短信验证码视图类"""
    # 给当前视图类指定序列化器
    serializer_class = serializers.ImageCodeCheckSerializer
    def get(self, request,mobile):
        """创建短信验证码"""
    # 1.调用序列化器检查图片验证码
    # 2.检查是否在60s内有发送记录
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
    # 3.生成短信验证码
        sms_code = '%06d'% random.randint(0, 999999)
    # 4.保存短信验证码与发送记录
        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()  # 获取redis的管道对象，redis能使用的操作，管道对象都可以使用
        # setex("变量名","有效期[秒]","值")
        pl.multi()
        pl.setex('sms_%s'% mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)
        # redis中维护一个 send_flag_<mobile>，60
        pl.setex('send_flag_%s'% mobile, constants.SEND_SMS_CODE_INTERVAL,1)
        pl.execute()  # 把上面所有的redis操作一并一次性执行
    # 5.发送短信
        sms_code_expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        # ccp = CCP()
        # time = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        # ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_TEMP_ID)

    # 调用celery执行异步任务发送短信
        # delay后面需要添加异步任务函数中的参数，而且要安装顺序一一填写
        send_sms_code.delay(mobile,sms_code)

    # 6. 返回响应结果
        return Response({'message':'OK'},status.HTTP_200_OK)


class SMSCodeByTokenView(GenericAPIView):
    serializer_class = serializers.CheckSMSCodeTokenSerializer
    """凭借access_token发送短信验证码"""
    def get(self, request):
    # 调用校验发送短信的 access_token和手机号码
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 提取序列化器中的属性 手机号码
        mobile = serializer.mobile

        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        # 4.保存短信验证码与发送记录
        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()  # 获取redis的管道对象，redis能使用的操作，管道对象都可以使用
        # setex("变量名","有效期[秒]","值")
        pl.multi()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis中维护一个 send_flag_<mobile>，60
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()  # 把上面所有的redis操作一并一次性执行
        # 发送短信
        sms_code_expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        # 调用celery执行异步任务发送短信
        # delay后面需要添加异步任务函数中的参数，而且要安装顺序一一填写
        send_sms_code.delay(mobile, sms_code)

        # 6. 返回响应结果
        return Response({'message': 'OK'}, status.HTTP_200_OK)












