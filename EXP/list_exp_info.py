#encoding: utf8
import sys,os
import importlib
import re, json

print 'name,author,cve,date,attack_type,app_type,app_name,min_version,max_version,version_list,description,reference'

def arrOrstr(p):
    if type(p) is list:
        return ','.join(p)
    else:
        return p

dir = sys.path[0]
for filename in os.listdir(dir):
    classname = filename.split('.')[0]
    if classname in ['list_exp_info', 'exp_template']:
        continue
    file = dir +'/'+ filename
    if os.path.isfile(file) and filename.split('.')[-1] == 'py':
        text = open(file).read()
        m = re.search(r'meta_info.*?return.*?\{(.*?)\}', text, re.S|re.M|re.I)
        if m:
            x = eval('{%s}' % m.group(1))
        #imp_module = __import__(classname)
        #imp_module = importlib.import_module(classname)
        #imp_class = getattr(imp_module, classname)
        #obj = imp_class('')
        #x = obj.meta_info()
            info = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (x['name'], x['author'], x['cve'], x['date'], x['attack_type'], x['app_type'], arrOrstr(x['app_name']), x['min_version'], x['max_version'], x['version_list'], x['description'], x['reference'])
            print info.decode('utf8').encode('gbk')
oj = json.loads(open('other_exps/config.txt').read())
for item in oj:
    x = oj[item]
    info = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (x['name'], x['author'], x['cve'], x['date'], x['attack_type'], x['app_type'], arrOrstr(x['app_name']), x['min_version'], x['max_version'], x['version_list'], x['description'], x['reference'])
    print info.encode('gbk')