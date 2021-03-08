"""
https://luminati-china.biz/cp/howto
find by judy 20201027
国外代理，按流量计费，可用于google search， twitter, whois
国内代理使用国内代理池
"""

# test code by judy 20201027
# print('If you get error "ImportError: No module named \'six\'" install six:\n'+\
#     '$ sudo pip install six');
# print('To enable your free eval account and get CUSTOMER, YOURZONE and ' + \
#     'YOURPASS, please contact sales@luminati.io')
# import sys
# if sys.version_info[0]==2:
#     import six
#     from six.moves.urllib import request
#     opener = request.build_opener(
#         request.ProxyHandler(
#             {'http': 'http://lum-customer-hl_d08f7ef9-zone-static:cyg5pnh9hnlw@zproxy.lum-superproxy.io:22225',
#             'https': 'http://lum-customer-hl_d08f7ef9-zone-static:cyg5pnh9hnlw@zproxy.lum-superproxy.io:22225'}))
#     print(opener.open('http://lumtest.com/myip.json').read())
# if sys.version_info[0]==3:
#     import urllib.request
#     opener = urllib.request.build_opener(
#         urllib.request.ProxyHandler(
#             {'http': 'http://lum-customer-hl_d08f7ef9-zone-static:cyg5pnh9hnlw@zproxy.lum-superproxy.io:22225',
#             'https': 'http://lum-customer-hl_d08f7ef9-zone-static:cyg5pnh9hnlw@zproxy.lum-superproxy.io:22225'}))
#     print(opener.open('http://lumtest.com/myip.json').read())
#

luminati_proxy_dict = {
    'http': 'http://lum-customer-hl_d08f7ef9-zone-static:cyg5pnh9hnlw@zproxy.lum-superproxy.io:22225',
    'https': 'http://lum-customer-hl_d08f7ef9-zone-static:cyg5pnh9hnlw@zproxy.lum-superproxy.io:22225'}
