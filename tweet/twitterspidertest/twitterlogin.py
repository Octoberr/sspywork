"""
根据twitter返回的数据模拟twitter登陆
"""
import requests
from bs4 import BeautifulSoup
import execjs

sa = requests.session()
home_page_url = 'https://twitter.com/'
home_res = sa.get(home_page_url)
# home_headers = home_res.headers
# print(home_headers)
login_page_url = 'https://twitter.com/login'
login_res = sa.get(login_page_url)
res_text = login_res.text
#
soup = BeautifulSoup(res_text, 'lxml')
authenticity = soup.find('input', attrs={'name': 'authenticity_token'})
a_value = authenticity.attrs.get('value')
# ui_div = soup.find('div', attrs={'class':'LoginForm-rememberForgot'})
# ui_metric = ui_div.find('input', attrs={'name':'ui_metrics'})
# 先不用ui这个参数试试
# js1_url = 'https://twitter.com/i/js_inst?c_name=ui_metrics'
# js1_res = sa.get(js1_url)
# js1_res = js1_res.text
# print(js1_res)
# js2_url = 'https://twitter.com/i/js_inst?c_name=ui_metrics'
# js2_res = sa.get(js2_url)
# js2_res = js2_res.text
# print(js2_res)
posturl = 'https://twitter.com/sessions'
querystring = {"session[username_or_email]":"%20sepjudy@gmail.com","session[password]":"%20ADSZadsz123","authenticity_token":"%2058cecfc29933eaf1f4b359786a2631a9ebea8097"}
login_res = sa.get(posturl, params=querystring)
cookiestring = login_res.cookies.get_dict()
newcookiestr = ';'.join([str(x) + '=' + str(y) for x, y in cookiestring.items()])
print(newcookiestr)

