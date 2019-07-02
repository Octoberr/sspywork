# import redis
#
# r = redis.Redis(host='127.0.0.1', port=8888, db=0)
# r.set('name', 'swm')
# print(r.get('name'))
import requests

a = requests.get("http://127.0.0.1:5010/get/")
print(a.text)