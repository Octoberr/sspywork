"""The enumeration of charset code pages"""

# -*- coding:utf-8 -*-


class EncodingInfo(object):
    """Represents a charset/encoding page."""

    all_charsets = {}
    _all_charsets_lower_cased_name = {}

    # the name of the charset
    name: str = None

    # the code page of the charset
    code_page: str = None

    # the display name(in chinese) of the charset
    display_name: str = None

    def __init__(self, name: str, codepage: str, displayname: str = None):
        self.name = name
        self.code_page = codepage
        self.display_name = displayname
        EncodingInfo.all_charsets[name] = self
        EncodingInfo._all_charsets_lower_cased_name[name.lower()] = self

    @staticmethod
    def contains_charset(self, s: str) -> bool:
        """Judge if given str is a valid charset name, return a boolean. 
        The str could be charset name like 'utf-8' and the code page number 
        like '65001'. Letter case ignored."""
        return EncodingInfo._all_charsets_lower_cased_name.__contains__(
            s.lower())


def contains_charset(s: str) -> bool:
    """Judge if given str is a valid charset name, return a boolean. 
    The str could be charset name like 'utf-8' and the code page number 
    like '65001'. Letter case ignored."""
    return EncodingInfo._all_charsets_lower_cased_name.__contains__(s.lower())


IBM037: EncodingInfo = EncodingInfo('IBM037', '37', 'IBM EBCDIC (美国-加拿大)')
IBM437: EncodingInfo = EncodingInfo('IBM437', '437', 'OEM 美国')
IBM500: EncodingInfo = EncodingInfo('IBM500', '500', 'IBM EBCDIC (国际)')
ASMO708: EncodingInfo = EncodingInfo('ASMO-708', '708', '阿拉伯字符(ASMO-708)')
DOS720: EncodingInfo = EncodingInfo('DOS-720', '720', '阿拉伯字符(DOS)')
ibm737: EncodingInfo = EncodingInfo('ibm737', '737', '希腊字符(DOS)')
ibm775: EncodingInfo = EncodingInfo('ibm775', '775', '波罗的海字符(DOS)')
ibm850: EncodingInfo = EncodingInfo('ibm850', '850', '西欧字符(DOS)')
ibm852: EncodingInfo = EncodingInfo('ibm852', '852', '中欧字符(DOS)')
IBM855: EncodingInfo = EncodingInfo('IBM855', '855', 'OEM 西里尔语')
ibm857: EncodingInfo = EncodingInfo('ibm857', '857', '土耳其字符(DOS)')
IBM00858: EncodingInfo = EncodingInfo('IBM00858', '858', 'OEM 多语言拉丁语 I')
IBM860: EncodingInfo = EncodingInfo('IBM860', '860', '葡萄牙语(DOS)')
ibm861: EncodingInfo = EncodingInfo('ibm861', '861', '冰岛语(DOS)')
DOS862: EncodingInfo = EncodingInfo('DOS-862', '862', '希伯来字符(DOS)')
IBM863: EncodingInfo = EncodingInfo('IBM863', '863', '加拿大法语(DOS)')
IBM864: EncodingInfo = EncodingInfo('IBM864', '864', '阿拉伯字符(864)')
IBM865: EncodingInfo = EncodingInfo('IBM865', '865', '北欧字符(DOS)')
cp866: EncodingInfo = EncodingInfo('cp866', '866', '西里尔字符(DOS)')
ibm869: EncodingInfo = EncodingInfo('ibm869', '869', '现代希腊字符(DOS)')
IBM870: EncodingInfo = EncodingInfo('IBM870', '870', 'IBM EBCDIC (多语言拉丁语 2)')
windows874: EncodingInfo = EncodingInfo('windows-874', '874', '泰语(Windows)')
cp875: EncodingInfo = EncodingInfo('cp875', '875', 'IBM EBCDIC (现代希腊语)')
shift_jis: EncodingInfo = EncodingInfo('shift_jis', '932', '日语(Shift-JIS)')
gb2312: EncodingInfo = EncodingInfo('gb2312', '936', '简体中文(GB2312)')
ks_c_56011987: EncodingInfo = EncodingInfo('ks_c_5601-1987', '949', '朝鲜语')
big5: EncodingInfo = EncodingInfo('big5', '950', '繁体中文(Big5)')
IBM1026: EncodingInfo = EncodingInfo('IBM1026', '1026',
                                     'IBM EBCDIC (土耳其拉丁语 5)')
IBM01047: EncodingInfo = EncodingInfo('IBM01047', '1047', 'IBM 拉丁语 1')
IBM01140: EncodingInfo = EncodingInfo('IBM01140', '1140',
                                      'IBM EBCDIC (美国-加拿大-欧洲)')
IBM01141: EncodingInfo = EncodingInfo('IBM01141', '1141', 'IBM EBCDIC (德国-欧洲)')
IBM01142: EncodingInfo = EncodingInfo('IBM01142', '1142',
                                      'IBM EBCDIC (丹麦-挪威-欧洲)')
IBM01143: EncodingInfo = EncodingInfo('IBM01143', '1143',
                                      'IBM EBCDIC (芬兰-瑞典-欧洲)')
IBM01144: EncodingInfo = EncodingInfo('IBM01144', '1144',
                                      'IBM EBCDIC (意大利-欧洲)')
IBM01145: EncodingInfo = EncodingInfo('IBM01145', '1145',
                                      'IBM EBCDIC (西班牙-欧洲)')
IBM01146: EncodingInfo = EncodingInfo('IBM01146', '1146', 'IBM EBCDIC (英国-欧洲)')
IBM01147: EncodingInfo = EncodingInfo('IBM01147', '1147', 'IBM EBCDIC (法国-欧洲)')
IBM01148: EncodingInfo = EncodingInfo('IBM01148', '1148', 'IBM EBCDIC (国际-欧洲)')
IBM01149: EncodingInfo = EncodingInfo('IBM01149', '1149',
                                      'IBM EBCDIC (冰岛语-欧洲)')
# This Unicode is the same as utf16, add it here is for easy using and understanding...
Unicode: EncodingInfo = EncodingInfo('utf-16', '1200', 'Unicode')
utf16: EncodingInfo = EncodingInfo('utf-16', '1200', 'Unicode')
utf16BE: EncodingInfo = EncodingInfo('utf-16BE', '1201',
                                     'Unicode (Big-Endian)')
windows1250: EncodingInfo = EncodingInfo('windows-1250', '1250',
                                         '中欧字符(Windows)')
windows1251: EncodingInfo = EncodingInfo('windows-1251', '1251',
                                         '西里尔字符(Windows)')
Windows1252: EncodingInfo = EncodingInfo('Windows-1252', '1252',
                                         '西欧字符(Windows)')
windows1253: EncodingInfo = EncodingInfo('windows-1253', '1253',
                                         '希腊字符(Windows)')
windows1254: EncodingInfo = EncodingInfo('windows-1254', '1254',
                                         '土耳其字符(Windows)')
windows1255: EncodingInfo = EncodingInfo('windows-1255', '1255',
                                         '希伯来字符(Windows)')
windows1256: EncodingInfo = EncodingInfo('windows-1256', '1256',
                                         '阿拉伯字符(Windows)')
windows1257: EncodingInfo = EncodingInfo('windows-1257', '1257',
                                         '波罗的海字符(Windows)')
windows1258: EncodingInfo = EncodingInfo('windows-1258', '1258',
                                         '越南字符(Windows)')
Johab: EncodingInfo = EncodingInfo('Johab', '1361', '朝鲜语(Johab)')
macintosh: EncodingInfo = EncodingInfo('macintosh', '10000', '西欧字符(Mac)')
xmacjapanese: EncodingInfo = EncodingInfo('x-mac-japanese', '10001', '日语(Mac)')
xmacchinesetrad: EncodingInfo = EncodingInfo('x-mac-chinesetrad', '10002',
                                             '繁体中文(Mac)')
xmackorean: EncodingInfo = EncodingInfo('x-mac-korean', '10003', '朝鲜语(Mac)')
xmacarabic: EncodingInfo = EncodingInfo('x-mac-arabic', '10004', '阿拉伯字符(Mac)')
xmachebrew: EncodingInfo = EncodingInfo('x-mac-hebrew', '10005', '希伯来字符(Mac)')
xmacgreek: EncodingInfo = EncodingInfo('x-mac-greek', '10006', '希腊字符(Mac)')
xmaccyrillic: EncodingInfo = EncodingInfo('x-mac-cyrillic', '10007',
                                          '西里尔字符(Mac)')
xmacchinesesimp: EncodingInfo = EncodingInfo('x-mac-chinesesimp', '10008',
                                             '简体中文(Mac)')
xmacromanian: EncodingInfo = EncodingInfo('x-mac-romanian', '10010',
                                          '罗马尼亚语(Mac)')
xmacukrainian: EncodingInfo = EncodingInfo('x-mac-ukrainian', '10017',
                                           '乌克兰语(Mac)')
xmacthai: EncodingInfo = EncodingInfo('x-mac-thai', '10021', '泰语(Mac)')
xmacce: EncodingInfo = EncodingInfo('x-mac-ce', '10029', '中欧字符(Mac)')
xmacicelandic: EncodingInfo = EncodingInfo('x-mac-icelandic', '10079',
                                           '冰岛语(Mac)')
xmacturkish: EncodingInfo = EncodingInfo('x-mac-turkish', '10081',
                                         '土耳其字符(Mac)')
xmaccroatian: EncodingInfo = EncodingInfo('x-mac-croatian', '10082',
                                          '克罗地亚语(Mac)')
utf32: EncodingInfo = EncodingInfo('utf-32', '12000', 'Unicode (UTF-32)')
utf32BE: EncodingInfo = EncodingInfo('utf-32BE', '12001',
                                     'Unicode (UTF-32 Big-Endian)')
xChineseCNS: EncodingInfo = EncodingInfo('x-Chinese-CNS', '20000', '繁体中文(CNS)')
xcp20001: EncodingInfo = EncodingInfo('x-cp20001', '20001', 'TCA 中国台湾')
xChineseEten: EncodingInfo = EncodingInfo('x-Chinese-Eten', '20002',
                                          '繁体中文(Eten)')
xcp20003: EncodingInfo = EncodingInfo('x-cp20003', '20003', 'IBM5550 中国台湾')
xcp20004: EncodingInfo = EncodingInfo('x-cp20004', '20004', 'TeleText 中国台湾')
xcp20005: EncodingInfo = EncodingInfo('x-cp20005', '20005', 'Wang 中国台湾')
xIA5: EncodingInfo = EncodingInfo('x-IA5', '20105', '西欧字符(IA5)')
xIA5German: EncodingInfo = EncodingInfo('x-IA5-German', '20106', '德语(IA5)')
xIA5Swedish: EncodingInfo = EncodingInfo('x-IA5-Swedish', '20107', '瑞典语(IA5)')
xIA5Norwegian: EncodingInfo = EncodingInfo('x-IA5-Norwegian', '20108',
                                           '挪威语(IA5)')
usascii: EncodingInfo = EncodingInfo('us-ascii', '20127', 'US-ASCII')
xcp20261: EncodingInfo = EncodingInfo('x-cp20261', '20261', 'T.61')
xcp20269: EncodingInfo = EncodingInfo('x-cp20269', '20269', 'ISO-6937')
IBM273: EncodingInfo = EncodingInfo('IBM273', '20273', 'IBM EBCDIC (德国)')
IBM277: EncodingInfo = EncodingInfo('IBM277', '20277', 'IBM EBCDIC (丹麦-挪威)')
IBM278: EncodingInfo = EncodingInfo('IBM278', '20278', 'IBM EBCDIC (芬兰-瑞典)')
IBM280: EncodingInfo = EncodingInfo('IBM280', '20280', 'IBM EBCDIC (意大利)')
IBM284: EncodingInfo = EncodingInfo('IBM284', '20284', 'IBM EBCDIC (西班牙)')
IBM285: EncodingInfo = EncodingInfo('IBM285', '20285', 'IBM EBCDIC (UK)')
IBM290: EncodingInfo = EncodingInfo('IBM290', '20290', 'IBM EBCDIC (日语片假名)')
IBM297: EncodingInfo = EncodingInfo('IBM297', '20297', 'IBM EBCDIC (法国)')
IBM420: EncodingInfo = EncodingInfo('IBM420', '20420', 'IBM EBCDIC (阿拉伯语)')
IBM423: EncodingInfo = EncodingInfo('IBM423', '20423', 'IBM EBCDIC (希腊语)')
IBM424: EncodingInfo = EncodingInfo('IBM424', '20424', 'IBM EBCDIC (希伯来语)')
xEBCDICKoreanExtended: EncodingInfo = EncodingInfo(
    'x-EBCDIC-KoreanExtended', '20833', 'IBM EBCDIC (朝鲜语扩展)')
IBMThai: EncodingInfo = EncodingInfo('IBM-Thai', '20838', 'IBM EBCDIC (泰语)')
koi8r: EncodingInfo = EncodingInfo('koi8-r', '20866', '西里尔字符(KOI8-R)')
IBM871: EncodingInfo = EncodingInfo('IBM871', '20871', 'IBM EBCDIC (冰岛语)')
IBM880: EncodingInfo = EncodingInfo('IBM880', '20880', 'IBM EBCDIC (西里尔俄语)')
IBM905: EncodingInfo = EncodingInfo('IBM905', '20905', 'IBM EBCDIC (土耳其语)')
IBM00924: EncodingInfo = EncodingInfo('IBM00924', '20924', 'IBM 拉丁语 1')
EUCJP: EncodingInfo = EncodingInfo('EUC-JP', '20932',
                                   '日语(JIS 0208-1990 和 0212-1990)')
xcp20936: EncodingInfo = EncodingInfo('x-cp20936', '20936', '简体中文(GB2312-80)')
xcp20949: EncodingInfo = EncodingInfo('x-cp20949', '20949', '朝鲜语 Wansung')
cp1025: EncodingInfo = EncodingInfo('cp1025', '21025',
                                    'IBM EBCDIC (西里尔塞尔维亚-保加利亚语)')
koi8u: EncodingInfo = EncodingInfo('koi8-u', '21866', '西里尔字符(KOI8-U)')
iso88591: EncodingInfo = EncodingInfo('iso-8859-1', '28591', '西欧字符(ISO)')
iso88592: EncodingInfo = EncodingInfo('iso-8859-2', '28592', '中欧字符(ISO)')
iso88593: EncodingInfo = EncodingInfo('iso-8859-3', '28593', '拉丁语 3 (ISO)')
iso88594: EncodingInfo = EncodingInfo('iso-8859-4', '28594', '波罗的海字符(ISO)')
iso88595: EncodingInfo = EncodingInfo('iso-8859-5', '28595', '西里尔字符(ISO)')
iso88596: EncodingInfo = EncodingInfo('iso-8859-6', '28596', '阿拉伯字符(ISO)')
iso88597: EncodingInfo = EncodingInfo('iso-8859-7', '28597', '希腊字符(ISO)')
iso88598: EncodingInfo = EncodingInfo('iso-8859-8', '28598',
                                      '希伯来字符(ISO-Visual)')
iso88599: EncodingInfo = EncodingInfo('iso-8859-9', '28599', '土耳其字符(ISO)')
iso885913: EncodingInfo = EncodingInfo('iso-8859-13', '28603', '爱沙尼亚语(ISO)')
iso885915: EncodingInfo = EncodingInfo('iso-8859-15', '28605', '拉丁语 9 (ISO)')
xEuropa: EncodingInfo = EncodingInfo('x-Europa', '29001', '欧罗巴')
iso88598i: EncodingInfo = EncodingInfo('iso-8859-8-i', '38598',
                                       '希伯来字符(ISO-Logical)')
iso2022jp: EncodingInfo = EncodingInfo('iso-2022-jp', '50220', '日语(JIS)')
csISO2022JP: EncodingInfo = EncodingInfo('csISO2022JP', '50221',
                                         '日语(JIS-允许 1 字节假名)')
iso2022jp: EncodingInfo = EncodingInfo('iso-2022-jp', '50222',
                                       '日语(JIS-允许 1 字节假名 - SO/SI)')
iso2022kr: EncodingInfo = EncodingInfo('iso-2022-kr', '50225', '朝鲜语(ISO)')
xcp50227: EncodingInfo = EncodingInfo('x-cp50227', '50227', '简体中文(ISO-2022)')
eucjp: EncodingInfo = EncodingInfo('euc-jp', '51932', '日语(EUC)')
EUCCN: EncodingInfo = EncodingInfo('EUC-CN', '51936', '简体中文(EUC)')
euckr: EncodingInfo = EncodingInfo('euc-kr', '51949', '朝鲜语(EUC)')
hzgb2312: EncodingInfo = EncodingInfo('hz-gb-2312', '52936', '简体中文(HZ)')
GB18030: EncodingInfo = EncodingInfo('GB18030', '54936', '简体中文(GB18030)')
xisciide: EncodingInfo = EncodingInfo('x-iscii-de', '57002', 'ISCII 梵文')
xisciibe: EncodingInfo = EncodingInfo('x-iscii-be', '57003', 'ISCII 孟加拉语')
xisciita: EncodingInfo = EncodingInfo('x-iscii-ta', '57004', 'ISCII 泰米尔语')
xisciite: EncodingInfo = EncodingInfo('x-iscii-te', '57005', 'ISCII 泰卢固语')
xisciias: EncodingInfo = EncodingInfo('x-iscii-as', '57006', 'ISCII 阿萨姆语')
xisciior: EncodingInfo = EncodingInfo('x-iscii-or', '57007', 'ISCII 奥里雅语')
xisciika: EncodingInfo = EncodingInfo('x-iscii-ka', '57008', 'ISCII 卡纳达语')
xisciima: EncodingInfo = EncodingInfo('x-iscii-ma', '57009', 'ISCII 马拉雅拉姆语')
xisciigu: EncodingInfo = EncodingInfo('x-iscii-gu', '57010', 'ISCII 古吉拉特语')
xisciipa: EncodingInfo = EncodingInfo('x-iscii-pa', '57011', 'ISCII 旁遮普语')
utf7: EncodingInfo = EncodingInfo('utf-7', '65000', 'Unicode (UTF-7)')
utf8: EncodingInfo = EncodingInfo('utf-8', '65001', 'Unicode (UTF-8)')
utf8_bom: EncodingInfo = EncodingInfo('utf_8_sig', '65001', 'UTF-8带BOM')
