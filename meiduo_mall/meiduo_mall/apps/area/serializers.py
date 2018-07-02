from rest_framework import serializers

from area.models import Area


class AreaSerializer(serializers.ModelSerializer):
    """行政区划序列化器"""
    class Meta:
        model = Area
        fields = ('id','name')

class SubAreaSerializer(serializers.ModelSerializer):
    """子行政区划区域序列化器"""
    # 在模型声明字段时，设置related_name,可以帮我们解决多个模型之间外链关联时的重名情况
    subs = AreaSerializer(many=True, read_only=True)
    class Meta:
        model = Area
        fields = ('id','name','subs')