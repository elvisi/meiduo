from collections import OrderedDict
from django.conf import settings
from django.template import loader
from goods.utils import get_categories
import os
import time

from goods.models import GoodsChannel
from .models import ContentCategory


def generate_static_index_html():
    """
    生成静态的主页html文件
    """
    print('%s: generate_static_index_html' % time.ctime())
    # 商品频道及分类菜单

    categories = get_categories()


    # 广告内容
    contents = {}
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True)

    # 渲染模板
    context = {
        'categories': categories,
        'contents': contents
    }
    template = loader.get_template('index.html')
    html_text = template.render(context)
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')
    html_text_data = html_text.encode('utf-8')
    with open(file_path, 'wb') as f:
        f.write(html_text_data)