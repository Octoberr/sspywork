"""
create by judy
2019/08/06
这个文件是为了以后准备的，
在编写了专门的数据存储以后可能才会用到这个文件的接口
update by judy 2019/08/14
"""
import uuid
import threading
from abc import abstractmethod

from commonbaby.mslog import MsLogger, MsLogManager

from idownclient.clientdbmanager import DbManager
from idownclient.config_task import clienttaskconfig
from jsonoutputer import Outputjtf


class AutoPluginBase(object):

    def __init__(self):
        self._sqlfunc = DbManager
        self._logger: MsLogger = MsLogManager.get_logger('AutoPlugin')
        self.tmppath = clienttaskconfig.tmppath
        self.outpath = clienttaskconfig.outputpath

        # 文件锁
        self.file_locker = threading.RLock()

    def write_text(self, tx, suffix):
        """
        输出特定的文件数据，需要后缀
        这里是编写输出text,现在懒得写，
        现在是无论直接传入字符串和string都可以
        :param suffix:
        :param tx:
        :return:
        """
        outname = Outputjtf.output_json_to_file(tx, self.tmppath, self.outpath, suffix)
        self._logger.info(f"Output data success, filename:{outname}")
        return outname

    def write_text_binary(self, description: str, sourcedata, suffix):
        """
        输出带文件体的数据，需要后缀
        这里是输出带文件体的数据，需要写两次，一次是
        将数据写入文件，再然后是写入二进制数据
        :param suffix:
        :param sourcedata:
        :param description:
        :return:
        """
        # --------------------------------------------tmppath
        tmpname = self.tmppath / f'{uuid.uuid1()}.{suffix}'
        while tmpname.exists():
            tmpname = self.tmppath / f'{uuid.uuid1()}.{suffix}'
        with tmpname.open('a', encoding='utf-8') as tf:
            tf.write(description)
            tf.write('\n')
        with tmpname.open('ab+') as tf:
            tf.write(sourcedata)

        # ------------------------------------------outputpath
        outname = self.outpath / f'{uuid.uuid1()}.{suffix}'
        while outname.exists():
            outname = self.outpath / f'{uuid.uuid1()}.{suffix}'
        # 将tmppath 移动到outputpath
        tmpname.replace(outname)
        return outname.name

    def write_text_string(self, description: str, sourcedata, suffix):
        """
        输出带文件体的数据，需要后缀
        这里是输出带文件体的数据，需要写两次，一次是
        将数据写入文件，再然后是写入二进制数据
        :param suffix:
        :param sourcedata:
        :param description:
        :return:
        """
        # --------------------------------------------tmppath
        tmpname = self.tmppath / f'{uuid.uuid1()}.{suffix}'
        while tmpname.exists():
            tmpname = self.tmppath / f'{uuid.uuid1()}.{suffix}'
        with tmpname.open('a', encoding='utf-8') as tf:
            tf.write(description)
            tf.write('\n')
        with tmpname.open('a') as tf:
            tf.write(sourcedata)

        # ------------------------------------------outputpath
        outname = self.outpath / f'{uuid.uuid1()}.{suffix}'
        while outname.exists():
            outname = self.outpath / f'{uuid.uuid1()}.{suffix}'
        # 将tmppath 移动到outputpath
        tmpname.replace(outname)
        return outname.name

    def is_expdbdata_unique(self, data):
        """
        数据量太TM大了单独存
        expdb
        这里是查询数据服务器上的数据是否已经是下载过的
        目的：1、增量下载；2、分布式下载
        是否为重复数据
        重复->True
        不重复->false
        :param data:
        :return:
        """
        res = self._sqlfunc.is_expdbdata_duplicate(data)
        return res

    def store_expdbdata_unique(self, data):
        """
        数据量太TM大了单独存
        expdb
        存储数据的唯一标识，为了增量下载和分布式下载
        :param data:
        :return:
        """
        res = self._sqlfunc.save_expdbdata_identification(data)
        return res

    def is_geodata_unique(self, data):
        """
        数据量太TM大了单独存
        geoname
        这里是查询数据服务器上的数据是否已经是下载过的
        目的：1、增量下载；2、分布式下载
        是否为重复数据
        重复->True
        不重复->false
        :param data:
        :return:
        """
        res = self._sqlfunc.is_geodata_duplicate(data)
        return res

    def store_geodata_unique(self, data):
        """
        数据量太TM大了单独存
        geoname
        存储数据的唯一标识，为了增量下载和分布式下载
        :param data:
        :return:
        """
        res = self._sqlfunc.save_geodata_identification(data)
        return res

    @abstractmethod
    def start(self):
        """
        子类必须实现
        :return: 
        """
        pass

    def tag_mapping(self, keyword):
        """
        漏洞类型映射
        :param keyword:
        :return: 
        """
        tags_dict = {'Buffer Overflow': 'Buffer Overflow', 'Use After Free (UAF)': 'USE-AFTER-FREE',
                     'Out Of Bounds': 'Out Of Bounds', 'Cross-Site Request Forgery (CSRF)': 'CSRF',
                     'Metasploit Framework (MSF)': 'Metasploit Framework (MSF)',
                     'SQL Injection (SQLi)': 'SQL injection', 'Cross-Site Scripting (XSS)': 'XSS', 'Malware': 'Malware',
                     'Denial of Service (DoS)': 'Denial of service',
                     'File Inclusion (LFI/RFI)': 'File Inclusion (LFI/RFI)', 'Heap Overflow': 'Heap Overflow',
                     'Deserialization': 'Deserialization',
                     'Authentication Bypass / Credentials Bypass (AB/CB)': 'Authentication Bypass / Credentials Bypass (AB/CB)',
                     'XML External Entity (XXE)': 'XML External Entity (XXE)',
                     'Server-Side Request Forgery (SSRF)': 'ssrf', 'Local': 'Local', 'Traversal': 'Traversal',
                     'Remote': 'Remote', 'Type Confusion': 'Type Confusion', 'Command Injection': 'Command Injection',
                     'Code Injection': 'Code Injection', 'NULL Pointer Dereference': 'NULL Pointer Dereference',
                     'Integer Overflow': 'Integer Overflows', 'Race Condition': 'Race Condition', 'Pwn2Own': 'Pwn2Own',
                     'Console': 'Console', 'WordPress Core': 'WordPress Core', 'Client Side': 'Client Side',
                     'WordPress Plugin': 'WordPress Plugin', 'HTTP 参数污染': 'HTTP Parameter Pollution', '后门': 'Backdoor',
                     'Cookie 验证错误': 'Insecure Cookie Handling', '跨站请求伪造': 'CSRF', 'ShellCode': 'ShellCode',
                     'SQL 注入': 'SQL injection', '任意文件下载': 'Arbitrary File Download',
                     '任意文件创建': 'Arbitrary File Creation', '任意文件删除': 'Arbitrary File Deletion',
                     '任意文件读取': 'Arbitrary File Read', '其他类型': 'Other', '变量覆盖': 'Variable coverage',
                     '命令执行': 'Command Execution', '嵌入恶意代码': 'injecting malware codes', '弱密码': 'Weak Password',
                     '拒绝服务': 'Denial of service', '数据库发现': 'Database Found', '文件上传': 'upload files',
                     '远程文件包含': 'Remote File Inclusion', '本地溢出': 'local overflow', '权限提升': 'Privilege Escalation',
                     '信息泄漏': 'Information Disclosure', '登录绕过': 'Login Bypass', '目录穿越': 'Path Traversal',
                     '解析错误': 'Resolve Error', '越权访问': 'Unauthorized access', '跨站脚本': 'XSS', '路径泄漏': 'Path Disclosure',
                     '代码执行': 'Code Execution', '远程密码修改': 'Remote Password Change', '远程溢出': 'Remote Overflow',
                     '目录遍历': 'Directory Listing', '空字节注入': 'Null Byte Injection', '中间人攻击': 'Man-in-the-middle',
                     '格式化字符串': 'Format String', '缓冲区溢出': 'Buffer Overflow', 'HTTP 请求拆分': 'HTTP Request Splitting',
                     'CRLF 注入': 'CRLF Injection', 'XML 注入': 'XML Injection', '本地文件包含': 'Local File Inclusion',
                     '证书预测': 'Credential Prediction', 'HTTP 响应拆分': 'HTTP Response Splitting', 'SSI 注入': 'SSI Injection',
                     '内存溢出': 'Out of Memory', '整数溢出': 'Integer Overflows', 'HTTP 响应伪造': 'HTTP Response Smuggling',
                     'HTTP 请求伪造': 'HTTP Request Smuggling', '内容欺骗': 'Content Spoofing', 'XQuery 注入': 'XQuery Injection',
                     '缓存区过读': 'Buffer Over-read', '暴力破解': 'Brute Force', 'LDAP 注入': 'LDAP Injection',
                     '安全模式绕过': 'Security Mode Bypass', '备份文件发现': 'Backup File Found', 'XPath 注入': 'XPath Injection',
                     'URL 重定向': 'URL Redirector Abuse', '代码泄漏': 'Code Disclosure', '释放后重用': 'USE-AFTER-FREE',
                     'DNS 劫持': 'DNS hijacking', '错误的输入验证': 'Improper Input Validation', '通用跨站脚本': 'UXSS',
                     '服务器端请求伪造': 'ssrf', '跨域漏洞': 'Cross domain vulnerability',
                     '错误的证书验证': 'Improper Certificate Validation', 'remote exploits': 'Remote',
                     'local exploits': 'Local', 'web applications': 'web applications',
                     'dos / poc': 'Denial of service', 'shellcode': 'ShellCode'}
        if keyword in tags_dict.keys():
            return tags_dict[keyword]
        else:
            return keyword
