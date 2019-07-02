"""
去哪的验证码爬虫
"""
import requests

import time

url = "https://user.qunar.com/captcha/api/image?k={en7mni(z&p=ucenter_login&c=ef7d278eca6d25aa6aec7272d57f0a9a&t=1554864025127"
headers = {
    'accept': "image/webp,image/apng,image/*,*/*;q=0.8",
    'accept-encoding': "gzip, deflate, br",
    'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
    'cache-control': "no-cache,no-cache",
    'cookie': "QN1=O5cv8VytSnFvFDK4SURjAg==; _i=VInJOm2w6XYCQJ3qZfwH6jhC5Efq; _vi=Rx8ytZBW7puq8LJnQuoOWHFHBStbTH7SXN0Khn741vOJM6PqoGHEY9wEvNyaTO5JmBYOTbqssh06DPtqR7Hrbqt7V0nBDFWGZjGi0Fxwu9MQziTr1M62aaFi2StD28-tM4eqNmVs_JtyQ0fwYkPDaHR5-noumhObkWSE7sM-5E3J; QN25=82bf9137-39c1-4c15-827a-c41ddd6a5fc2-9f992f90",
    'pragma': "no-cache",
    'referer': "https://user.qunar.com/passport/login.jsp?ret=https%3A%2F%2Fwww.qunar.com%2F",
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"
}

path = r'D:/swmdata/traindata/train_original_data/'
suffix = '.png'
num = 5001
while num > 0:
    response = requests.request("GET", url, headers=headers)
    filename = path + str(time.time()).replace('.', '')+suffix
    with open(filename, "wb") as fp:
        fp.write(response.content)
    print(num)
    num -= 1