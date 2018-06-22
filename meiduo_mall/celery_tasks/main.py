from celery import Celery

# 创建Celery应用对象
app = Celery('meiduo')
# 加载Celery配置
app.config_from_object('celery_tasks.config')

# 注册异步任务到Celery   # 自动会查找到任务包里面的tasks模块
app.autodiscover_tasks(['celery_tasks.sms'])

# 最终在终端里面运行Celery
# celery -A 主程序的包路径 worker -l info
# 一般从后端的项目根目录下，执行上面的命令
# celery -A celery_tasks.main worker -l info