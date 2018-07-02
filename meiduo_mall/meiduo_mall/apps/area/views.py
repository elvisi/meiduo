from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from area.models import Area
from area.serializers import AreaSerializer, SubAreaSerializer


class AreaViewSet(CacheResponseMixin,ReadOnlyModelViewSet):
    """行政区划视图集"""
    pagination_class = None  # 区划信息不分页

    # 重写当前视图获取序列化类的方法，根据动作实例化不同的序列化对象
    def get_serializer_class(self, *args, **kwargs):
        # 判断当前的请求动作
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubAreaSerializer

    def get_queryset(self):
        """提供数据集"""
        # 根据不同的动作，把顶级的行政区域分离出来进行查询
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()
