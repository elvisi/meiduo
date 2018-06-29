import json
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen

from django.conf import settings

from oauth.exceptions import QQAPIError


class OAuthQQ():
    """
    QQ第三方登陆工具类
    这里保存的是QQ第三方登陆需要使用操作的方法和数据
    """

    def __init__(self):
        self.app_id = settings.QQ_APP_ID
        self.app_key = settings.QQ_APP_KEY
        self.redirect_uri = settings.QQ_REDIRECT_URI

    def generate_qq_login_url(self, state):
        """
        生成QQ登陆的url地址
        :param state: QQ登陆成功后跳转的地址
        :return: QQ登陆地址
        """
        base_url = 'https://graph.qq.com/oauth2.0/authorize' + '?'
        query_params = {
            "response_type": "code",  # 固定值
            "client_id": self.app_id,  # app id
            "redirect_uri": self.redirect_uri,
            "state": state,  # 登陆页面中的跳转地址
            "scope": "get_user_info",  # 声明使用的接口名称，可选
        }
        # 把字典转换成查询字符串
        query_string = urlencode(query_params)
        url = base_url + query_string
        print(query_params)
        return url

    def get_qq_access_token(self, code):
        """凭借code发起请求到QQ服务器获取access_token"""
        # 拼接接口地址和参数
        base_url = 'https://graph.qq.com/oauth2.0/token' + '?'
        query_params = {
            'grant_type':'authorization_code',
            'client_id': self.app_id,
            'client_secret': self.app_key,
            'code': code,
            'redirect_uri': self.redirect_url
        }
        # 把字典转换成查询字符串
        query_string = urlencode(query_params)
        url = base_url + query_string
        # 发起请求
        response = urlopen(url)
        response_data = response.read().decode()
        data = parse_qs(response_data)
        access_token = data.get('access_token')
        if not access_token:
            raise QQAPIError
        # 返回access_token
        return access_token[0]

    def get_qq_openid(self, access_token):
        """凭借access_token发起请求到QQ服务器获取openid"""
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token
        # 发起请求
        response = urlopen(url)
        response_data = response.read().decode()
        # 'callback( {"client_id":"101480417","openid":"78F9651BA2F74316175B9BBA5A6A240A"} );\n'
        try:
            data = json.loads(response_data[10:-4])
        except:
            raise QQAPIError
        else:
            return data['openid']















