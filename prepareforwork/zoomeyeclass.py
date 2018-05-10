dict = {}
dict['web应用'] = ['WordPress', 'phpMyAdmin', 'Joomla',
                 'DedeCMS', 'LiteSpeed', 'Drupa', 'FCKeditor',
                 'CKEditor', 'Discuz!', 'RoundCube', 'Magento',
                 'Shopify', 'Z-Blog', 'phpBB', 'phpcms', 'ZenCart',
                 'Invision Power Board', 'ECShop', 'MaxCMS', 'osCommerce']
dict['设备'] = ['Unknown', 'broadband router', 'WAP', 'router', 'media device',
             'webcam', 'firewall', 'switch', 'storage-misc', 'printer', 'bridge',
             'security-misc', 'VoIP adapter', 'load balancer', 'remote management',
             'PBX', 'VoIP phone', 'power-misc', 'specialized', 'proxy server']
dict['Web框架'] = ['ASP.NET MVC', 'Apache Coyote', 'ExpressJS', 'ColdFusion',
                 'ThinkPHP', 'CodeIgniter', 'Spring Framework', 'Django', 'Struts2',
                 'Zope', 'Nette', 'CakePHP', 'Fat-Free', 'web2py', 'Tornado', 'Play! Framework',
                 'WebObjects', 'Zend Framework', 'Jetspeed', 'Jinja2']
dict['组键'] = ['Unknown', 'Apache httpd', 'OpenSSH', 'Dropbear sshd', 'Allegro RomPager',
              'AkamaiGHost', 'gSOAP soap', 'nginx', 'Microsoft IIS httpd', 'Portable SDK for UPnP devices',
              'MySQL', 'Microsoft HTTPAPI httpd', 'TR-069 remote access', 'lighttpd',
              'Microsoft Windows RPC', 'Exim smtpd', 'Microsoft Terminal Service',
              'Dovecot imapd', 'mini_httpd', 'Dovecot pop3d']

dict['Web容器'] = ['Apache httpd', 'Microsoft IIS httpd', 'Nginx', 'Varnish',
                 'Tengine', 'Litespeed', 'Apache Traffic Server', 'Apache Tomcat',
                 'WWW Server', 'Microsoft-HTTPAPI', 'lighttpd', 'Microsfot-HTTPAPI',
                 'IBM HTTP Server', 'Resin', 'eHTTP', 'Heroku Proxy', 'kangle',
                 'Jetty', 'Squid', 'GlassFish Server']

dict['服务'] = ['Unknown', 'http', 'ssh', 'ftp', 'telnet', 'soap', 'smtp',
              'upnp', 'sip', 'mysql', 'domain', 'ms-wbt-server', 'pop3',
              'imap', 'rtsp', 'netbios-ssn', 'msrpc', 'snmp', 'http-proxy', 'netbios-ns']


from prepareforwork.someusefuldict import MONGO

inser = MONGO('localhost', 27017)
inser.insertintomongo(dict)