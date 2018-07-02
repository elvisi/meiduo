from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'area', views.AreaViewSet, base_name='area')

urlpatterns = []

urlpatterns += router.urls