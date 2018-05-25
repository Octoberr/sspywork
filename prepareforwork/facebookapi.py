"""
使用facebook的API尝试获取数据
create by swm 2018/05/23
安装facebook api
add by swm 2018/05/25
pip install -e git+https://github.com/mobolic/facebook-sdk.git#egg=facebook-sdk
"""

import facebook

# 有效期持续到2018/07/23
accesstoken = 'EAAdNwl57kx8BAMTXi5TSmxds1Xm98PjZCdZCmpvz0iPBYjrS4MfZBlI1mZAU1Bu2FZCx0je5ZBPuVJNlkhY4XwoQPPwQWBtN6U0noCEfvS5FxLKrAJ6FioeSZC6fiOjgLKPXRZAonZAtnzjF6gFAQdj1bivYfdiZB4ioazqY8ffZCnZCIQZDZD'
apptoken = '366182893787676|h-TF55O56GGICvQN4uFJqRK0i0s'

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
    "cookie":"sb=oHADW-ZcKeEjonBqTB8aej77; datr=oHADW5gHZ9Z03CBY-QhlJXq5; locale=zh_CN; c_user=100026301698530; xs=11%3AMlHEwT9fLhrHrQ%3A2%3A1526952876%3A-1%3A-1; pl=n; ; fr=0ZI8S8W5dSa7utuLH.AWXzJTM5QlSvb195FCkjALtPzzA.Ba77es.qj.AAA.0.0.BbBQ4D.AWW4O79X; act=1527058935570%2F86; presence=EDvF3EtimeF1527058937EuserFA21B26301698530A2EstateFDt3F_5bDiFA2user_3a1B26063503367A2ErF1EoF4EfF10CAcDiFA2user_3a1B26B242731A2ErF1EoF6EfF9C_5dEutc3F1527058431371G527058937646CEchFDp_5f1B26301698530F137CC; wd=594x769"
}

# html = requests.get(url, headers=headers)
# html.encoding = 'utf-8'
# # print(html.text)
# Soup = BeautifulSoup(html.text, 'lxml')
# div1 = Soup.find('div', id='globalContainer', class_='uiContextualLayerParent')
# div2 = div1.find('div', id='content_container')
# div3 = div2.find('div', class_='clearfix')
# div4 = div3.find('div', id='pagelet_timeline_main_column')
# div5 = div4.find('div', id='id_5b051898802182940386045')
# print(div5)
graph = facebook.GraphAPI(access_token=accesstoken, version='3.0')
post = graph.get_object('583390655086575')
print(post)