# -*- coding:utf-8 -*-
import os, sys
import threading
import time
import re
import ctypes
import urllib.request, urllib.parse, urllib.error
import socket
import urllib.request, urllib.error, urllib.parse
import http.cookiejar
import zlib
import struct
import ctypes
import io


class Log():
    FILE = ''
    LOGLOCK = None
    std_out_handle = None
    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE = -12
    GRAY    = 0x08
    GREEN   = 0x0a
    BLUE    = 0x0b
    RED     = 0x0c
    PINK    = 0x0d
    YELLOW  = 0x0e
    WHITE   = 0x0f
    
    @staticmethod
    def INIT():
        Log.std_out_handle = ctypes.windll.kernel32.GetStdHandle(Log.STD_OUTPUT_HANDLE)
        if Log.LOGLOCK == None:
            Log.LOGLOCK = threading.RLock()
        
    @staticmethod
    def set_cmd_text_color(color):
        return ctypes.windll.kernel32.SetConsoleTextAttribute(Log.std_out_handle, color)   
        
    @staticmethod
    def resetColor():
        Log.set_cmd_text_color(Log.WHITE)
        
    @staticmethod
    def console(line, color=YELLOW):
        line = line + '\n'
        Log.LOGLOCK.acquire()
        Log.set_cmd_text_color(color)
        sys.stdout.write(line)
        Log.resetColor()
        Log.LOGLOCK.release()
        
    @staticmethod
    def file(line, color=GREEN):
        Log.console(line, color)
        line = line + '\n'    
        if Log.FILE != '':
            Log.LOGLOCK.acquire()
            f = open(Log.FILE, 'a')
            f.write(line)
            f.close()
            Log.LOGLOCK.release()

class AHTTPErrorProcessor(urllib.request.HTTPErrorProcessor):
    def http_response(self, req, response):
        code, msg, hdrs = response.code, response.msg, response.info()        
        if code == 302: return response  # stop 302
        if not (200 <= code < 300):
            response = self.parent.error('http', req, response, code, msg, hdrs)
        return response
    https_response = http_response

class HttpSession():
    UserAgent = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'
    def __init__(self, url='', follow302=True):
        self.jar = http.cookiejar.CookieJar()
        self.url     = url
        self.html    = ''
        self.headers = ''
        self.jumpurl = ''
        self.follow302 = follow302
        self.opener  = None
    
    @staticmethod
    def make_cookie(name, value, domain):
        return http.cookiejar.Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain=domain,
            domain_specified=True,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=False,
            comment=None,
            comment_url=None,
            rest=None
        )
        
    def Get(self, url='', data=None):
        if url != '':
            self.url = url
        if self.url == '':
            self.Update('')
            return False
        if self.opener == None:
            if self.follow302:
                self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
            else:
                self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), AHTTPErrorProcessor)
            self.opener.addheaders = [
                ('User-Agent', HttpSession.UserAgent),
                #('Accept-Encoding', 'gzip, deflate'),
                ]
        try:
            return self.__GetHtml(data)
        except:
            self.html = ''
            self.jumpurl = ''
            return False
    
    def __GetHtml(self, data):        
        try:
            if data == None:
                response = self.opener.open(self.url, timeout = 10)
            else:
                response = self.opener.open(self.url, urllib.parse.urlencode(data), timeout = 10)
            self.html = response.read()
            self.jumpurl = response.url
            self.headers = dict(response.info())
            return True
        except urllib.error.HTTPError as e:
            self.html = e.read()
            self.jumpurl = e.url
            self.headers = dict(response.info())
            return True
        except:
            self.html = ''
            self.jumpurl = ''
            return False
    def Update(self, url):
        self.html = ''
        self.jumpurl = ''
        self.headers = ''
        self.url = url
    
    def AddCookie(self, name, value, site):
        self.jar.set_cookie(HttpSession.make_cookie(name, value, site))
            
class Tasker():
    def __init__(self, resource, threadsnum=5):
        self.lock = threading.RLock()
        self.taskpool = []
        self.resource = resource
        self.threadsnum = 5
        self.bend = False
        
    def run(self):
        threads = []
        t = threading.Thread(target=self.taskadder, args=())
        t.start()
        threads.append(t)        
        for i in range(0, self.threadsnum):
            t = threading.Thread(target=self.taskgeter, args=())
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def taskadder(self):
        if isinstance(self.resource, list):
            for line in self.resource:
                resolved = self.resolvetask(line)
                self.taskpool += resolved
        tmpfile = None
        if isinstance(self.resource, str):
            tmpfile = open(self.resource)
        if isinstance(self.resource, io.IOBase) or tmpfile:
            if not tmpfile:
                tmpfile = self.resource
        if tmpfile:
            for line in tmpfile:
                line = line.strip('\r\n')
                while True:
                    self.lock.acquire()
                    if len(self.taskpool) > self.threadsnum * 3:
                        self.lock.release()
                        time.sleep(0.1)
                        continue
                    else:
                        resolved = self.resolvetask(line)
                        self.taskpool += resolved
                        self.lock.release()
                        break
        self.lock.acquire()
        self.bend = True
        self.lock.release()
        if isinstance(self.resource, str):
            tmpfile.close()
        
    def taskgeter(self):
        currenttask = None
        while True:
            self.lock.acquire()
            if len(self.taskpool) > 0:
                currenttask = self.taskpool[0]
                del self.taskpool[0]
                self.lock.release()
            else:
                if self.bend:
                    self.lock.release()
                    return
                self.lock.release()
                time.sleep(0.1)
                continue
            self.taskprocesser(currenttask)
        
    def taskprocesser(self, task):
        sys.stdout.write(task+'\n')
        
    def resolvetask(self, task):
        return [task]


fingers = [
("ACSNO网络探针","http://www.acsno.com.cn/product_view.php?id=78","4/22/2015",[{"title":["探针管理与测试系统-登录界面"],"header":["h123"]}]),
("网趣网上购物系统旗舰版","http://www.cnhww.com/list.asp?id=8","4/17/2015",[{"header":["Set-Cookie: dmwh%5Fuser"]},{"body":["class.asp?lx=tejia","images/cnhww_css.css","Wq_StranJF.js"]}]),
("网康 NS-ASG","http://www.netentsec.com","4/17/2015",[{"title":["NS-ASG"]},{"body":["commonplugin/softkeyboard.js"]}]),
("方维众筹","http://www.fanwe.com/index.php?ctl=zongchou#yanshi","4/17/2015",[{"body":["app/Tpl/fanwe_1/images/lazy_loading.gif","index.php?ctl=article_cate"]}]),
("无忧购物系统ASP通用版","http://www.gzwyshop.com/Pdt_zz.asp","4/17/2015",[{"body":["images/loginh2.gif","nsort.asp?sort_id="]}]),
("XYCMS","http://www.yuleroom.cn/","4/17/2015",[{"title":["Powered by XYCMS"]},{"body":["advfile/ad12.js"]}]),
("JSPGOU","http://demo3.jeecms.com/","4/17/2015",[{"title":["Powered by JSPGOU"]},{"body":["/r/gou/www/css/","shopMember/index.jspx"]}]),
("Jspxcms","http://www.jspxcms.com/","4/17/2015",[{"title":["Powerd by Jspxcms"]},{"body":["_files/jspxcms.css"]}]),
("惠尔顿上网行为管理系统","http://www.wholeton.com/","4/16/2015",[{"body":["updateLoginPswd.php","PassroedEle"]}]),
("milu_seotool","http://addon.discuz.com/?ac=item&from=api_1&id=milu_seotool.plugin","4/7/2015",[{"body":["plugin.php?id=milu_seotool"]}]),
("Privoxy","http://www.privoxy.org","4/7/2015",[{"header":["Proxy-Agent: Privoxy"]}]),
("seeyoo广告机","http://www.seeyoo.cn/","3/30/2015",[{"body":["AC_Config.js"]}]),
("埃森诺网络服务质量检测系统","http://www.acsno.com.cn","3/29/2015",[{"title":["埃森诺网络服务质量检测系统"]}]),
("Mercurial","http://mercurial.selenic.com/","2/27/2015",[{"title":["Mercurial repositories index"]}]),
("一采通","http://www.1caitong.com","1/27/2015",[{"body":["/custom/GroupNewsList.aspx?GroupId="]}]),
("O2OCMS","http://www.zzqss.com/","1/26/2015",[{"body":["/index.php/clasify/showone/gtitle/"]}]),
("全国烟草系统","#","1/26/2015",[{"body":["ycportal/webpublish"]}]),
("万户网络","http://www.wanhu.com.cn","12/15/2014",[{"body":["css/css_whir.css"]}]),
("ExtMail","http://www.extmail.org","12/15/2014",[{"title":["欢迎使用ExtMail"]},{"body":["setCookie('extmail_username"]}]),
("金龙卡金融化一卡通网站查询子系统","http://www.posser.net/","12/11/2014",[{"title":["金龙卡金融化一卡通网站查询子系统"]},{"body":["location.href=\"homeLogin.action"]}]),
("ezOFFICE","http://www.whir.net/cn/ezofficeqyb/index_52.html","12/11/2014",[{"title":["Wanhu ezOFFICE"]},{"body":["EZOFFICEUSERNAME"]}]),
("GlassFish","https://glassfish.java.net","12/11/2014",[{"header":["Server: GlassFish Server"]}]),
("Piwigo","http://cn.piwigo.org","12/3/2014",[{"body":["generator\" content=\"Piwigo"]},{"header":["pwg_id"]}]),
("天柏在线培训/考试系统","http://www.timber2005.com/","12/2/2014",[{"title":["连接中，请稍候"],"header":["index.html"]},{"body":["App_Image/PXSystem"]},{"body":["App_Image/System"]}]),
("Dorado","http://bstek.com/product/dorado7_introduce","12/2/2014",[{"title":["Dorado Login Page"]}]),
("openEAP","http://products.suntektech.com/products/archive.jsp?catid=327&id=269","12/2/2014",[{"title":["openEAP_统一登录门户"]}]),
("hikashop","http://www.hikashop.com","11/28/2014",[{"body":["/media/com_hikashop/css/"]}]),
("PigCms","http://pigcms.com","11/27/2014",[{"header":["X-Powered-By: PigCms.com"]}]),
("帕拉迪统一安全管理和综合审计系统","http://www.pldsec.com/","11/26/2014",[{"body":["module/image/pldsec.css"]}]),
("qibosoft v7","http://www.qibosoft.com/","11/25/2014",[{"body":["/images/v7/cms.css\">"]}]),
("KXmail","http://mail.pushmold.com","11/25/2014",[{"body":["Powered By <a href=\"http://www.kxmail.net"]},{"title":["科信邮件系统"]}]),
("易创思ecs","http://www.ecs.cn/","11/25/2014",[{"body":["src=\"/Include/EcsServerApi.js"]}]),
("URP 综合教务系统","http://jwxt.bibt.edu.cn/","11/25/2014",[{"body":["<input name=\"j_captcha_response\" type=\"hidden"]},{"title":["URP 综合教务系统"]}]),
("webbuilder","http://www.putdb.com","11/25/2014",[{"body":["src=\"webbuilder/script/wb.js"]}]),
("e-Learning","http://nvcc.cneln.net","11/25/2014",[{"body":["method=\"post\" action=\"/eln3_asp/login.do"]}]),
("ruvar","http://gov.ruvar.com/","11/25/2014",[{"body":["<iframe id=\"ifrm\" width=\"100%\" height=\"100%\" frameborder=\"0\" scrolling=\"no\" src=\"/include/login.aspx"]}]),
("acsoft","http://ac.haidilao.com/","11/25/2014",[{"body":["login_1\">CA密码"]},{"title":["费用报销系统"]}]),
("lezhixing","http://202.108.154.209/datacenter/#","11/25/2014",[{"body":["var contextPath = \"/datacenter"]},{"body":["location.href=contextPath+\"/login/password/password.jsp"]},{"body":["action=\"/datacenter/authentication/login.do\" method=\"post"]}]),
("yunyin","http://press.njtu.edu.cn","11/25/2014",[{"body":["技术支持：云因信息"]},{"body":["<a href=\"../scrp/getpassword.cfm"]},{"body":["/scrp/book.cfm\" method=\"post\">"]}]),
("某通用型政府cms","http://www.wooyun.org/bugs/wooyun-2014-054821","11/17/2014",[{"body":["/deptWebsiteAction.do"]}]),
("U-Mail","http://www.comingchina.com","11/16/2014",[{"body":["<BODY LINK=\"White\" VLINK=\"White\" ALINK=\"White\">"]}]),
("IP.Board","http://www.invisionpower.com/apps/board/","11/13/2014",[{"body":["ipb.vars"]}]),
("i@Report","http://sanlink.com.cn","11/11/2014",[{"body":["ESENSOFT_IREPORT_SERVER"]},{"body":["com.sanlink.server.Login"]},{"body":["ireportclient"]},{"body":["css/ireport.css"]}]),
("国家数字化学习资源中心系统","http://ipv6.google.com.hk/#newwindow=1&q=%22技术支持：中央广播电视大学现代远程教育资源中心%22","11/11/2014",[{"title":["页面加载中,请稍候"],"body":["FrontEnd"]}]),
("UcSTAR","http://www.qqtech.com/comm/index.htm","11/11/2014",[{"title":["UcSTAR 管理控制台"]}]),
("mod_antiloris","http://sourceforge.net/projects/mod-antiloris/","11/10/2014",[{"header":["mod_antiloris"]}]),
("CISCO_VPN","http://www.cisco.com/","11/7/2014",[{"header":["webvpn"]}]),
("Axis2","http://axis.apache.org/axis2/","11/7/2014",[{"body":["axis2-web/css/axis-style.css"]},{"title":["Axis 2 - Home"]},{"title":["Apache-Axis"]}]),
("Puppet_Node_Manager","http://puppetlabs.com","11/6/2014",[{"title":["Puppet Node Manager"]}]),
("Kibana","http://www.elasticsearch.org/overview/kibana/","11/6/2014",[{"title":["Kibana"]},{"body":["kbnVersion"]}]),
("HAProxy_Report","http://haproxy.com","11/6/2014",[{"body":["Statistics Report for HAProxy"]}]),
("Spark_Master","http://spark.apache.org","11/6/2014",[{"title":["Spark Master at"]}]),
("Spark_Worker","http://spark.apache.org","11/6/2014",[{"title":["Spark Worker at"]}]),
("GenieATM","http://www.genienrm.com/index.php","11/6/2014",[{"title":["GenieATM"]},{"body":["Copyright© Genie Networks Ltd."]},{"body":["defect 3531"]}]),
("dasannetworks","http://www.dasannetworks.com/en/index.asp","11/3/2014",[{"body":["clear_cookie(\"login\");"]}]),
("eagleeyescctv","http://www.eagleeyescctv.com/","11/3/2014",[{"body":["IP Surveillance for Your Life"]},{"body":["/nobody/loginDevice.js"]}]),
("Linksys_SPA_Configuration","http://www.linksys.com","11/3/2014",[{"title":["Linksys SPA Configuration"]}]),
("CDR-Stats","http://www.cdr-stats.org","11/3/2014",[{"title":["CDR-Stats | Customer Interface"]},{"body":["/static/cdr-stats/js/jquery"]}]),
("SHOUTcast","http://www.shoutcast.com","11/3/2014",[{"title":["SHOUTcast Administrator"]}]),
("SLTM32_Configuration","http://www.lgericssonipecs.com","11/3/2014",[{"title":["SLTM32 Web Configuration Pages "]}]),
("ntop","https://www.ntop.org","11/3/2014",[{"body":["Global Traffic Statistics"]},{"header":["Server: ntop"]},{"body":["ntopMenuID"]}]),
("SquirrelMail","http://www.squirrelmail.org","11/3/2014",[{"header":["SQMSESSID"]}]),
("PineApp","http://www.pineapp.com","11/3/2014",[{"title":["PineApp WebAccess - Login"]},{"body":["/admin/css/images/pineapp.ico"]}]),
("Synology_DiskStation","https://www.synology.com","11/3/2014",[{"title":["Synology DiskStation"]},{"body":["SYNO.SDS.Session"]}]),
("OnSSI_Video_Clients","http://www.onssi.com","11/3/2014",[{"title":["OnSSI Video Clients"]},{"body":["x-value=\"On-Net Surveillance Systems Inc.\""]}]),
("LiteSpeed_Web_Admin_Console","http://www.litespeedtech.com","11/3/2014",[{"title":["LiteSpeed Web Admin Console"]},{"header":["LSWSWEBUI"]}]),
("FortiGuard","http://www.fortiguard.com/static/webfiltering.html","11/3/2014",[{"body":["FortiGuard Web Filtering"]},{"title":["Web Filter Block Override"]},{"body":["/XX/YY/ZZ/CI/MGPGHGPGPFGHCDPFGGOGFGEH"]}]),
("Centreon","http://www.centreon.com","11/3/2014",[{"body":["Generator\" content=\"Centreon - Copyright"]},{"title":["Centreon - IT & Network Monitoring"]}]),
("blog_fc2","http://blog.fc2.com","11/3/2014",[{"header":["bloguid","cookietest=test"]}]),
("shopify","http://www.shopify.com","11/3/2014",[{"header":["X-Shopid:"]}]),
("sugon_gridview","http://www.sugon.com/product/detail/productid/105.html","10/29/2014",[{"body":["/common/resources/images/common/app/gridview.ico"]}]),
("concrete5","http://www.concrete5.org","10/26/2014",[{"body":["generator\" content=\"ezCMS"]},{"header":["CONCRETE5"]},{"body":["CCM_DISPATCHER_FILENAME"]}]),
("WebsiteBaker-CMS","http://www.websitebaker-cms.de","10/26/2014",[{"header":["wb_session_id"]}]),
("DokuWiki","https://www.dokuwiki.org","10/26/2014",[{"body":["generator\" content=\"DokuWiki"]},{"header":["DokuWiki"]}]),
("Directadmin","http://www.directadmin.com","10/26/2014",[{"header":["X-Directadmin"]},{"header":["DirectAdmin Daemon"]},{"title":["DirectAdmin Login"]}]),
("Diferior","http://diferior.com","10/26/2014",[{"body":["Powered by Diferior"]}]),
("DVWA","http://www.dvwa.co.uk","10/26/2014",[{"title":["Damn Vulnerable Web App"]},{"body":["dvwa/images/login_logo.png"]}]),
("wordpress_qTranslate","http://www.qianqin.de/qtranslate/","10/26/2014",[{"header":["qtrans_cookie_test"]}]),
("网神VPN","http://www.legendsec.com","10/26/2014",[{"body":["admin/js/virtual_keyboard.js"]},{"header":["host_for_cookie"]}]),
("nginx_admin","http://www.nginxcp.com","10/26/2014",[{"header":["nginx admin"]}]),
("Storm","http://storm.apache.org","10/24/2014",[{"title":["Storm UI"]},{"body":["stormtimestr"]}]),
("Privoxy代理","http://www.privoxy.org","10/24/2014",[{"header":["Privoxy"]}]),
("dayrui系列产品","http://www.dayrui.com/product/","10/23/2014",[{"header":["dr_ci_session"]},{"body":["dayrui/statics"]}]),
("FineCMS","http://www.dayrui.com","10/23/2014",[{"body":["Powered by FineCMS"]},{"body":["dayrui@gmail.com"]},{"body":["Copyright\" content=\"FineCMS"]}]),
("MaticsoftSNS_动软分享社区","http://sns.maticsoft.com","10/23/2014",[{"body":["MaticsoftSNS"]},{"body":["maticsoft","/Areas/SNS/"]}]),
("Maticsoft_Shop_动软商城","http://www.maticsoft.com/Products.aspx#shop","10/23/2014",[{"body":["Maticsoft Shop"]},{"body":["maticsoft","/Areas/Shop/"]}]),
("hishop","http://www.hishop.com.cn","10/23/2014",[{"body":["hishop.plugins.openid"]},{"body":["Hishop development team"]}]),
("北京阳光环球建站系统","http://www.sunad.net.cn/wangzhanjianshe/","10/22/2014",[{"body":["bigSortProduct.asp?bigid"]}]),
("amazon-cloudfront","http://aws.amazon.com/cn/cloudfront/","10/22/2014",[{"header":["X-Amz-Cf-Id"]}]),
("ecwapoa","http://www.google.com.hk/#newwindow=1&q=ecwapoa","10/22/2014",[{"body":["ecwapoa"]}]),
("easysite","http://huilan.com/zkhl/products/platform/easysite/index.html","10/21/2014",[{"body":["GENERATOR\" content=\"EasySite"]},{"body":["Copyright 2009 by Huilan"]},{"body":["_DesktopModules_PictureNews"]},{"header":["EasySite-Compression"]}]),
("擎天电子政务","http://www.skynj.com/cp/dzzw/index.htm","10/21/2014",[{"body":["App_Themes/1/Style.css"]},{"body":["window.location = \"homepages/index.aspx"]},{"body":["homepages/content_page.aspx"]}]),
("asp168欧虎","http://www.asp168.com","10/21/2014",[{"body":["App_Themes/1/Style.css"]},{"body":["window.location = \"homepages/index.aspx"]},{"body":["homepages/content_page.aspx"]}]),
("锐捷应用控制引擎","http://www.ruijie.com.cn/Product/Gateway/RG-ACE/RG-ACE","10/21/2014",[{"body":["window.open(\"/login.do\",\"airWin"]},{"title":["锐捷应用控制引擎"]}]),
("TinyShop","http://www.tinyrise.com/","10/20/2014",[{"body":["var server_url = '/__con__/__act__';"]},{"body":["tiny_token_"]}]),
("ThinkSNS","http://www.thinksns.com","10/20/2014",[{"body":["_static/image/favicon.ico"]},{"header":["T3_lang"]}]),
("Piwik","http://piwik.org","10/20/2014",[{"header":["PIWIK_SESSID"]}]),
("QingCloud","https://www.qingcloud.com","10/20/2014",[{"header":["QINGCLOUDELB"]}]),
("RG-PowerCache内容加速系统","http://www.ruijie.com.cn/","10/17/2014",[{"title":["RG-PowerCache"]}]),
("北京清科锐华CEMIS","http://www.reachway.com.cn/web/cemis/introduction.aspx","10/17/2014",[{"body":["/theme/2009/image","login.asp"]}]),
("iredadmin(Roundcube?)","http://www.iredmail.com","10/17/2014",[{"header":["iredadmin"]},{"body":["iredadmin"]}]),
("SIMIT_framework","","10/16/2014",[{"header":["SIMIT framework"]}]),
("flow_framework","http://flow.typo3.org/home","10/16/2014",[{"header":["FLOW/FRAMEWORK"]}]),
("Kohana-Framework","http://kohanaframework.org","10/16/2014",[{"header":["Kohana Framework"]}]),
("Restlet-Framework","https://github.com/restlet/restlet-framework-java","10/16/2014",[{"header":["Restlet-Framework"]}]),
("Play-Framework","http://www.playframework.com","10/16/2014",[{"header":["Play! Framework"]}]),
("Starlet","https://github.com/kazuho/Starlet","10/16/2014",[{"header":["Plack::Handler::Starlet"]}]),
("SamanPortal","http://www.sis-eg.com","10/16/2014",[{"header":["sisRapid"]}]),
("Fat-FreeFramework","http://fatfreeframework.com","10/16/2014",[{"header":["Fat-Free Framework"]}]),
("NetteFramework","http://nette.org","10/16/2014",[{"header":["Nette Framework"]}]),
("typo3","http://typo3.org","10/15/2014",[{"header":["fe_typo_user"]}]),
("irecms","http://www.irecms.de","10/15/2014",[{"header":["IRe.CMS"]}]),
("MuraCMS","http://www.getmura.com","10/15/2014",[{"header":["Mura CMS"]}]),
("Tncms","http://cn.bing.com/search?q=tncms+Xrds&go=提交&qs=n&form=QBRE&pq=tncms+xrds&sc=0-6&sp=-1&sk=&cvid=663f37af2cd849a0918ffe5212c56463","10/15/2014",[{"header":["X-Tncms-Version"]}]),
("Azure_ARR","http://blogs.msdn.com/b/azchina/archive/2013/11/21/disabling-arr-s-instance-affinity-in-windows-azure-web-sites.aspx","10/15/2014",[{"header":["ARRAffinity"]}]),
("sitecore","http://www.sitecore.net","10/15/2014",[{"header":["Sitecore CMS"]}]),
("synkronvia","http://synkronvia.com","10/15/2014",[{"header":["Synkron Via CMS"]}]),
("EasywebCMS","http://www.eaysweb.se","10/15/2014",[{"header":["Easyweb CMS"]}]),
("UMI.CMS","http://www.umi-cms.ru","10/15/2014",[{"header":["UMI.CMS"]}]),
("mozartframework","http://mozartframework.ru","10/15/2014",[{"header":["Mozart Framework"]}]),
("zikula_framework","http://zilkula.org","10/14/2014",[{"header":["ZIKULASID1"]},{"header":["ZIKULASID2"]},{"header":["ZIKULASID3"]}]),
("Zikula_CMS","http://www.zikula.de","10/14/2014",[{"header":["ZKSID2"]}]),
("Bad_Behavior","http://bad-behavior.ioerror.us/","10/14/2014",[{"header":["bb2_screener_"]}]),
("Bigcommerce","https://www.bigcommerce.com","10/14/2014",[{"header":["SHOP_SESSION_TOKEN"]}]),
("逐浪zoomla","http://www.zoomla.cn","10/14/2014",[{"body":["script src=\"http://code.zoomla.cn/"]},{"body":["NodePage.aspx","Item"]},{"body":["/style/images/win8_symbol_140x140.png"]}]),
("微普外卖点餐系统","http://diancan365.com/","10/14/2014",[{"body":["Author\" content=\"微普外卖点餐系统"]},{"body":["Powered By 点餐系统"]},{"body":["userfiles/shoppics/"]}]),
("squarespace建站","http://www.squarespace.com/","10/14/2014",[{"header":["SS_MID","squarespace.net"]}]),
("PrestaShop","http://www.prestashop.com","10/13/2014",[{"header":["PrestaShop"]},{"body":["Shop powered by PrestaShop"]}]),
("ECMall","http://ecmall.shopex.cn","10/13/2014",[{"header":["ECM_ID"]},{"body":["generator\" content=\"ECMall"]}]),
("OpenCart","http://www.opencart.com/","10/13/2014",[{"body":["Powered By OpenCart"]},{"body":["catalog/view/theme"]}]),
("Magento","http://magento.com","10/13/2014",[{"body":["body","BLANK_IMG"]},{"body":["Magento, Varien, E-commerce"]}]),
("Facebook_insights","https://developers.facebook.com/docs/platforminsights","10/13/2014",[{"body":["fb:app_id"]}]),
("北创图书检索系统","http://www.bcrj.com.cn","10/13/2014",[{"body":["opac_two"]}]),
("Tipask","http://www.tipask.com","10/13/2014",[{"body":["Tipask Team"]}]),
("HIMS酒店云计算服务","http://www.luopan.cn","10/13/2014",[{"body":["GB_ROOT_DIR","maincontent.css"]},{"body":["HIMS酒店云计算服务"]}]),
("地平线CMS","http://www.deepsoon.com/","10/13/2014",[{"title":["Powered by deep soon"],"body":["labelOppInforStyle"]},{"body":["search_result.aspx","frmsearch"]}]),
("weebly","http://www.weebly.com/","10/13/2014",[{"header":["intern.weebly.net"]},{"body":["wsite-page-index"]}]),
("phpweb","http://www.phpweb.net","10/11/2014",[{"body":["PDV_PAGENAME"]}]),
("Webmin","http://www.webmin.cn","10/11/2014",[{"title":["Login to Webmin"]},{"body":["Webmin server on"]}]),
("mirapoint","http://www.mirapoint.com","10/10/2014",[{"body":["/wm/mail/login.html"]}]),
("UFIDA_NC","http://www.yonyou.com/product/NC.aspx","10/10/2014",[{"body":["UFIDA","logo/images/"]}]),
("元年财务软件","http://www.epochsoft.com.cn","10/9/2014",[{"body":["yuannian.css"]},{"body":["/image/logo/yuannian.gif"]}]),
("正方教务管理系统","http://www.zfsoft.com/type_jx/040000011001.html","10/9/2014",[{"body":["style/base/jw.css"]}]),
("BoyowCMS","http://www.boyow.com/Index.html","10/9/2014",[{"body":["publish by BoyowCMS"]}]),
("ganglia","http://ganglia.info","10/9/2014",[{"body":["ganglia_form.submit"]},{"header":["gs=unspecified"]}]),
("mantis","http://www.mantisbt.org","10/9/2014",[{"body":["browser_search_plugin.php?type=id"]},{"body":["MantisBT Team"]}]),
("创星伟业校园网群","http://www.conking.com.cn","10/9/2014",[{"body":["javascripts/float.js","vcxvcxv"]}]),
("TerraMaster","http://www.terra-master.com/","10/9/2014",[{"body":["/js/common.js"],"title":["vcxvcxv"]}]),
("OA企业智能办公自动化系统","http://down.chinaz.com/soft/23657.htm","10/9/2014",[{"body":["input name=\"S1\" type=\"image\"","count/mystat.asp"]}]),
("anymacro","http://www.anymacro.com","10/9/2014",[{"header":["LOGIN_KEY"]},{"body":["document.aa.F_email"]},{"body":["AnyWebApp"]}]),
("iGENUS_webmail","http://www.igenus.cn","10/9/2014",[{"body":["script/logo_display_set.js","check code"]},{"body":["top.location='login.php';"]},{"body":["iGENUS WEBMAIL SYSTEM"]},{"body":["css/igenus.css"]}]),
("gitlab","https://about.gitlab.com/","10/9/2014",[{"header":["_gitlab_session"]},{"body":["gon.default_issues_tracker"]},{"body":["GitLab Community Edition"]}]),
("trac","http://trac.edgewall.org","10/9/2014",[{"body":["<h1>Available Projects</h1>"]},{"body":["wiki/TracGuide"]},{"header":["trac_session"]}]),
("MRTG","http://oss.oetiker.ch/mrtg/","10/9/2014",[{"body":["Command line is easier to read using \"View Page Properties\" of your browser"]},{"title":["MRTG Index Page"]},{"body":["commandline was: indexmaker"]}]),
("opennms","http://www.opennms.com","10/9/2014",[{"header":["/opennms/login.jsp"]},{"body":["/css/gwt-asset.css"]},{"body":["OpenNMS® is a registered trademark of"]}]),
("Munin","http://munin-monitoring.org","10/9/2014",[{"body":["Auto-generated by Munin"]},{"body":["munin-month.html"]}]),
("Adiscon_LogAnalyzer","http://loganalyzer.adiscon.com","10/9/2014",[{"title":["Adiscon LogAnalyzer"]},{"body":["Adiscon LogAnalyzer","Adiscon GmbH"]}]),
("Atmail","https://www.atmail.com","10/9/2014",[{"body":["Powered by Atmail"]},{"header":["atmail6"]},{"body":["FixShowMail"]}]),
("orocrm","http://www.orocrm.com","10/9/2014",[{"body":["/bundles/oroui/"]}]),
("ALCASAR","http://www.alcasar.net","10/9/2014",[{"body":["valoriserDiv5"]}]),
("Nagios","http://www.nagios.org","10/9/2014",[{"header":["Nagios access"]},{"body":["/nagios/cgi-bin/status.cgi"]}]),
("webEdition","http://www.webedition.org","10/9/2014",[{"body":["generator\" content=\"webEdition"]}]),
("cart_engine","http://www.c97.net","10/8/2014",[{"body":["skins/_common/jscripts.css"]}]),
("IPFire","http://www.ipfire.org","10/8/2014",[{"header":["IPFire - Restricted"]}]),
("testlink","http://testlink.org","10/8/2014",[{"body":["testlink_library.js"]}]),
("NOALYSS","http://www.phpcompta.org","10/8/2014",[{"title":["NOALYSS"]}]),
("bacula-web","http://www.bacula-web.org","10/8/2014",[{"title":["Webacula"]},{"title":["Bacula Web"]},{"title":["Bacula-Web"]}]),
("Ultra_Electronics","http://en.wikipedia.org/wiki/NetillaOS_NetConnect_by_Northbridge_Secure_Systems_(Secure_Remote_Access_SSL_VPN)","10/8/2014",[{"body":["/preauth/login.cgi"]},{"body":["/preauth/style.css"]}]),
("Osclass","http://osclass.org/","10/8/2014",[{"body":["generator\" content=\"Osclass"]},{"header":["osclass"]}]),
("hellobar","http://hellobar.com","10/8/2014",[{"body":["hellobar.js"]}]),
("Django","http://djangoproject.com","10/8/2014",[{"body":["__admin_media_prefix__"]},{"body":["csrfmiddlewaretoken"]}]),
("cakephp","http://cakephp.org","10/8/2014",[{"header":["CAKEPHP"]}]),
("51yes","http://www.51yes.com","10/8/2014",[{"body":["51yes.com/click.aspx"]}]),
("recaptcha","http://www.google.com/recaptcha/intro/index.html","10/8/2014",[{"body":["recaptcha_ajax.js"]}]),
("hubspot","http://www.hubspot.com","10/8/2014",[{"body":["js.hubspot.com/analytics"]}]),
("Communique","http://en.wikipedia.org/wiki/InSoft_Inc.#Communique","10/8/2014",[{"header":["Communique"]}]),
("Chromelogger","http://craig.is/writing/chrome-logger/techspecs","10/4/2014",[{"header":["X-Chromelogger-Data"]}]),
("OpenMas","http://zj.chinamobile.com","10/4/2014",[{"title":["OpenMas"]},{"body":["loginHead\"><link href=\"App_Themes"]}]),
("Hudson","http://hudson-ci.org","9/30/2014",[{"header":["X-Hudson"]}]),
("Splunk","http://www.splunk.com","9/30/2014",[{"body":["Splunk.util.normalizeBoolean"]}]),
("zenoss","http://www.zenoss.com","9/30/2014",[{"body":["/zport/dmd/"]}]),
("Synology_NAS","http://www.synology.com","9/29/2014",[{"header":["webman/index.cgi"]},{"body":["modules/BackupReplicationApp"]}]),
("cpanel","http://cpanel.net","9/28/2014",[{"header":["cprelogin:"]}]),
("WebObjects","http://wiki.wocommunity.org/display/WEB/Home","9/28/2014",[{"header":["WebObjects","wosid"]}]),
("梭子鱼防火墙","https://www.barracuda.com/","9/28/2014",[{"body":["a=bsf_product\" class=\"transbutton","/cgi-mod/header_logo.cgi"]}]),
("梭子鱼设备","http://www.barracudanetworks.com","9/28/2014",[{"header":["BarracudaHTTP"]}]),
("PHP-CGI","http://baidu.com/?q=PHP-CGI","9/28/2014",[{"header":["PHP-CGI"]}]),
("微门户","http://www.tvm.cn","9/25/2014",[{"body":["/tpl/Home/weimeng/common/css/"]}]),
("Amaya","http://www.w3.org/Amaya","9/22/2014",[{"body":["generator\" content=\"Amaya"]}]),
("AlloyUI","http://www.alloyui.com","9/22/2014",[{"body":["cdn.alloyui.com"]}]),
("Akamai","http://akamai.com","9/22/2014",[{"header":["X-Akamai-Transformed"]}]),
("advancedwebstats","http://www.advancedwebstats.com","9/22/2014",[{"body":["caphyon-analytics.com/aws.js"]}]),
("adriver","http://adriver.ru","9/22/2014",[{"body":["ad.adriver.ru/cgi-bin"]}]),
("Adobe_RoboHelp","http://adobe.com/products/robohelp.html","9/22/2014",[{"body":["generator\" content=\"Adobe RoboHelp"]}]),
("Adobe_GoLive","http://www.adobe.com/products/golive","9/22/2014",[{"body":["generator\" content=\"Adobe GoLive"]}]),
("Adobe_ CQ5","http://adobe.com/products/cq.html","9/22/2014",[{"body":["_jcr_content"]}]),
("ColdFusion","http://adobe.com/products/coldfusion-family.html","9/22/2014",[{"body":["/cfajax/"]},{"header":["CFTOKEN"]},{"body":["ColdFusion.Ajax"]},{"body":["cdm"]}]),
("adinfinity","http://adinfinity.com.au","9/22/2014",[{"body":["adinfinity.com.au/adapt"]}]),
("addthis","http://addthis.com","9/22/2014",[{"body":["addthis.com/js/"]}]),
("phpDocumentor","http://www.phpdoc.org","9/22/2014",[{"body":["Generated by phpDocumentor"]}]),
("Open_AdStream","http://xaxis.com/","9/22/2014",[{"body":["OAS_AD"]}]),
("Google_AdSense","https://www.google.com/adsense","9/22/2014",[{"body":["googlesyndication"]}]),
("3DCART","http://www.3dcart.com","9/22/2014",[{"header":["X-Powered-By: 3DCART"]}]),
("2z project","http://2zproject-cms.ru","9/22/2014",[{"body":["Generator\" content=\"2z project"]}]),
("1und1","http://1und1.de","9/22/2014",[{"body":["/shop/catalog/browse?sessid="]}]),
("TechartCMS","http://www.techart.ru","9/22/2014",[{"header":["X-Powered-Cms: Techart CMS"]}]),
("TwilightCMS","http://www.twl.ru","9/22/2014",[{"header":["X-Powered-Cms: Twilight CMS"]}]),
("WMSN","http://wmsn.biz/","9/22/2014",[{"header":["X-Powered-Cms: WMSN"]}]),
("SubrionCMS","http://www.subrion.com","9/22/2014",[{"header":["X-Powered-Cms: Subrion CMS"]}]),
("BPanelCMS","http://www.bpanel.net","9/22/2014",[{"header":["X-Powered-Cms: BPanel CMS"]}]),
("FOXI BIZzz","http://foxi.biz","9/22/2014",[{"header":["X-Powered-Cms: FOXI BIZzz"]}]),
("BitrixSiteManager","http://www.1c-bitrix.ru","9/22/2014",[{"header":["X-Powered-Cms: Bitrix Site Manager"]}]),
("EleanorCMS","http://eleanor-cms.ru","9/22/2014",[{"header":["Eleanor CMS"]}]),
("Z-BlogPHP","http://www.zblogcn.com","9/22/2014",[{"header":["Product: Z-BlogPHP"]}]),
("Typecho","http://typecho.org","9/22/2014",[{"body":["generator\" content=\"Typecho"]},{"body":["强力驱动","Typecho"]}]),
("护卫神网站安全系统","http://www.huweishen.com","9/19/2014",[{"title":["护卫神.网站安全系统"]}]),
("护卫神主机管理","http://www.huweishen.com","9/19/2014",[{"title":["护卫神·主机管理系统"]}]),
("LUM服务器管理","http://www.lum.net.cn","9/19/2014",[{"header":["LUM_SESSION"]}]),
("蓝盾BDWebGuard","http://www.bluedon.com/product/category/4.html","9/18/2014",[{"body":["BACKGROUND: url(images/loginbg.jpg) #e5f1fc"]}]),
("MOBOTIX_Camera","http://www.mobotix.com/","9/18/2014",[{"header":["MOBOTIX Camera"]}]),
("ECOR","http://www.everfocus.de/","9/18/2014",[{"header":["ECOR264"]}]),
("TP-LINK","http://www.tp-link.tw/products/?categoryid=201","9/18/2014",[{"header":["TP-LINK"]}]),
("HuaweiHomeGateway","http://www.huawei.com","9/18/2014",[{"header":["HuaweiHomeGateway"]}]),
("APC_Management","http://www.apc.com/","9/18/2014",[{"header":["APC Management Card"]},{"body":["This object on the APC Management Web Server is protected"]}]),
("Allegro-Software-RomPager","http://www.allegrosoft.com/embedded-web-server","9/18/2014",[{"header":["Allegro-Software-RomPager"]}]),
("CCProxy","http://www.ccproxy.com","9/18/2014",[{"header":["Server: CCProxy"]}]),
("DI-804HV","http://www.dlink.com/xk/sq/support/product/di-804hv-broadband-vpn-router","9/18/2014",[{"header":["DI-804HV"]}]),
("AirLink_modem","http://www.airLink.com","9/18/2014",[{"header":["Modem@AirLink.com"]}]),
("moosefs","http://www.moosefs.org","9/17/2014",[{"body":["mfs.cgi"]},{"body":["under-goal files"]}]),
("WHM","http://cpanel.net/cpanel-whm/","9/17/2014",[{"header":["whostmgrsession"]}]),
("用友商战实践平台","http://tradewar.135e.com","9/17/2014",[{"body":["Login_Main_BG","Login_Owner"]}]),
("ZTE_MiFi_UNE","http://www.zte.com.cn/cn/","9/17/2014",[{"title":["MiFi UNE 4G LTE"]}]),
("rap","http://www.arubanetworks.com.cn/allwireless/","9/17/2014",[{"body":["/jscripts/rap_util.js"]}]),
("Scientific-Atlanta_Cable_Modem","http://www.cisco.com/web/services/acquisitions/scientific-atlanta.html","9/17/2014",[{"title":["Scientific-Atlanta Cable Modem"]}]),
("Aethra_Telecommunications_Operating_System","http://www.aethra.com","9/17/2014",[{"header":["atos"]}]),
("Cisco_Cable_Modem","http://www.cisco.com","9/17/2014",[{"title":["Cisco Cable Modem"]}]),
("Wimax_CPE","http://www.huawei.com/cn/ProductsLifecycle/RadioAccessProducts/WiMAXProducts/hw-194630.htm","9/17/2014",[{"title":["Wimax CPE Configuration"]}]),
("HFS","http://www.rejetto.com/hfs/","9/16/2014",[{"header":["Server: HFS"]}]),
("Macrec_DVR","http://macrec.co","9/16/2014",[{"title":["Macrec DVR"]}]),
("CrushFTP","http://www.crushftp.com","9/16/2014",[{"header":["Server: CrushFTP HTTP Server"]}]),
("SMA_Sunny_Webbox","http://www.sma-america.com/en_US/products/monitoring-systems/sunny-webbox.html","9/16/2014",[{"title":["SMA Sunny Webbox"]},{"header":["Server: WebBox-20"]}]),
("ecshop","http://www.ecshop.com/","9/16/2014",[{"title":["Powered by ECShop"]},{"header":["ECS_ID"]},{"body":["content=\"ECSHOP"]},{"body":["/api/cron.php"]}]),
("gunicorn","http://gunicorn.org","9/16/2014",[{"header":["gunicorn"]}]),
("Sucuri","https://sucuri.net","9/15/2014",[{"header":["Sucuri/Cloudproxy"]}]),
("WebKnight","https://www.aqtronix.com/webknight/","9/15/2014",[{"header":["WebKnight"]}]),
("PaloAlto_Firewall","https://www.paloaltonetworks.com","9/15/2014",[{"body":["Access to the web page you were trying to visit has been blocked in accordance with company policy"]}]),
("FortiWeb","http://www.fortinet.com.tw/products/fortiweb/","9/15/2014",[{"header":["FORTIWAFSID"]},{"header":["FortiWeb"]}]),
("Mod_Security","https://www.modsecurity.org","9/15/2014",[{"header":["Mod_Security"]}]),
("Citrix_Netscaler","http://www.citrix.com.tw/products/netscaler-application-delivery-controller/overview.html","9/15/2014",[{"header":["ns_af"]}]),
("Dotdefender","http://www.applicure.com/Products/dotdefender","9/15/2014",[{"header":["X-Dotdefender-Denied"]}]),
("Kerio_WinRoute_Firewall","http://winroute.ru/kerio_winroute_firewall.htm","9/15/2014",[{"header":["Kerio WinRoute Firewall"]},{"body":["style/bodyNonauth.css"]}]),
("Motorola_SBG900","http://www.motorolasolutions.com/CN-ZH/Business+Solutions/Industry+Solutions/Utilities/Wireless+Broadband+Solution_CN-ZH","9/12/2014",[{"title":["Motorola SBG900"]}]),
("Ruckus","http://www.ruckuswireless.com","9/12/2014",[{"body":["mon. Tell me your username"]},{"title":["Ruckus Wireless Admin"]}]),
("ZyXEL","http://www.zyxel.com/cn/zh/products_services/service_provider-dsl_cpes.shtml?t=c","9/12/2014",[{"body":["Forms/rpAuth_1"]}]),
("Horde","http://www.horde.org/apps/webmail","9/12/2014",[{"body":["IMP: Copyright 2001-2009 The Horde Project"]},{"header":["Horde3"]},{"header":["Set-Cookie: Horde"]}]),
("Roundcube","http://roundcube.net","9/12/2014",[{"header":["roundcube_sessid"]}]),
("Comcast_Business_Gateway","http://business.comcast.com/","9/12/2014",[{"body":["Comcast Business Gateway"]}]),
("teamportal","http://www.teamsystem.com","9/12/2014",[{"body":["TS_expiredurl"]}]),
("Lotus-Domino","http://www-03.ibm.com/software/products/en/ibmdomino","9/12/2014",[{"header":["Server: Lotus-Domino"]}]),
("Lotus","http://ibm.com","9/12/2014",[{"title":["IBM Lotus iNotes Login"]},{"body":["iwaredir.nsf"]}]),
("arrisi_Touchstone","http://www.arrisi.com/products/touchstone/","9/12/2014",[{"title":["Touchstone Status"]},{"body":["passWithWarnings"]}]),
("Zimbra","http://www.zimbra.com","9/12/2014",[{"header":["ZM_TEST"]}]),
("DnP Firewall","http://ipv6.google.com.hk/search?q=DnP+Firewall","9/12/2014",[{"body":["Powered by DnP Firewall"]},{"body":["dnp_firewall_redirect"]}]),
("BinarySec","http://www.binarysec.com/","9/12/2014",[{"header":["X-Binarysec-Via"]}]),
("AnZuWAF","http://www.fsg2.org","9/12/2014",[{"header":["AnZuWAF"]}]),
("Safe3WAF","http://www.safe3.com.cn","9/12/2014",[{"header":["Safe3WAF"]}]),
("AOLserver","http://aolserver.sourceforge.net","9/12/2014",[{"header":["AOLserver"]}]),
("D-Link","http://www.dlink.com.hk/products/?pid=446","9/12/2014",[{"title":["D-Link VoIP Wireless Router"]},{"title":["D-LINK SYSTEMS"]}]),
("FreeboxOS","http://www.free.fr/assistance/5056.html","9/12/2014",[{"title":["Freebox OS"]},{"body":["logo_freeboxos"]}]),
("MediaWiki","http://www.mediawiki.org/wiki/MediaWiki","9/11/2014",[{"body":["generator\" content=\"MediaWiki"]},{"body":["/wiki/images/6/64/Favicon.ico"]},{"body":["Powered by MediaWiki"]}]),
("Jenkins","http://jenkins-ci.org","9/11/2014",[{"header":["X-Jenkins-Session"]},{"body":["translation.bundles"]},{"header":["X-Jenkins"]}]),
("reviewboard","https://www.reviewboard.org","9/11/2014",[{"body":["/static/rb/images/delete"]},{"header":["rbsessionid"]}]),
("Phabricator","http://phabricator.org","9/11/2014",[{"header":["phsid"]},{"body":["phabricator-application-launch-container"]},{"body":["res/phabricator"]}]),
("mod_auth_passthrough","http://cpanel.net","9/11/2014",[{"header":["mod_auth_passthrough"]}]),
("mod_bwlimited","http://ipv6.google.com.hk/search?q=mod_bwlimited","9/11/2014",[{"header":["mod_bwlimited"]}]),
("OpenSSL","http://openssl.org","9/11/2014",[{"header":["OpenSSL"]}]),
("lemis管理系统","http://www.baidu.com/s?wd=lemis%E7%AE%A1%E7%90%86%E7%B3%BB%E7%BB%9F","9/11/2014",[{"body":["lemis.WEB_APP_NAME"]}]),
("unknown_cms_rcms","http://fofa.so/","9/11/2014",[{"body":["r/cms/www"]},{"header":["clientlanguage"]}]),
("joomla-facebook","https://www.sourcecoast.com/joomla-facebook/","9/11/2014",[{"header":["jfbconnect_permissions_granted"]}]),
("ranzhi","http://www.ranzhi.org","9/11/2014",[{"body":["/sys/index.php?m=user&f=login&referer="]},{"header":["rid","theme","lang"]}]),
("chanzhi","http://www.chanzhi.org","9/11/2014",[{"body":["chanzhi.js"]},{"header":["Set-Cookie: frontsid"]},{"body":["poweredBy'><a href='http://www.chanzhi.org"]}]),
("unbouncepages","http://unbouncepages.com","9/11/2014",[{"header":["X-Unbounce-Pageid"]}]),
("unknown_cms","http://ipv6.google.com.hk/#q=%22Requestsuccess4ajax%22","9/11/2014",[{"header":["Requestsuccess4ajax"]}]),
("Alternate-Protocol","http://www.chromium.org/spdy/spdy-protocol/spdy-protocol-draft2","9/11/2014",[{"header":["Alternate-Protocol"]}]),
("pagespeed","https://github.com/pagespeed","9/11/2014",[{"header":["X-Page-Speed"]},{"header":["X-Mod-Pagespeed"]}]),
("TRSMAS","http://www.trs.com.cn","9/11/2014",[{"header":["X-Mas-Server"]}]),
("Wp-Super-Cache","https://wordpress.org/plugins/wp-super-cache/","9/11/2014",[{"header":["Wp-Super-Cache"]}]),
("Cocoon","http://cocoon.apache.org","9/11/2014",[{"header":["X-Cocoon-Version"]}]),
("LiquidGIS","http://www.liquidgis.com/","9/11/2014",[{"header":["Productname: LiquidGIS"]}]),
("Cacti","http://www.cacti.net","9/11/2014",[{"header":["Set-Cookie: Cacti="]},{"title":["Login to Cacti"]},{"body":["/plugins/jqueryskin/include/login.css"]}]),
("Cactiez","http://www.cactiez.com","9/11/2014",[{"header":["Cactiez"]}]),
("uPlusFtp","http://www.erisesoft.com/cn/uplusftp.htm","9/11/2014",[{"header":["uPlusFtp"]}]),
("SJSWS_ OiWS","http://www.oracle.com/technetwork/middleware/webtier/overview/index.html#iWS","9/11/2014",[{"header":["Oracle-iPlanet-Web-Server"]},{"header":["Sun-Java-System-Web-Server"]}]),
("SJSWPS_ OiWPS","http://www.oracle.com/technetwork/middleware/webtier/overview/index.html#iPS","9/11/2014",[{"header":["Sun-Java-System-Web-Proxy-Server"]},{"header":["Oracle-iPlanet-Proxy-Server"]}]),
("Blackboard","http://www.blackboard.com/Platforms/Learn/overview.aspx","9/11/2014",[{"header":["X-Blackboard-Product"]},{"header":["X-Blackboard-Appserver"]}]),
("Adblock","https://adblockplus.org","9/11/2014",[{"header":["X-Adblock-Key"]}]),
("Kooboocms","http://kooboo.com","9/11/2014",[{"header":["Kooboocms"]}]),
("安慧网盾","http://www.huianquan.com","9/11/2014",[{"header":["Protected-By: AnHui Web Firewall"]}]),
("plone","http://plone.org/","9/11/2014",[{"header":["plone.content"]},{"body":["generator\" content=\"Plone"]}]),
("ManagedFusion","http://managedfusion.com/products/url-rewriter/","9/11/2014",[{"header":["ManagedFusion"]}]),
("X-72e-Nobeian-Transfer","http://ipv6.google.com.hk/#q=%22X-72e-Nobeian-Transfe","9/11/2014",[{"header":["X-72e-Nobeian-Transfer"]}]),
("P3p_enabled","http://www.w3.org/P3P/","9/11/2014",[{"header":["P3p: CP"]}]),
("Oraclea-DMS","http://docs.oracle.com/cd/E21764_01/core.1111/e10108/dms.htm#ASPER295","9/11/2014",[{"header":["X-Oracle-Dms-Ecid"]}]),
("Powercdn","http://www.powercdn.com","9/11/2014",[{"header":["Powercdn"]}]),
("Iisexport","http://www.adsonline.co.uk/iisexport/documentation/","9/11/2014",[{"header":["Iisexport"]}]),
("DotNetNuke","http://www.dnnsoftware.com/","9/11/2014",[{"header":["DotNetNukeAnonymous"]},{"header":["Dnnoutputcache"]}]),
("Dnnoutputcache","http://www.dnnsoftware.com/","9/11/2014",[{"header":["Dnnoutputcache"]}]),
("rack-cache","http://rtomayko.github.io/rack-cache/","9/11/2014",[{"header":["X-Rack-Cache"]}]),
("wspx","http://ipv6.google.com.hk/search?q=%22X-Copyright:+wspx","9/11/2014",[{"header":["X-Copyright: wspx"]},{"header":["X-Powered-By: ANSI C"]}]),
("CodeIgniter","https://ellislab.com/codeigniter","9/11/2014",[{"header":["ci_session"]}]),
("CEMIS","http://www.reachway.com.cn/web/cemis/introduction.aspx","9/10/2014",[{"title":["综合项目管理系统登录"],"body":["<div id=\"demo\" style=\"overflow:hidden"]}]),
("云因网上书店","http://www.yunyin.com/product/product12.cfm?iType=12&sProName=%D4%C6%D2%F2%CD%F8%D5%BE%CF%B5%CD%B3","9/10/2014",[{"body":["main/building.cfm"]},{"body":["href=\"../css/newscomm.css"]}]),
("bit-service","http://www.bit-service.com/index.html","9/10/2014",[{"body":["bit-xxzs"]},{"body":["xmlpzs/webissue.asp"]}]),
("baidu广告联盟","http://yingxiao.baidu.com/support/adm/index.html","9/10/2014",[{"body":["http://cpro.baidu.com/cpro/ui/c.js"]},{"body":["http://cbjs.baidu.com/js/m.js"]}]),
("doubleclick_ad","http://www.google.com/doubleclick/","9/10/2014",[{"body":["ad.doubleclick.net"]}]),
("Acidcat_CMS","http://www.acidcat.com/","9/10/2014",[{"body":["Start Acidcat CMS footer information"]},{"body":["Powered by Acidcat CMS"]}]),
("ABO_CMS","http://www.abocms.com/","9/10/2014",[{"header":["a-powered-by"]}]),
("6kbbs","http://www.6kbbs.com","9/10/2014",[{"body":["Powered by 6kbbs"]},{"body":["generator\" content=\"6KBBS"]}]),
("3COM_NBX","http://inpath.com/products/3com-nbx.html","9/10/2014",[{"title":["NBX NetSet"]},{"body":["NBX"],"header":["Alternates"]}]),
("360webfacil_360WebManager","http://www.360webfacil.com","9/10/2014",[{"body":["publico/template/","zonapie"]},{"body":["360WebManager Software"]}]),
("1024cms","http://www.1024cms.com","9/10/2014",[{"body":["Powered by 1024 CMS"]},{"body":["generator\" content=\"1024 CMS (c)"]}]),
("MS-Author-Via","http://msdn.microsoft.com/en-us/library/cc250246.aspx","9/10/2014",[{"header":["MS-Author-Via"]}]),
("Aicache","http://aiscaler.com","9/10/2014",[{"header":["X-Aicache"]}]),
("Varnish","https://www.varnish-cache.org","9/10/2014",[{"header":["X-Varnish"]}]),
("sharepoint","http://microsoft.com/","9/10/2014",[{"header":["Microsoftsharepointteamservices"]},{"header":["X-Sharepointhealthscore"]}]),
("TCN协议","https://www.ietf.org/rfc/rfc2295.txt","9/10/2014",[{"header":["Tcn: choice"]},{"header":["Tcn: list"]}]),
("Aspnetmvc","http://www.asp.net/mvc","9/10/2014",[{"header":["Aspnetmvc"]}]),
("FrontPageServerExtension","http://microsoft.com/","9/10/2014",[{"header":["Microsoftofficewebserver"]}]),
("weidun","http://www.weidun.com.cn","9/10/2014",[{"header":["Firewall: www.weidun.com.cn"]}]),
("Swiftlet","http://swiftlet.org","9/9/2014",[{"header":["Swiftlet"]}]),
("webray","http://www.webray.com.cn/","9/9/2014",[{"header":["Rayengine"]},{"header":["Drivedby: RaySrv"]}]),
("we7","http://www.we7.cn","9/9/2014",[{"body":["/Widgets/WidgetCollection/"]}]),
("ASP","http://www.iis.net/","9/9/2014",[{"header":["X-Powered-By: ASP"]}]),
("nodejs","http://nodejs.org","9/9/2014",[{"header":["X-Powered-By: Express"]},{"header":["pump.io"]},{"header":["node.js"]}]),
("perl","http://www.perl.org","9/9/2014",[{"header":["perl"]}]),
("jsp","http://www.oracle.com/technetwork/java/javaee/jsp/index.html","9/9/2014",[{"header":["jsp"]},{"header":["Servlet"]},{"header":["JBoss"]},{"header":["JSESSIONID"]}]),
("ruby","http://rubyonrails.org","9/9/2014",[{"header":["ruby"]},{"header":["WEBrick"]},{"header":["Phusion"]},{"header":["Mongrel"]},{"header":["X-Rack-Cache"]}]),
("python","https://www.djangoproject.com","9/9/2014",[{"header":["python"]},{"header":["Django"]}]),
("ASP.NET","http://www.iis.net/","9/9/2014",[{"header":["X-Powered-By: ASP.NET"]}]),
("PHP","http://www.php.net","9/9/2014",[{"header":["X-Powered-By: PHP"]}]),
("awstats","http://www.awstats.org/","9/9/2014",[{"body":["awstats.pl?config="]}]),
("awstats_admin","http://www.awstats.org/","9/9/2014",[{"body":["generator\" content=\"AWStats"]},{"body":["<frame name=\"mainleft\" src=\"awstats.pl?config="]}]),
("awstats_misc_tracker","http://www.awstats.org","9/9/2014",[{"body":["/js/awstats_misc_tracker.js"]}]),
("easypanel","http://www.kanglesoft.com/forum.php?gid=50","9/9/2014",[{"body":["/vhost/view/default/style/login.css"]}]),
("kangle反向代理","http://www.kanglesoft.com","9/9/2014",[{"header":["kangle"]},{"title":["welcome use kangle"]}]),
("trs_wcm","http://www.trs.com.cn/product/product-wcm.html","9/4/2014",[{"body":["/wcm/app/js"]},{"body":["0;URL=/wcm"]},{"body":["window.location.href = \"/wcm\";"]},{"body":["forum.trs.com.cn","wcm"]},{"body":["/wcm\" target=\"_blank\">网站管理"]},{"body":["/wcm\" target=\"_blank\">管理"]}]),
("AD_RS设备","http://ipv6.google.com.hk/#newwindow=1&q=AD_RS_COOKIE","9/4/2014",[{"header":["AD_RS_COOKIE"]}]),
("万户ezOFFICE","http://www.whir.net/cn/ezofficeqyb/index_52.html","9/4/2014",[{"header":["LocLan"]}]),
("yui","http://yuilibrary.com","9/4/2014",[{"body":["yui.js"]},{"body":["yui.min.js"]}]),
("d3","http://mbostock.github.com/d3/","9/4/2014",[{"body":["/d3.min.js"]},{"body":["/d3.v2.min.js"]},{"body":["/d3.js"]},{"body":["/d3.v2.js"]}]),
("313自助建站","http://www.313.com.cn","9/4/2014",[{"header":["313CMS"]}]),
("F5_BIGIP","http://www.f5.com.cn","9/4/2014",[{"header":["BIGipServer"]},{"header":["X-WA-Info"]},{"header":["X-PvInfo"]}]),
("泛微协同办公OA","http://www.weaver.com.cn/products/enature_info.asp","9/3/2014",[{"header":["testBanCookie"]},{"body":["/wui/common/css/w7OVFont.css"]}]),
("juniper_vpn","http://www.juniper.net/cn/zh/products-services/","9/3/2014",[{"body":["welcome.cgi?p=logo"]}]),
("zabbix","http://www.zabbix.com","9/3/2014",[{"body":["images/general/zabbix.ico"]},{"header":["zbx_sessionid"]}]),
("GeoTrust_cert","http://www.geotrust.com","9/2/2014",[{"body":["//smarticon.geotrust.com/si.js"]}]),
("globalsign_cert","http://cn.globalsign.com","9/2/2014",[{"body":["//seal.globalsign.com/SiteSeal"]}]),
("webtrust_cert","https://cert.webtrust.org","9/2/2014",[{"body":["https://cert.webtrust.org/ViewSeal"]}]),
("wosign_ssl_cert","https://www.wosign.cn","9/2/2014",[{"body":["https://seal.wosign.com/tws.js"]},{"body":["https://seal.wosign.com/Signature"]}]),
("thawte_ssl_cert","https://www.thawte.com/ssl/index.html","9/2/2014",[{"body":["https://seal.thawte.com/getthawteseal"]}]),
("360网站安全检测","http://webscan.360.cn","9/1/2014",[{"body":["webscan.360.cn/status/pai/hash"]}]),
("Bugzilla","http://www.bugzilla.org","9/1/2014",[{"body":["enter_bug.cgi"]},{"body":["/cgi-bin/bugzilla/"]},{"header":["Bugzilla_login_request_cookie"]},{"title":["Bugzilla Main Page"]}]),
("o2security_vpn","http://www.o2security.net","9/1/2014",[{"header":["client_param=install_active"]}]),
("天融信防火墙","http://www.topsec.com.cn","9/1/2014",[{"body":["WEB User Interface"]},{"header":["TopWebServer"]}]),
("Array_Networks_VPN","http://www.arraynetworks.com","9/1/2014",[{"body":["an_util.js"]}]),
("天融信VPN","http://www.topsec.com.cn/aqcp/bjaq/xnzwvpn/ipsecvpnxlcp/index.htm","9/1/2014",[{"header":["TopWebServer"]},{"header":["topsecsvportalname"]}]),
("深信服ssl-vpn","http://www.sangfor.com.cn/product/ssl_vpn/outline.html","9/1/2014",[{"body":["login_psw.csp"]},{"header":["TWFID"]}]),
("exchange","http://office.microsoft.com/zh-cn/exchange/FX103765014.aspx","9/1/2014",[{"header":["owa"]},{"body":["owaLgnBdy"]},{"header":["OutlookSession"]}]),
("苏亚星校园管理系统","http://www.suyaxing.com/product.aspx","8/31/2014",[{"body":["/ws2004/Public/"]}]),
("gocdn","http://baidu.com/?q=gocdn","8/31/2014",[{"header":["GOCDN"]}]),
("zentao","http://www.zentao.net","8/31/2014",[{"body":["欢迎使用禅道集成运行环境"]},{"body":["powered by <a href='http://www.zentao.net' target='_blank'>ZenTaoPMS"]}]),
("西部数码","http://www.west263.com/","8/28/2014",[{"header":["WT263CDN"]}]),
("Webluker","http://www.webluker.com/","8/28/2014",[{"header":["Webluker-Edge"]}]),
("快网","http://www.fastweb.com.cn/","8/28/2014",[{"header":["Fw-Via: "]}]),
("帝联","http://www.dnion.com/","8/28/2014",[{"header":["Server: DNION"]},{"header":["fastcdn.com"]}]),
("网宿","http://www.chinanetcenter.com/","8/28/2014",[{"header":["Cdn Cache Server"]},{"header":["WS CDN Server"]}]),
("蓝讯","http://www.chinacache.com/","8/28/2014",[{"header":["Powered-By-ChinaCache"]}]),
("JBoss","http://www.jboss.org","8/28/2014",[{"header":["JBoss"]},{"body":["Manage this JBoss AS Instance"]}]),
("Oracle-Application-Server","http://www.oracle.com/technetwork/middleware/ias/overview/index.html","8/28/2014",[{"header":["Oracle-Application-Server"]}]),
("Sun-ONE-Web-Server","http://docs.oracle.com/cd/E19857-01/817-1831-10/agintro.html","8/28/2014",[{"header":["Sun-ONE-Web-Server"]}]),
("Jetty","http://www.eclipse.org/jetty","8/28/2014",[{"header":["Server: Jetty"]}]),
("webrick","https://rubygems.org/gems/webrick","8/28/2014",[{"header":["webrick"]}]),
("Phusion","https://www.phusionpassenger.com","8/28/2014",[{"header":["Phusion"]}]),
("Netscape-Enterprise","http://docs.oracle.com/cd/E19957-01/816-5648-10/es351jpg.html","8/28/2014",[{"header":["Netscape-Enterprise"]}]),
("Resin","http://caucho.com","8/28/2014",[{"header":["Server: Resin"]}]),
("Zeus","http://zeus.com","8/28/2014",[{"header":["Server: Zeus"]}]),
("ngx_openresty","http://openresty.org/cn/index.html","8/28/2014",[{"header":["ngx_openresty"]}]),
("Microsoft-HTTPAPI","http://www.microsoft.com","8/28/2014",[{"header":["Microsoft-HTTPAPI"]}]),
("LiteSpeed","http://litespeedtech.com/","8/28/2014",[{"header":["Server: LiteSpeed"]}]),
("GSE","https://code.google.com/p/opengse/","8/28/2014",[{"header":["Server: GSE"]}]),
("IBM_HTTP_Server","http://www-03.ibm.com/software/products/en/http-servers/","8/28/2014",[{"header":["IBM_HTTP_Server"]}]),
("Tengine","http://tengine.taobao.org","8/28/2014",[{"header":["Server: Tengine"]}]),
("Apache","http://www.apache.org","8/28/2014",[{"header":["Server: Apache"]}]),
("Apache-Tomcat","http://tomcat.apache.org","8/28/2014",[{"header":["Apache-Coyote"]},{"body":["<HR size=\"1\" noshade=\"noshade\"><p>"]}]),
("Nginx","http://nginx.org","8/28/2014",[{"header":["Server: nginx"]}]),
("IIS","http://www.iis.net/","8/28/2014",[{"header":["Microsoft-IIS"]},{"header":["X-Powered-By: WAF/2.0"]}]),
("Websecurity_WAF","http://ipv6.google.com.hk/#newwindow=1&q=%22Websecurity:+WAF+1.0%22&start=0","8/28/2014",[{"header":["Websecurity: WAF 1.0"]}]),
("安全狗","http://www.safedog.cn/","8/28/2014",[{"header":["WAF/2.0"]}]),
("wamp","http://www.wampserver.com/","8/28/2014",[{"title":["WAMPSERVER"]}]),
("DVR camera","http://www.dvrnet.org/","8/28/2014",[{"title":["DVR WebClient"]}]),
("UPUPW","http://www.upupw.net/","8/28/2014",[{"title":["UPUPW环境集成包"]}]),
("jcg无线路由器","http://www.jcgcn.com","8/28/2014",[{"title":["Wireless Router"],"body":["http://www.jcgcn.com"]}]),
("H3C","http://www.h3c.com.cn/","8/28/2014",[{"header":["H3C-Miniware-Webs"]},{"title":["Web user login"],"body":["nLanguageSupported"]}]),
("nvdvr","http://www.nvdvr.net/","8/28/2014",[{"title":["XWebPlay"]}]),
("LANMP一键安装包","http://www.wdlinux.cn/","8/28/2014",[{"title":["LANMP一键安装包"]}]),
("中兴路由器","http://www.zte.com.cn/","8/28/2014",[{"header":["Server: Mini web server 1.0 ZTE corp 2005."]}]),
("wdcp管理系统","http://www.wdlinux.cn/bbs/forum-3-1.html","8/28/2014",[{"title":["wdcp服务器"]},{"title":["lanmp_wdcp 安装成功"]}]),
("Hikvision","http://www.hikvision.com/","8/28/2014",[{"header":["Hikvision"]},{"header":["DVRDVS"]},{"header":["App-webs"]},{"header":["DNVRS"]}]),
("mikrotik","http://www.mikrotik.com/","8/28/2014",[{"title":["RouterOS"],"body":["mikrotik"]}]),
("imailserver","http://www.imailserver.com/","8/28/2014",[{"body":["myICalUserName"]},{"header":["Ipswitch-IMail"]}]),
("Redmine","http://www.redmine.org/","8/28/2014",[{"body":["Redmine","authenticity_token"]}]),
("易普拉格科研管理系统","http://www.e-plugger.com/","8/28/2014",[{"body":["lan12-jingbian-hong"]},{"body":["科研管理系统，北京易普拉格科技"]}]),
("360企业版","http://b.360.cn/","8/28/2014",[{"body":["360EntInst"]}]),
("NETSurveillance","http://www.fh-net.cn/product/class/?119.html","8/28/2014",[{"title":["NETSurveillance"]}]),
("ICEFLOW_VPN","http://www.iceflow.cn/","8/28/2014",[{"header":["Server: ICEFLOW"]}]),
("Vmware_vFabric","http://www.vmware.com/products/vfabric-tcserver/","8/28/2014",[{"title":["vFabric"]},{"header":["TS01efd1fa"]}]),
("phpinfo","http://www.php.net/","8/28/2014",[{"title":["phpinfo"],"body":["Virtual Directory Support"]}]),
("VisualSVN","http://www.visualsvn.com/server/","8/28/2014",[{"title":["VisualSVN Server"]}]),
("瑞友天翼_应用虚拟化系统","http://www.realor.cn/product/tianyi/","8/28/2014",[{"title":["瑞友天翼－应用虚拟化系统"]}]),
("金和协同管理平台","http://www.jinher.com/chan-pin-ti-xi/c6","8/28/2014",[{"title":["金和协同管理平台"]}]),
("EnterCRM","http://www.entersoft.cn/ProductView.asp?ID=23&SortID=131","8/28/2014",[{"body":["EnterCRM"]}]),
("oracle_applicaton_server","https://www.oracle.com/","8/28/2014",[{"body":["OraLightHeaderSub"]}]),
("huawei_auth_server","http://www.huawei.com/","8/28/2014",[{"body":["75718C9A-F029-11d1-A1AC-00C04FB6C223"]}]),
("锐捷NBR路由器","http://www.ruijie.com.cn/","8/28/2014",[{"body":["free_nbr_login_form.png"]}]),
("亿赛通DLP","http://www.esafenet.com/","8/28/2014",[{"body":["CDGServer3"]}]),
("百为路由","http://www.bytevalue.com/","8/28/2014",[{"body":["提交验证的id必须是ctl_submit"]}]),
("Incapsula","http://www.incapsula.com/","8/28/2014",[{"header":["X-Cdn: Incapsula"]}]),
("bxemail","http://www.bxemail.com","8/27/2014",[{"title":["百讯安全邮件系统"]},{"title":["百姓邮局"]},{"body":["请输入正确的电子邮件地址，如：abc@bxemail.com"]}]),
("万网企业云邮箱","http://mail.mxhichina.com/","8/27/2014",[{"body":["static.mxhichina.com/images/favicon.ico"]}]),
("magicwinmail","http://www.magicwinmail.com","8/27/2014",[{"header":["magicwinmail_default_theme"]}]),
("EasyTrace(botwave)","http://www.botwave.com/products/easytrace/solution.html","8/27/2014",[{"title":["EasyTrace"],"body":["login_page"]}]),
("WishOA","http://www.wishtech.com.cn","8/26/2014",[{"body":["WishOA_WebPlugin.js"]}]),
("78oa","http://www.78oa.com/","8/26/2014",[{"body":["/resource/javascript/system/runtime.min.js"]},{"body":["license.78oa.com"]}]),
("PHPOA","http://www.phpoa.cn","8/26/2014",[{"body":["admin_img/msg_bg.png"]}]),
("buscape","http://www.buscape.com.br","8/26/2014",[{"header":["sessao3"]}]),
("techbridge","http://www.techbridge-inc.com/","8/25/2014",[{"body":["Sorry,you need to use IE brower"]}]),
("ZendServer","http://www.zend.com/en/products/server","8/25/2014",[{"header":["ZendServer"]}]),
("Z-Blog","http://www.zblogcn.com/","8/25/2014",[{"body":["strBatchView","str00"]},{"body":["Powered By Z-Blog"]},{"body":["generator\" content=\"Z-Blog"]},{"header":["Product: Z-Blog"]}]),
("sdcms","http://www.sdcms.cn","8/23/2014",[{"title":["powered by sdcms"],"body":["var webroot=","/js/sdcms.js"]}]),
("disqus","http://www.disqus.com/","8/22/2014",[{"body":["disqus_thread"]}]),
("ujian","http://www.ujian.cc/","8/22/2014",[{"body":["ujian.cc/code/ujian.js"]}]),
("uyan","http://www.uyan.cc/","8/22/2014",[{"body":["uyan.cc/code/uyan.js"]}]),
("jiathis","http://jiathis.com/","8/22/2014",[{"body":["jiathis.com/code/jia.js"]}]),
("eaststorecreeator","http://www.easystorecreator.com/","8/22/2014",[{"header":["easystorecreator1"]}]),
("cloudflare","https://www.cloudflare.com/","8/21/2014",[{"header":["cloudflare-nginx"]}]),
("Telerik Sitefinity","http://www.sitefinity.com/","8/11/2014",[{"body":["Telerik.Web.UI.WebResource.axd"]},{"body":["content=\"Sitefinity"]}]),
("Liferay","http://www.liferay.com","8/11/2014",[{"header":["Liferay-Portal"]}]),
("iAPPS","http://www.iapps.com/products/iapps-content-manager","8/11/2014",[{"header":["iAPPSCookie"]}]),
("ExpressionEngine","https://ellislab.com/expressionengine/","8/11/2014",[{"header":["exp_tracker"]}]),
("Parallels Plesk Panel","http://www.parallels.com/products/plesk/","8/11/2014",[{"body":["Parallels IP Holdings GmbH"]}]),
("Plesk","http://sp.parallels.com/products/plesk/","8/11/2014",[{"header":["PleskLin"]}]),
("Tumblr","https://www.tumblr.com/","8/11/2014",[{"header":["X-Tumblr-User"]}]),
("Dolibarr","http://www.dolibarr.org/","8/11/2014",[{"body":["Dolibarr Development Team"]}]),
("TurboMail","http://www.turbomail.org/","8/1/2014",[{"body":["Powered by TurboMail"]},{"body":["wzcon1 clearfix"]},{"title":["TurboMail邮件系统"]}]),
("GPSweb","http://ipv6.google.com.hk/#newwindow=1&q=GPSweb","8/1/2014",[{"title":["GPSweb"]}]),
("Polycom","http://support.polycom.com/PolycomService/support/us/support/video/index.html","7/31/2014",[{"title":["Polycom"],"body":["kAllowDirectHTMLFileAccess"]}]),
("360主机卫士","http://webscan.360.cn/guard/","7/30/2014",[{"header":["X-Safe-Firewall"]}]),
("一启快","http://www.yiqikuai.com/","7/30/2014",[{"header":["yiqikuai.com"]}]),
("主机宝","http://z.admin5.com/","7/30/2014",[{"body":["您访问的是主机宝服务器默认页"]}]),
("srun3000计费认证系统","http://www.srun.com/","7/29/2014",[{"title":["srun3000"]}]),
("网易企业邮箱","http://qiye.163.com/","7/29/2014",[{"title":["邮箱用户登录"],"body":["frmvalidator"]}]),
("pmway_E4_crm","http://www.pmway.com/","7/29/2014",[{"title":["E4","CRM"]}]),
("NetShare_VPN","http://www.zkvpn.com/","7/29/2014",[{"title":["NetShare","VPN"]}]),
("AVCON6","http://www.epross.com/","7/29/2014",[{"title":["AVCON6"]},{"body":["language_dispose.action"]}]),
("SonicWALL","http://www.sonicwall.com/","7/28/2014",[{"header":["Server: SonicWALL"]}]),
("亿邮","http://eyou.net/","7/28/2014",[{"body":["EYOU企业邮箱"]},{"header":["eYouWS"]},{"body":["cr\">eYouMail"]},{"header":["EMPHPSID"]}]),
("MVB2000","http://www.mvb2000.cn","7/28/2014",[{"title":["MVB2000"]},{"body":["The Magic Voice Box"]}]),
("dd-wrt","http://www.dd-wrt.com/","7/28/2014",[{"body":["dd-wrt.com","load average"]}]),
("Sun[tm]","http://www.oracle.com/us/sun/index.htm","7/28/2014",[{"title":["Sun[tm] ONE Web Server"]},{"header":["Server: Sun-ONE-Web-Server"]}]),
("edvr","http://ipv6.google.com.hk/#newwindow=1&q=EDVS+edvr","7/28/2014",[{"title":["edvs/edvr"]}]),
("iDVR","http://ipv6.google.com.hk/#newwindow=1&q=idvr","7/28/2014",[{"header":["Server: iDVRhttpSvr"]}]),
("EdmWebVideo","http://www.baidu.com/s?wd=EdmWebVideo","7/28/2014",[{"title":["EdmWebVideo"]}]),
("webplus","http://www.sudytech.com/","7/28/2014",[{"body":["webplus","高校网站群管理平台"]}]),
("LuManager","http://www.zijidelu.org/","7/28/2014",[{"title":["LuManager"]}]),
("管理易","http://www.ekingcn.com/","7/25/2014",[{"body":["管理易","minierp"]}]),
("Coremail","http://www.coremail.cn/","7/25/2014",[{"title":["/coremail/common/assets"]},{"title":["Coremail邮件系统"]},{"body":["coremail/common/"]}]),
("用友erp-nc","http://www.yonyou.com/product/NC.aspx","7/24/2014",[{"body":["/nc/servlet/nc.ui.iufo.login.Index"]},{"title":["用友新世纪"]}]),
("supesite","http://www.comsenz.com/downloads/install/supesite/","7/23/2014",[{"header":["supe_sid"]}]),
("同城多用户商城","http://www.anxin66.com/","7/23/2014",[{"body":["style_chaoshi"]}]),
("DIYWAP","http://www.diywap.cn/","7/23/2014",[{"body":["web980","bannerNum"]}]),
("TCCMS","http://www.teamcen.com/","7/23/2014",[{"title":["Power By TCCMS"]},{"body":["index.php?ac=link_more","index.php?ac=news_list"]}]),
("Shop7Z","http://www.shop7z.com/","7/22/2014",[{"header":["sitekeyword"]},{"body":["productlist.asp","headlist"]}]),
("IdeaCMS","http://www.ideacms.net/","7/22/2014",[{"body":["Powered By IdeaCMS"]},{"body":["m_ctr32"]}]),
("emlog","http://www.emlog.net/","7/22/2014",[{"body":["content=\"emlog\""]}]),
("phpshe","http://www.phpshe.com","7/16/2014",[{"body":["phpshe"]}]),
("华天动力OA(OA8000)","http://www.oa8000.com","7/16/2014",[{"body":["/OAapp/WebObjects/OAapp.woa"]}]),
("ThinkSAAS","http://www.thinksaas.cn","7/16/2014",[{"body":["/app/home/skins/default/style.css"]}]),
("e-tiller","http://www.e-tiller.com","7/16/2014",[{"body":["reader/view_abstract.aspx"]}]),
("mongodb","http://www.mongodb.org","7/11/2014",[{"body":["<a href=\"/_replSet\">Replica set status</a></p>"]}]),
("易瑞授权访问系统","http://www.infcn.com.cn/iras/752.jhtml","7/9/2014",[{"body":["/authjsp/login.jsp"]},{"body":["FE0174BB-F093-42AF-AB20-7EC621D10488"]}]),
("fangmail","http://www.fangmail.net/","7/9/2014",[{"body":["/fangmail/default/css/em_css.css"]}]),
("腾讯企业邮箱","http://exmail.qq.com/","7/9/2014",[{"body":["/cgi-bin/getinvestigate?flowid="]}]),
("通达OA","http://www.tongda2000.com/","7/9/2014",[{"body":["<link rel=\"shortcut icon\" href=\"/images/tongda.ico\" />"]},{"body":["OA提示：不能登录OA","紧急通知：今日10点停电"]},{"body":["Office Anywhere 2013"]}]),
("jira","https://www.atlassian.com/software/jira","7/8/2014",[{"body":["jira.webresources"]},{"header":["atlassian.xsrf.token"]},{"body":["ams-build-number"]},{"body":["com.atlassian.plugins"]}]),
("fisheye","https://www.atlassian.com/software/fisheye/overview","7/8/2014",[{"header":["Set-Cookie: FESESSIONID"]},{"body":["fisheye-16.ico"]}]),
("elasticsearch","http://www.elasticsearch.org/","7/7/2014",[{"body":["You Know, for Search"]},{"header":["application/json"],"body":["build_hash"]}]),
("MDaemon","http://www.altn.com/Products/MDaemon-Email-Server-Windows/","7/7/2014",[{"body":["/WorldClient.dll?View=Main"]}]),
("ThinkPHP","http://www.thinkphp.cn","7/3/2014",[{"header":["thinkphp"]},{"header":["think_template"]}]),
("OA(a8/seeyon/ufida)","http://yongyougd.com/productsview88.html","7/1/2014",[{"body":["/seeyon/USER-DATA/IMAGES/LOGIN/login.gif"]}]),
("yongyoufe","http://yongyougd.com/productsview88.html","7/1/2014",[{"title":["FE协作"]},{"body":["V_show","V_hedden"]}]),
("Zen Cart","http://www.zen-cart.com/","12/18/2013",[{"body":["shopping cart program by Zen Cart"]},{"header":["Set-Cookie: zenid="]}]),
("iWebShop","http://www.jooyea.cn/","12/18/2013",[{"body":["Powered by","iWebShop"]},{"header":["iweb_safecode"]},{"body":["/runtime/default/systemjs"]}]),
("DouPHP","http://www.douco.com/","12/18/2013",[{"body":["Powered by DouPHP"]},{"body":["controlBase","indexLeft","recommendProduct"]}]),
("twcms","http://www.twcms.cn/","12/18/2013",[{"body":["/twcms/theme/","/css/global.css"]}]),
("Cicro","http://www.cicro.com/","12/3/2013",[{"body":["Cicro","CWS"]},{"body":["content=\"Cicro"]},{"body":["index.files/cicro_userdefine.css"]},{"body":["structure/index","window.location.href="]}]),
("SiteServer","http://www.siteserver.cn/","11/29/2013",[{"body":["Powered by","http://www.siteserver.cn","SiteServer CMS"]},{"title":["Powered by SiteServer CMS"]},{"body":["T_系统首页模板"]},{"body":["siteserver","sitefiles"]}]),
("Joomla","http://www.Joomla.org","11/28/2013",[{"body":["content=\"Joomla"]},{"body":["/media/system/js/core.js","/media/system/js/mootools-core.js"]}]),
("phpbb","http://www.phpbb.com/","11/28/2013",[{"header":["Set-Cookie: phpbb3_"]},{"header":["HttpOnly, phpbb3_"]},{"body":["&copy;","http://www.longluntan.com/zh/phpbb/","phpBB"]},{"body":["phpBB Group\" /\>"]},{"body":["START QUICK HACK - phpBB Statistics MOD"]}]),
("HDWiki","http://kaiyuan.hudong.com/","11/26/2013",[{"title":["powered by hdwiki!"]},{"body":["content=\"HDWiki"]},{"body":["http://kaiyuan.hudong.com?hf=hdwiki_copyright_kaiyuan"]},{"header":["hd_sid="]}]),
("kesionCMS","http://www.kesion.com/","11/25/2013",[{"body":["/ks_inc/common.js"]},{"body":["publish by KesionCMS"]}]),
("CMSTop","http://www.cmstop.com/","11/23/2013",[{"body":["/css/cmstop-common.css"]},{"body":["/js/cmstop-common.js"]},{"body":["cmstop-list-text.css"]},{"body":["<a class=\"poweredby\" href=\"http://www.cmstop.com\""]}]),
("ESPCMS","http://www.ecisp.cn/","11/23/2013",[{"title":["Powered by ESPCMS"]},{"body":["Powered by ESPCMS"]},{"body":["infolist_fff","/templates/default/style/tempates_div.css"]}]),
("74cms","http://www.74cms.com/","11/23/2013",[{"body":["content=\"74cms.com"]},{"body":["content=\"骑士CMS"]},{"body":["Powered by <a href=\"http://www.74cms.com/\""]},{"body":["/templates/default/css/common.css","selectjobscategory"]}]),
("Foosun","http://www.foosun.net/","11/21/2013",[{"body":["Created by DotNetCMS"]},{"body":["For Foosun"]},{"body":["Powered by www.Foosun.net,Products:Foosun Content Manage system"]}]),
("PhpCMS","http://www.phpcms.com/","11/21/2013",[{"body":["Powered by","http://www.phpcms.cn"]},{"body":["content=\"Phpcms"]},{"body":["Powered by","phpcms"]}]),
("Hanweb","http://www.hanweb.com/","11/21/2013",[{"body":["Produced By 大汉网络"]},{"body":["/jcms_files/jcms"]},{"body":["<meta name='Author' content='大汉网络'>"]},{"body":["<meta name='Generator' content='大汉版通'>"]},{"body":["<a href='http://www.hanweb.com' style='display:none'>"]}]),
("Drupal","http://www.drupal.org/","11/21/2013",[{"header":["X-Generator: Drupal"]},{"body":["content=\"Drupal"]},{"body":["jQuery.extend(Drupal.settings"]},{"body":["/sites/default/files/","content=\"/sites/all/modules/","/sites/all/themes/"]}]),
("phpwind","http://www.phpwind.net/","11/19/2013",[{"title":["Powered by phpwind"]},{"body":["content=\"phpwind"]}]),
("Discuz","http://www.discuz.net/","11/19/2013",[{"title":["Powered by Discuz"]},{"body":["content=\"Discuz"]},{"body":["discuz_uid","portal.php?mod=view"]},{"body":["Powered by <strong><a href=\"http://www.discuz.net"]}]),
("vBulletin","http://www.vBulletin.com/","11/19/2013",[{"title":["Powered by vBulletin"],"body":["content=\"vBulletin"]},{"header":["bbsessionhash","bblastvisit"]},{"body":["Powered by vBulletin&trade;"]}]),
("cmseasy","http://www.cmseasy.cn/","11/19/2013",[{"title":["Powered by CmsEasy"]},{"header":["http://www.cmseasy.cn/service_1.html"]},{"body":["content=\"CmsEasy"]}]),
("wordpress","http://www.wordpress.com/","11/19/2013",[{"body":["content=\"WordPress"]},{"header":["X-Pingback","/xmlrpc.php"],"body":["/wp-includes/"]}]),
("DedeCMS","http://www.dedecms.com/","11/19/2013",[{"body":["Power by DedeCms"]},{"body":["Powered by","http://www.dedecms.com/","DedeCMS"]},{"body":["/templets/default/style/dedecms.css"]}]),
("ASPCMS","http://www.aspcms.com/","11/19/2013",[{"title":["Powered by ASPCMS"]},{"body":["content=\"ASPCMS"]},{"body":["/inc/AspCms_AdvJs.asp"]}]),
("MetInfo","http://www.metinfo.com/","11/19/2013",[{"title":["Powered by MetInfo"]},{"body":["content=\"MetInfo"]},{"body":["powered_by_metinfo"]},{"body":["/images/css/metinfo.css"]}]),
("PageAdmin","http://www.pageadmin.net/","11/19/2013",[{"title":["Powered by PageAdmin"]},{"body":["content=\"PageAdmin"]},{"body":["Powered by <a href='http://www.pageadmin.net'"]},{"body":["/e/images/favicon.ico"]}]),
("Npoint","http://www.npointhost.com/","11/19/2013",[{"title":["Powered by Npoint"]}]),
("小蚂蚁","http://www.xiaomayi.co/","11/19/2013",[{"title":["Powered by 小蚂蚁地方门户网站系统"]},{"header":["AntXiaouserslogin"]},{"body":["/Template/Ant/Css/AntHomeComm.css"]}]),
("捷点JCMS","http://www.jcms.com.cn/","11/19/2013",[{"body":["Publish By JCms2010"]}]),
("帝国CMS","http://www.phome.net/","11/19/2013",[{"title":["Powered by EmpireCMS"]},{"body":["/skin/default/js/tabs.js"]},{"body":["/e/member/login/loginjs.php"]}]),
("phpMyadmin","http://www.phpmyadmin.net/","11/19/2013",[{"header":["Set-Cookie: phpMyAdmin="]},{"title":["phpMyAdmin "]},{"body":["pma_password"]}]),
("JEECMS","http://www.jeecms.com/","11/19/2013",[{"title":["Powered by JEECMS"]},{"body":["Powered by","http://www.jeecms.com","JEECMS"]},{"body":["/r/cms/www/","jhtml"]}]),
("IdeaWebServer","#","6/4/2015 00:37:30",[{"header":["IdeaWebServer"]}]),
("Struts2","http://struts.apache.org/","6/4/2015",[{"header":["JSESSIONID"],"body":[".action"]},{"body":["Struts Problem Report"]},{"body":["There is no Action mapped for namespace"]},{"body":["No result defined for action and result input"]}]),
("AXIS 2120网络摄像头","http://www.axis.com/cn/zh-hans/products/axis-2120","6/8/2015 16:13:02",[{"title":["AXIS 2120 Network Camera"]}]),
("东方通中间件","http://www.tongtech.com/","6/12/2015",[{"header":["TongWeb Server"]}]),
("金蝶中间件Apusic","http://www.apusic.com/","6/12/2015",[{"header":["Apusic"]}]),
("Ektron","http://www.ektron.com", "21/12/2015", [{"body":["id=\"Ektron"]}]),
#("JQuery","http://jquery.com/","8/21/2014",[{"body":["jquery"]}]),
#("JQuery-UI","http://jqueryui.com","9/4/2014",[{"body":["jquery-ui"]}]),
#("bootstrap","http://getbootstrap.com/","8/21/2014",[{"body":["bootstrap.css"]},{"body":["bootstrap.min.css"]}]),
#("google-analytics","http://www.google.com/analytics/","8/21/2014",[{"body":["google-analytics.com/ga.js"]},{"body":["google-analytics.com/analytics.js"]}]),
#("__VIEWSTATE","http://msdn.microsoft.com/en-us/library/ms972976.aspx","10/4/2014",[{"body":["__VIEWSTATE"]}]),
#("Angularjs","http://www.angularjs.org/","6/6/2015",[{"body":["angularjs"]}]),
#("sogou站长平台","http://zhanzhang.sogou.com/","8/22/2014",[{"body":["sogou_site_verification"]}]),
#("51la","http://www.51.la/","8/22/2014",[{"body":["js.users.51.la"]}]),
#("baidu统计","http://tongji.baidu.com/","8/22/2014",[{"body":["hm.baidu.com/h.js"]}]),
#("baidu站长平台","http://zhanzhang.baidu.com/?castk=LTE%3D","8/22/2014",[{"body":["baidu-site-verification"]}]),
#("360站长平台","http://zhanzhang.so.com/","8/22/2014",[{"body":["360-site-verification"]}]),
#("百度分享","http://share.baidu.com/","8/22/2014",[{"body":["share.baidu.com/static/api/js/share.js"]}]),
#("squid","http://www.squid-cache.org/","8/28/2014",[{"header":["squid"]}]),
#("CNZZ统计","http://cnzz.com","8/28/2014",[{"body":["cnzz.com/stat.php?id="]}]),
#("安全宝","http://www.anquanbao.com/","8/28/2014",[{"header":["X-Powered-By-Anquanbao"]}]),
#("360网站卫士","http://wangzhan.360.cn/","8/28/2014",[{"header":["360wzb"]}]),
#("mod_wsgi","http://code.google.com/p/modwsgi","10/8/2014",[{"header":["mod_wsgi"]}]),
#("mod_ssl","http://modssl.org","10/8/2014",[{"header":["mod_ssl"]}]),
#("mod_rails","http://phusionpassenger.com","10/8/2014",[{"header":["mod_rails"]}]),
#("mod_rack","http://phusionpassenger.com","10/8/2014",[{"header":["mod_rack"]}]),
#("mod_python","http://www.modpython.org","10/8/2014",[{"header":["mod_python"]}]),
#("mod_perl","http://perl.apache.org","10/8/2014",[{"header":["mod_perl"]}]),
#("mod_jk","http://tomcat.apache.org/tomcat-3.3-doc/mod_jk-howto.html","10/8/2014",[{"header":["mod_jk"]}]),
#("mod_fastcgi","http://www.fastcgi.com/mod_fastcgi/docs/mod_fastcgi.html","10/8/2014",[{"header":["mod_fastcgi"]}]),
#("mod_auth_pam","http://pam.sourceforge.net/mod_auth_pam","10/8/2014",[{"header":["mod_auth_pam"]}]),
#("百度云加速","http://yunjiasu.baidu.com/","8/28/2014",[{"header":["X-Server","fhl"]}]),
#("加速乐","http://www.jiasule.com/","8/28/2014",[{"header":["__jsluid"]}]),
]

cmsver = {
"wordpress":('/', r'<meta\s*name="generator"\s*content="WordPress\s*([\d\.]*)"\s/>'),
"Drupal":('/CHANGELOG.txt', r'Drupal ([\d]+.[\d]+[.[\d]+]*, [\d]{4}-[\d]{2}-[\d]{2})'),
"Joomla":('/modules/mod_login/mod_login.xml', r'<version>(.+)</version>'),
"IIS":('/', r'Microsoft-IIS/([\d\.]+)'),
"Privoxy":('/', r'Privoxy\s*([\w\.]+)'),
"ExtMail":('/', r'ExtMail\s*Pro\s*([\w\.]+)'),
"GlassFish":('/', r':\s*GlassFish\s*Server\s*Open\s*Source\s*Edition\s\s*([\w\.]+)'),
"qibosoft":('/', r'>qibosoft\s*([\w\.]+)'),
"UcSTAR":('/', r'">\S(V.*)</'),
"FineCMS":('/', r'FineCMS\s*([\w\.]+)"\s*>'),
"Maticsoft_Shop_动软商城":('/', r'Maticsoft\s*Shop\s*([\w\.]+)'),
"hishop":('/', r'Hishop:\s*([\w\.]+)'),
"Tipask":('/', r'"generator"\s*content="Tipask\s*([\w\.]+)'),
"地平线CMS":('/', r'Powered\s*by\s*deepsoon\s*cms\s*version\s*([\w\.]+)\s'),
"BoyowCMS":('/', r'BoyowCMS\s*([\w\.]+)'),
"mod_python":('/', r'\s*mod_python\s*/([\w\.]+)\s'),
"mod_perl/1.22":('/', r'mod_perl/([\w\.]+)'),
"mod_jk":('/', r'mod_jk/([\w\.]+)'),
"mod_fastcgi":('/', r'mod_perl/([\w\.]+)'),
"mod_auth_pam":('/', r'mod_auth_pam/([\w\.]+)'),
"Communique":('/', r'Communique/([\w\.]+)'),
"Z-BlogPHP":('/', r'Z-BlogPHP\s*([\w\.]+)'),
"护卫神网站安全系统":('/', r'<title>护卫神.网站安全系统(V.*)</title>'),
"Allegro-Software-RomPager":('/', r'Allegro-Software-RomPager/([\w\.]+)'),
"HFS":('/', r'Server:\s*HFS\s*(.*?)beta'),
"ecshop":('/', r'ECSHOP\s*(.*?)\s*/>'),
"gunicorn":('/', r'gunicorn/([\w\.]*)'),
"WebKnight":('/', r'WebKnight/([\w\.]*)'),
"FortiWeb":('/', r'FortiWeb-([\w\.]*)'),
"Mod_Security":('/', r'Mod_Security\s*([\w\.]*)'),
"DnP Firewall":('/', r'DnP\s*Firewall.*\s*([\w\.]+).*copy'),
"AnZuWAF":('/', r'AnZuWAF/([\w\.]+)'),
"Safe3WAF":('/', r'Safe3WAF/([\w\.]+)'),
"mod_auth_passthrough":('/', r'mod_auth_passthrough/([\w\.]+)'),
"mod_bwlimited":('/', r'mod_bwlimited/([\w\.]+)'),
"OpenSSL":('/', r'OpenSSL/([\w\.]+)'),
"Alternate-Protocol":('/', r'Alternate-Protocol:\s*npn-spdy/([\w\.]+)'),
"pagespeed":('/', r'X-Mod-Pagespeed:\s*([\w\.]+)'),
"Cocoon":('/', r'X-Cocoon-Version:\s*([\w\.]+)'),
"Kooboocms":('/', r'X-KoobooCMS-Version:\s*([\w\.]+)'),
"plone":('/', r'Plone/([\w\.]+)'),
"Powercdn":('/', r'PowerCDN/([\w\.]+)\s*'),
"Iisexport":('/', r'IIS\s*Export\s*([\w\.]+) '),
"DotNetNuke":('/', r'DotNetNuke\s*Error:\s*-\s*Version(.*)</'),
"Aspnetmvc":('/', r'X-AspNetMvc-Version:\s*([\w\.]+)'),
"perl":('/', r'Perl/([\w\.]+)\s*'),
"jsp":('/', r'JSP/([\w\.]+)\s*'),
"ruby":('/', r'Ruby/([\w\.]+)\s*'),
"python":('/', r'Python/([\w\.]+)\s*'),
"PHP":('/', r'PHP/([\w\.]+)\s*'),
"JQuery-UI":('/', r'jquery-ui-([\w\.]+)\s*'),
"zabbix":('/', r'\s*Zabbix\s*([\w\.]+)*\sCopyright'),
"JBoss":('/', r'JBoss-([\w\.]+)'),
"Oracle-Application-Server":('/', r':\s*Oracle-Application-Server-10g/([\w\.]+)'),
"Jetty":('/', r'Jetty/([\w\.]+)'),
"webrick":('/', r'WEBrick/([\w\.]+)'),
"Phusion":('/', r'Phusion\s*Passenger\s*([\w\.]+)'),
"Netscape-Enterprise":('/', r':\s*Netscape-Enterprise/([\w\.]+)'),
"Resin":('/', r'Resin/([\w\.]+)'),
"Zeus":('/', r'Zeus/([\w\.]+)'),
"ngx_openresty":('/', r'ngx_openresty/([\w\.]+)'),
"Microsoft-HTTPAPI":('/', r''),
"Tengine":('/', r'Tengine/([\w\.]+)'),
"Apache":('/', r'Apache/([\w\.]+)'),
"Apache-Tomcat":('/', r'Apache-Coyote/([\w\.]+)'),
"Nginx":('/', r'Nginx/([\w\.]+)'),
"squid":('/', r':\s*squid/([\w\.]+)'),
"ZendServer":('/', r'ZendServer/([\w\.]+)'),
"Z-Blog":('/', r'Z-Blog\s*([\w\.]+)'),
"Liferay":('/', r''),
"fisheye":('/', r'>FishEye\s*([\w\.]+)'),
"MDaemon":('/', r'MDaemon\s*([\w\.]+)'),
"DouPHP":('/', r'DouPHP\s*([\w\.]+)'),
"HDWiki":('/', r'="*HDWiki\s*([\w\.]+)"'),
"ESPCMS":('/', r'Powered\s*by\s*ESPCMS\s*([\w\.]+)'),
"Discuz":('/', r'>Discuz!</a></strong>\s*<em>([\w\.]+)</em></p>'),
"vBulletin":('/', r'="\s*vBulletin\s*([\w\.]+)"\s*/>'),
"cmseasy":('/', r'"Generator"\s*content="CmsEasy\s*([\w\.]+)"\s*/>'),
"ASPCMS":('/', r'content="ASPCMS!\s*([\w\.]+)"\s*'),
"MetInfo":('/', r'MetInfo</b></a>\s*([\w\.]+)'),
"IdeaWebServer":('/', r'Server:\s*IdeaWebServer/([\w\.]+)'),
"金蝶中间件Apusic":('/', r'<TITLE>Apusic\s*Application\s*Server/([\w\.]+)'),
"天柏在线培训/考试系统":('/Login.aspx', r'KSXTQYB-V(.*)</span>'),
"openEAP":('/security/login/login.jsp', r'<p.*(open.*?)</'),
"phpwind":('/robots.txt', r'Version\s*([\w\.]+)'),
"DedeCMS":('/data/admin/ver.txt', r'(.*)'),
"Ektron":('/Workarea/version.xml', r'<CMS400 DATE="[\d\-]+">([\w\.]+)</CMS400>\s*</installation>'),
}

class Cmsfinger(Tasker):
    id = 0
    lock = threading.RLock()
    
    def __init__(self, resource):
        Tasker.__init__(self, resource)
        
    def taskprocesser(self, task):
        Cmsfinger.lock.acquire()
        Cmsfinger.id = Cmsfinger.id + 1
        Cmsfinger.lock.release()
        req = HttpSession()
        if not req.Get(task):
            return
        result = {}
        headers = str(req.headers)
        for line in fingers:
            allfingers = line[3]
            for onefinger in allfingers:
                bMatch = True
                for key in onefinger:
                    if key == 'header':
                        for r in onefinger[key]:
                            if headers.find(r) < 0:
                                bMatch = False
                                break
                        if not bMatch:
                            break
                    if not bMatch:
                        break
                    if key == 'title' or key == 'body':
                        for r in onefinger[key]:
                            if req.html.find(r) < 0:
                                bMatch = False
                                break
                        if not bMatch:
                                break
                    if not bMatch:
                        break
                if bMatch:
                    result[line[0]] = ''
                    break
        for cms in result:
            if cms in cmsver:
                if cmsver[cms][0] == '/':
                    m = re.search(cmsver[cms][1], req.html)
                    if not m:
                        m = re.search(cmsver[cms][1], headers)
                    result[cms] = m.group(1) if m else 'unkown'
                else:
                    tmpreq = HttpSession(task.strip('/')+cmsver[cms][0])
                    if tmpreq.Get():
                        m = re.search(cmsver[cms][1], tmpreq.html)
                        if not m:
                            m = re.search(cmsver[cms][1], str(tmpreq.headers))
                        result[cms] = m.group(1) if m else 'unkown'
        if len(result) == 0:
            Log.file('"unkown","%s"' % task, Log.YELLOW)
        else:
            Log.file('"%s","%s"' % (task, result))
        
    def resolvetask(self, task):
        if task[0:4] != 'http':
            return ['http://'+task]
        else:
            return [task]
              
        
def help():
    print('this.py www.baidu.com')
    print('this.py -r domainlist.txt')
    
if __name__ == "__main__":
    Log.INIT()
    Log.FILE = sys.path[0]+'\\cms-finger-log.txt'
    if len(sys.argv) == 1:
        help()
    elif len(sys.argv) == 2:
        b = Cmsfinger([sys.argv[1]])
        b.run()
    elif len(sys.argv) == 3 and sys.argv[1] == '-r':
        b = Cmsfinger(sys.argv[2])
        b.run()
    else:
        help()
    
    