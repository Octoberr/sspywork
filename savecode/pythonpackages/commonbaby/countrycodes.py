"""The enumeration of country codes"""

# -*- coding:utf-8 -*-

import os
import sys

VERSION = 1.0


class CountryCode:
    """Rpresents the country code, region, phone number country code, time difference. etc. informations.
    countrycode: the country code
    phonecode: the phone country code
    countrynames: {language, countryname}. for example: {(EN, China), (CN, 中国)}
    useage: countrycodes.ALLCOUNTRYS.__contains__("EN")
    countrycodes.EN"""

    def __init__(self,
                 iso2: str,
                 iso3: str,
                 countrycode: str,
                 timediffer: float = 0,
                 squarekilometre: float = 0,
                 countrynames: {} = None,
                 remark: str = None):
        if iso2 is None or iso2 == '':
            raise ValueError("iso2 cannot be empty")
        if iso3 is None or iso3 == '':
            raise ValueError("iso3 cannot be empty")
        if countrycode is None or countrycode == '':
            raise ValueError("countrycode cannot be empty")

        self.iso2 = iso2
        self.ios3 = iso3
        self.countrycode = countrycode
        self.timediffer = timediffer
        self.squarekilometre = squarekilometre

        self.country_names = {}
        if not countrynames is None and len(countrynames) > 0:
            for key, val in countrynames.items():
                self.country_names[key] = val

        self.remark = ''
        if not remark is None and not remark == '':
            self.remark = remark


# all countries in dictionary
ALL_COUNTRIES = {}

AF = CountryCode("AF", "AFG", "93", 0, 647500, {
    "CN": "阿富汗",
    "EN": "Afghanistan"
})
ALL_COUNTRIES["AF"] = AF
AL = CountryCode("AL", "ALB", "355", -7, 28748, {
    "CN": "阿尔巴尼亚",
    "EN": "Albania"
})
ALL_COUNTRIES["AL"] = AL
DZ = CountryCode("DZ", "DZA", "213", -8, 2381740, {
    "CN": "阿尔及利亚",
    "EN": "Algeria"
})
ALL_COUNTRIES["DZ"] = DZ
AS = CountryCode("AS", "ASM", "1-684", -11, 199, {
    "CN": "美属萨摩亚",
    "EN": "American Samoa"
})
ALL_COUNTRIES["AS"] = AS
AD = CountryCode("AD", "AND", "376", -8, 468, {
    "CN": "安道尔共和国",
    "EN": "Andorra"
})
ALL_COUNTRIES["AD"] = AD
AO = CountryCode("AO", "AGO", "244", -7, 1246700, {
    "CN": "安哥拉",
    "EN": "Angola"
})
ALL_COUNTRIES["AO"] = AO
AI = CountryCode("AI", "AIA", "1-264", -12, 102, {
    "CN": "安圭拉岛",
    "EN": "Anguilla"
})
ALL_COUNTRIES["AI"] = AI
AQ = CountryCode("AQ", "ATA", "672", -3, 14000000, {
    "CN": "南极洲",
    "EN": "Antarctica"
})
ALL_COUNTRIES["AQ"] = AQ
AG = CountryCode("AG", "ATG", "1-268", -4, 443, {
    "CN": "安提瓜和巴布达",
    "EN": "Antigua and Barbuda"
})
ALL_COUNTRIES["AG"] = AG
AR = CountryCode("AR", "ARG", "54", -11, 2766890, {
    "CN": "阿根廷",
    "EN": "Argentina"
})
ALL_COUNTRIES["AR"] = AR
AM = CountryCode("AM", "ARM", "374", -6, 29800, {
    "CN": "亚美尼亚",
    "EN": "Armenia"
})
ALL_COUNTRIES["AM"] = AM
AW = CountryCode("AW", "ABW", "297", -4, 193, {
    "CN": "阿鲁巴岛（加勒比海）",
    "EN": "Aruba"
})
ALL_COUNTRIES["AW"] = AW
AU = CountryCode("AU", "AUS", "61", 2, 7686850, {
    "CN": "澳大利亚",
    "EN": "Australia"
})
ALL_COUNTRIES["AU"] = AU
AT = CountryCode("AT", "AUT", "43", -7, 83858, {"CN": "奥地利", "EN": "Austria"})
ALL_COUNTRIES["AT"] = AT
AZ = CountryCode("AZ", "AZE", "994", -5, 86600, {
    "CN": "阿塞拜疆",
    "EN": "Azerbaijan"
})
ALL_COUNTRIES["AZ"] = AZ
BS = CountryCode("BS", "BHS", "1-242", -13, 13940, {
    "CN": "巴哈马",
    "EN": "Bahamas"
})
ALL_COUNTRIES["BS"] = BS
BH = CountryCode("BH", "BHR", "973", -5, 665, {"CN": "巴林", "EN": "Bahrain"})
ALL_COUNTRIES["BH"] = BH
BD = CountryCode("BD", "BGD", "880", -2, 144000, {
    "CN": "孟加拉国",
    "EN": "Bangladesh"
})
ALL_COUNTRIES["BD"] = BD
BB = CountryCode("BB", "BRB", "1-246", -12, 431, {
    "CN": "巴巴多斯",
    "EN": "Barbados"
})
ALL_COUNTRIES["BB"] = BB
BY = CountryCode("BY", "BLR", "375", -6, 207600, {
    "CN": "白俄罗斯",
    "EN": "Belarus"
})
ALL_COUNTRIES["BY"] = BY
BE = CountryCode("BE", "BEL", "32", -7, 30510, {"CN": "比利时", "EN": "Belgium"})
ALL_COUNTRIES["BE"] = BE
BZ = CountryCode("BZ", "BLZ", "501", -14, 22966, {"CN": "伯利兹", "EN": "Belize"})
ALL_COUNTRIES["BZ"] = BZ
BJ = CountryCode("BJ", "BEN", "229", -7, 112620, {"CN": "贝宁", "EN": "Benin"})
ALL_COUNTRIES["BJ"] = BJ
BM = CountryCode("BM", "BMU", "1-441", -3, 53, {
    "CN": "百慕大群岛",
    "EN": "Bermuda"
})
ALL_COUNTRIES["BM"] = BM
BT = CountryCode("BT", "BTN", "975", 6, 47000, {"CN": "不丹", "EN": "Bhutan"})
ALL_COUNTRIES["BT"] = BT
BO = CountryCode("BO", "BOL", "591", -12, 1098580, {
    "CN": "玻利维亚",
    "EN": "Bolivia"
})
ALL_COUNTRIES["BO"] = BO
BA = CountryCode("BA", "BIH", "387", 2, 51129, {
    "CN": "波斯尼亚和黑塞哥维那",
    "EN": "Bosnia and Herzegovina"
}, "简称“波黑”,巴尔干半岛的一个国家")
ALL_COUNTRIES["BA"] = BA
BW = CountryCode("BW", "BWA", "267", -6, 600370, {
    "CN": "博茨瓦纳",
    "EN": "Botswana"
})
ALL_COUNTRIES["BW"] = BW
BR = CountryCode("BR", "BRA", "55", -11, 8511965, {"CN": "巴西", "EN": "Brazil"})
ALL_COUNTRIES["BR"] = BR
IO = CountryCode("IO", "IOT", "246", 6, 60, {
    "CN": "英属印度洋领地",
    "EN": "British Indian Ocean Territory"
})
ALL_COUNTRIES["IO"] = IO
VG = CountryCode("VG", "VGB", "1-284", -4, 153, {
    "CN": "英属维尔京群岛",
    "EN": "British Virgin Islands"
}, "英国在小安的列斯群岛最北部的殖民地，首府罗德城")
ALL_COUNTRIES["VG"] = VG
BN = CountryCode("BN", "BRN", "673", 0, 5770, {"CN": "文莱", "EN": "Brunei"})
ALL_COUNTRIES["BN"] = BN
BG = CountryCode("BG", "BGR", "359", -6, 110910, {
    "CN": "保加利亚",
    "EN": "Bulgaria"
})
ALL_COUNTRIES["BG"] = BG
BF = CountryCode("BF", "BFA", "226", -8, 274200, {
    "CN": "布基纳法索",
    "EN": "Burkina-faso"
})
ALL_COUNTRIES["BF"] = BF
BI = CountryCode("BI", "BDI", "257", -6, 27830, {"CN": "布隆迪", "EN": "Burundi"})
ALL_COUNTRIES["BI"] = BI
KH = CountryCode("KH", "KHM", "855", 7, 181040, {
    "CN": "柬埔寨",
    "EN": "Cambodia"
})
ALL_COUNTRIES["KH"] = KH
CM = CountryCode("CM", "CMR", "237", -7, 475440, {
    "CN": "喀麦隆",
    "EN": "Cameroon"
})
ALL_COUNTRIES["CM"] = CM
CA = CountryCode("CA", "CAN", "1", -13, 9984670, {"CN": "加拿大", "EN": "Canada"})
ALL_COUNTRIES["CA"] = CA
CV = CountryCode("CV", "CPV", "238", -1, 4033, {
    "CN": "佛得角",
    "EN": "Cape Verde"
})
ALL_COUNTRIES["CV"] = CV
KY = CountryCode("KY", "CYM", "1-345", -5, 262, {
    "CN": "开曼群岛",
    "EN": "Cayman Islands"
})
ALL_COUNTRIES["KY"] = KY
CF = CountryCode("CF", "CAF", "236", 1, 622984, {
    "CN": "中非共和国",
    "EN": "Central African Republic"
})
ALL_COUNTRIES["CF"] = CF
TD = CountryCode("TD", "TCD", "235", -7, 1284000, {"CN": "乍得", "EN": "Chad"})
ALL_COUNTRIES["TD"] = TD
CL = CountryCode("CL", "CHL", "56", -13, 756950, {"CN": "智利", "EN": "Chile"})
ALL_COUNTRIES["CL"] = CL
CN = CountryCode("CN", "CHN", "86", 0, 9596960, {"CN": "中国", "EN": "China"})
ALL_COUNTRIES["CN"] = CN
CX = CountryCode("CX", "CXR", "61", 14, 135, {
    "CN": "圣诞岛",
    "EN": "Christmas Island"
})
ALL_COUNTRIES["CX"] = CX
CC = CountryCode("CC", "CCK", "61", 6.5, 14, {
    "CN": "科科斯群岛;可可岛;",
    "EN": "Cocos Islands"
})
ALL_COUNTRIES["CC"] = CC
CO = CountryCode("CO", "COL", "57", 0, 1138910, {
    "CN": "哥伦比亚",
    "EN": "Colombia"
})
ALL_COUNTRIES["CO"] = CO
KM = CountryCode("KM", "COM", "269", 9, 2170, {
    "CN": "科摩罗（非洲）;",
    "EN": "Comoros"
})
ALL_COUNTRIES["KM"] = KM
CK = CountryCode("CK", "COK", "682", 9, 240, {
    "CN": "库克群岛;",
    "EN": "Cook Islands"
})
ALL_COUNTRIES["CK"] = CK
CR = CountryCode("CR", "CRI", "506", 9, 51100, {
    "CN": "哥斯达黎加;",
    "EN": "Costa Rica"
})
ALL_COUNTRIES["CR"] = CR
HR = CountryCode("HR", "HRV", "385", 9, 56542, {
    "CN": "克罗地亚;",
    "EN": "Croatia"
})
ALL_COUNTRIES["HR"] = HR
CU = CountryCode("CU", "CUB", "53", -13, 110860, {"CN": "古巴", "EN": "Cuba"})
ALL_COUNTRIES["CU"] = CU
CW = CountryCode("CW", "CUW", "599", 9, 444, {
    "CN": "柑桂酒，柑香酒",
    "EN": "Curacao"
})
ALL_COUNTRIES["CW"] = CW
CY = CountryCode("CY", "CYP", "357", -6, 9250, {"CN": "塞浦路斯", "EN": "Cyprus"})
ALL_COUNTRIES["CY"] = CY
CZ = CountryCode("CZ", "CZE", "420", 9, 78866, {
    "CN": "捷克共和国",
    "EN": "Czech Republic"
}, "欧罗巴洲,简称：捷克")
ALL_COUNTRIES["CZ"] = CZ
CD = CountryCode("CD", "COD", "243", 9, 2345410, {
    "CN": "刚果民主共和国;",
    "EN": "Democratic Republic of the Congo"
})
ALL_COUNTRIES["CD"] = CD
DK = CountryCode("DK", "DNK", "45", -7, 43094, {"CN": "丹麦", "EN": "Denmark"})
ALL_COUNTRIES["DK"] = DK
DJ = CountryCode("DJ", "DJI", "253", -5, 23000, {
    "CN": "吉布提",
    "EN": "Djibouti"
})
ALL_COUNTRIES["DJ"] = DJ
DM = CountryCode("DM", "DMA", "1-767", 9, 754, {
    "CN": "多米尼加",
    "EN": "Dominica"
}, "西印度群岛岛国")
ALL_COUNTRIES["DM"] = DM
DO = CountryCode("DO", "DOM", "1-809 1-829 1-849", 9, 48730, {
    "CN": "多米尼加共和国",
    "EN": "Dominican Republic"
})
ALL_COUNTRIES["DO"] = DO
TL = CountryCode("TL", "TLS", "670", 9, 15007, {
    "CN": "东帝汶",
    "EN": "East Timor"
}, "亚细亚洲")
ALL_COUNTRIES["TL"] = TL
EC = CountryCode("EC", "ECU", "593", -13, 283560, {
    "CN": "厄瓜多尔",
    "EN": "Ecuador"
})
ALL_COUNTRIES["EC"] = EC
EG = CountryCode("EG", "EGY", "20", -6, 1001450, {"CN": "埃及", "EN": "Egypt"})
ALL_COUNTRIES["EG"] = EG
SV = CountryCode("SV", "SLV", "503", 9, 21040, {
    "CN": "萨尔瓦多;",
    "EN": "El Salvador"
})
ALL_COUNTRIES["SV"] = SV
GQ = CountryCode("GQ", "GNQ", "240", 9, 28051, {
    "CN": "赤道几内亚",
    "EN": "Equatorial Guinea"
}, "为西非之一国")
ALL_COUNTRIES["GQ"] = GQ
ER = CountryCode("ER", "ERI", "291", 9, 121320, {
    "CN": "厄立特里亚;",
    "EN": "Eritrea"
})
ALL_COUNTRIES["ER"] = ER
EE = CountryCode("EE", "EST", "372", -5, 45226, {
    "CN": "爱沙尼亚",
    "EN": "Estonia"
})
ALL_COUNTRIES["EE"] = EE
ET = CountryCode("ET", "ETH", "251", -5, 1127127, {
    "CN": "埃塞俄比亚",
    "EN": "Ethiopia"
})
ALL_COUNTRIES["ET"] = ET
FK = CountryCode("FK", "FLK", "500", 9, 12173, {
    "CN": "",
    "EN": "Falkland Islands"
})
ALL_COUNTRIES["FK"] = FK
FO = CountryCode("FO", "FRO", "298", 9, 1399, {
    "CN": "法罗群岛",
    "EN": "Faroe Islands"
}, "位于北大西洋")
ALL_COUNTRIES["FO"] = FO
FJ = CountryCode("FJ", "FJI", "679", 4, 18270, {"CN": "斐济", "EN": "Fiji"})
ALL_COUNTRIES["FJ"] = FJ
FI = CountryCode("FI", "FIN", "358", -6, 337030, {"CN": "芬兰", "EN": "Finland"})
ALL_COUNTRIES["FI"] = FI
FR = CountryCode("FR", "FRA", "33", -8, 547030, {"CN": "法国", "EN": "France"})
ALL_COUNTRIES["FR"] = FR
PF = CountryCode("PF", "PYF", "689", 9, 4167, {
    "CN": "法属玻利尼西亚",
    "EN": "French Polynesia"
}, "[地名][大洋洲]法属波利尼西亚;")
ALL_COUNTRIES["PF"] = PF
GA = CountryCode("GA", "GAB", "241", -7, 267667, {"CN": "加蓬", "EN": "Gabon"})
ALL_COUNTRIES["GA"] = GA
GM = CountryCode("GM", "GMB", "220", -8, 11300, {"CN": "冈比亚", "EN": "Gambia"})
ALL_COUNTRIES["GM"] = GM
GE = CountryCode("GE", "GEO", "995", 0, 69700, {"CN": "格鲁吉亚", "EN": "Georgia"})
ALL_COUNTRIES["GE"] = GE
DE = CountryCode("DE", "DEU", "49", -7, 357021, {"CN": "德国", "EN": "Germany"})
ALL_COUNTRIES["DE"] = DE
GH = CountryCode("GH", "GHA", "233", -8, 239460, {"CN": "加纳", "EN": "Ghana"})
ALL_COUNTRIES["GH"] = GH
GI = CountryCode("GI", "GIB", "350", -8, 7, {"CN": "直布罗陀", "EN": "Gibraltar"})
ALL_COUNTRIES["GI"] = GI
GR = CountryCode("GR", "GRC", "30", -6, 131940, {"CN": "希腊", "EN": "Greece"})
ALL_COUNTRIES["GR"] = GR
GL = CountryCode("GL", "GRL", "299", 9, 2166086, {
    "CN": "格陵兰",
    "EN": "Greenland"
}, "岛名，位于北美洲的东北部，属丹麦")
ALL_COUNTRIES["GL"] = GL
GD = CountryCode("GD", "GRD", "1-473", -14, 344, {
    "CN": "格林纳达",
    "EN": "Grenada"
})
ALL_COUNTRIES["GD"] = GD
GU = CountryCode("GU", "GUM", "1-671", 2, 549, {"CN": "关岛", "EN": "Guam"})
ALL_COUNTRIES["GU"] = GU
GT = CountryCode("GT", "GTM", "502", -14, 108890, {
    "CN": "危地马拉",
    "EN": "Guatemala"
})
ALL_COUNTRIES["GT"] = GT
GG = CountryCode("GG", "GGY", "44-1481", 9, 78, {
    "CN": "格恩西衫",
    "EN": "Guernsey"
})
ALL_COUNTRIES["GG"] = GG
GN = CountryCode("GN", "GIN", "224", -8, 245857, {"CN": "几内亚", "EN": "Guinea"})
ALL_COUNTRIES["GN"] = GN
GW = CountryCode("GW", "GNB", "245", 9, 36120, {
    "CN": "几内亚比绍共和国;",
    "EN": "Guinea-Bissau"
})
ALL_COUNTRIES["GW"] = GW
GY = CountryCode("GY", "GUY", "592", -11, 214970, {
    "CN": "圭亚那",
    "EN": "Guyana"
})
ALL_COUNTRIES["GY"] = GY
HT = CountryCode("HT", "HTI", "509", -13, 27750, {"CN": "海地", "EN": "Haiti"})
ALL_COUNTRIES["HT"] = HT
HN = CountryCode("HN", "HND", "504", -14, 112090, {
    "CN": "洪都拉斯",
    "EN": "Honduras"
})
ALL_COUNTRIES["HN"] = HN
HK = CountryCode("HK", "HKG", "852", 0, 1092, {"CN": "香港", "EN": "Hongkong"})
ALL_COUNTRIES["HK"] = HK
HU = CountryCode("HU", "HUN", "36", -7, 93030, {"CN": "匈牙利", "EN": "Hungary"})
ALL_COUNTRIES["HU"] = HU
IS = CountryCode("IS", "ISL", "354", -9, 103000, {"CN": "冰岛", "EN": "Iceland"})
ALL_COUNTRIES["IS"] = IS
IN = CountryCode("IN", "IND", "91", -2.3, 3287590, {"CN": "印度", "EN": "India"})
ALL_COUNTRIES["IN"] = IN
ID = CountryCode("ID", "IDN", "62", -0.3, 1919440, {
    "CN": "印度尼西亚",
    "EN": "Indonesia"
})
ALL_COUNTRIES["ID"] = ID
IR = CountryCode("IR", "IRN", "98", -4.3, 1648000, {"CN": "伊朗", "EN": "Iran"})
ALL_COUNTRIES["IR"] = IR
IQ = CountryCode("IQ", "IRQ", "964", -5, 437072, {"CN": "伊拉克", "EN": "Iraq"})
ALL_COUNTRIES["IQ"] = IQ
IE = CountryCode("IE", "IRL", "353", -4.3, 70280, {
    "CN": "爱尔兰",
    "EN": "Ireland"
})
ALL_COUNTRIES["IE"] = IE
IM = CountryCode("IM", "IMN", "44-1624", 9, 572, {
    "CN": "英国属地曼岛",
    "EN": "Isle of Man"
}, "首都道格拉斯，位于欧洲")
ALL_COUNTRIES["IM"] = IM
IL = CountryCode("IL", "ISR", "972", -6, 20770, {"CN": "以色列", "EN": "Israel"})
ALL_COUNTRIES["IL"] = IL
IT = CountryCode("IT", "ITA", "39", -7, 301230, {"CN": "意大利", "EN": "Italy"})
ALL_COUNTRIES["IT"] = IT
CI = CountryCode("CI", "CIV", "225", 9, 322460, {
    "CN": "象牙海岸",
    "EN": "Ivory Coast"
}, "非洲")
ALL_COUNTRIES["CI"] = CI
JM = CountryCode("JM", "JAM", "1-876", -12, 10991, {
    "CN": "牙买加",
    "EN": "Jamaica"
})
ALL_COUNTRIES["JM"] = JM
JP = CountryCode("JP", "JPN", "81", 1, 377835, {"CN": "日本", "EN": "Japan"})
ALL_COUNTRIES["JP"] = JP
JE = CountryCode("JE", "JEY", "44-1534", 9, 116, {"CN": "泽西岛", "EN": "Jersey"})
ALL_COUNTRIES["JE"] = JE
JO = CountryCode("JO", "JOR", "962", -6, 92300, {"CN": "约旦", "EN": "Jordan"})
ALL_COUNTRIES["JO"] = JO
KZ = CountryCode("KZ", "KAZ", "7", -5, 2717300, {
    "CN": "哈萨克斯坦",
    "EN": "Kazakstan"
})
ALL_COUNTRIES["KZ"] = KZ
KE = CountryCode("KE", "KEN", "254", -5, 582650, {"CN": "肯尼亚", "EN": "Kenya"})
ALL_COUNTRIES["KE"] = KE
KI = CountryCode("KI", "KIR", "686", 9, 811, {
    "CN": "基里巴斯",
    "EN": "Kiribati"
}, "西太平洋上一共和国")
ALL_COUNTRIES["KI"] = KI
XK = CountryCode("XK", "XKX", "383", 9, 10887, {
    "CN": "科索沃",
    "EN": "Kosovo"
}, "南斯拉夫自治省名")
ALL_COUNTRIES["XK"] = XK
KW = CountryCode("KW", "KWT", "965", -5, 17820, {"CN": "科威特", "EN": "Kuwait"})
ALL_COUNTRIES["KW"] = KW
KG = CountryCode("KG", "KGZ", "996", -5, 198500, {
    "CN": "吉尔吉斯坦",
    "EN": "Kyrgyzstan"
})
ALL_COUNTRIES["KG"] = KG
LA = CountryCode("LA", "LAO", "856", -1, 236800, {"CN": "老挝", "EN": "Laos"})
ALL_COUNTRIES["LA"] = LA
LV = CountryCode("LV", "LVA", "371", -5, 64589, {"CN": "拉脱维亚", "EN": "Latvia"})
ALL_COUNTRIES["LV"] = LV
LB = CountryCode("LB", "LBN", "961", -6, 10400, {"CN": "黎巴嫩", "EN": "Lebanon"})
ALL_COUNTRIES["LB"] = LB
LS = CountryCode("LS", "LSO", "266", -6, 30355, {"CN": "莱索托", "EN": "Lesotho"})
ALL_COUNTRIES["LS"] = LS
LR = CountryCode("LR", "LBR", "231", -8, 111370, {
    "CN": "利比里亚",
    "EN": "Liberia"
})
ALL_COUNTRIES["LR"] = LR
LY = CountryCode("LY", "LBY", "218", -6, 1759540, {"CN": "利比亚", "EN": "Libya"})
ALL_COUNTRIES["LY"] = LY
LI = CountryCode("LI", "LIE", "423", -7, 160, {
    "CN": "列支敦士登",
    "EN": "Liechtenstein"
})
ALL_COUNTRIES["LI"] = LI
LT = CountryCode("LT", "LTU", "370", -5, 65200, {
    "CN": "立陶宛",
    "EN": "Lithuania"
})
ALL_COUNTRIES["LT"] = LT
LU = CountryCode("LU", "LUX", "352", -7, 2586, {
    "CN": "卢森堡",
    "EN": "Luxembourg"
})
ALL_COUNTRIES["LU"] = LU
MO = CountryCode("MO", "MAC", "853", 0, 254, {"CN": "澳门", "EN": "Macao"})
ALL_COUNTRIES["MO"] = MO
MK = CountryCode("MK", "MKD", "389", 9, 25333, {
    "CN": "马其顿王国",
    "EN": "Macedonia"
}, "马其顿地区")
ALL_COUNTRIES["MK"] = MK
MG = CountryCode("MG", "MDG", "261", -5, 587040, {
    "CN": "马达加斯加",
    "EN": "Madagascar"
})
ALL_COUNTRIES["MG"] = MG
MW = CountryCode("MW", "MWI", "265", -6, 118480, {"CN": "马拉维", "EN": "Malawi"})
ALL_COUNTRIES["MW"] = MW
MY = CountryCode("MY", "MYS", "60", -0.5, 329750, {
    "CN": "马来西亚",
    "EN": "Malaysia"
})
ALL_COUNTRIES["MY"] = MY
MV = CountryCode("MV", "MDV", "960", -7, 300, {"CN": "马尔代夫", "EN": "Maldives"})
ALL_COUNTRIES["MV"] = MV
ML = CountryCode("ML", "MLI", "223", -8, 1240000, {"CN": "马里", "EN": "Mali"})
ALL_COUNTRIES["ML"] = ML
MT = CountryCode("MT", "MLT", "356", -7, 316, {"CN": "马耳他", "EN": "Malta"})
ALL_COUNTRIES["MT"] = MT
MH = CountryCode("MH", "MHL", "692", 9, 181, {
    "CN": "马绍尔群岛;",
    "EN": "Marshall Islands"
}, "[地名][大洋洲]")
ALL_COUNTRIES["MH"] = MH
MR = CountryCode("MR", "MRT", "222", 9, 1030700, {
    "CN": "毛利塔尼亚",
    "EN": "Mauritania"
}, "北非古国")
ALL_COUNTRIES["MR"] = MR
MU = CountryCode("MU", "MUS", "230", -4, 2040, {
    "CN": "毛里求斯",
    "EN": "Mauritius"
})
ALL_COUNTRIES["MU"] = MU
YT = CountryCode("YT", "MYT", "262", 9, 374, {
    "CN": "马约特岛",
    "EN": "Mayotte"
}, "印度洋西部,位于科摩罗群岛东南端")
ALL_COUNTRIES["YT"] = YT
MX = CountryCode("MX", "MEX", "52", -15, 1972550, {
    "CN": "墨西哥",
    "EN": "Mexico"
})
ALL_COUNTRIES["MX"] = MX
FM = CountryCode("FM", "FSM", "691", 9, 702, {
    "CN": "密克罗尼西亚",
    "EN": "Micronesia"
}, "西太平洋岛群，意为“小岛群岛”")
ALL_COUNTRIES["FM"] = FM
MD = CountryCode("MD", "MDA", "373", 9, 33843, {
    "CN": "摩尔多瓦;",
    "EN": "Moldova"
})
ALL_COUNTRIES["MD"] = MD
MC = CountryCode("MC", "MCO", "377", -7, 2, {"CN": "摩纳哥", "EN": "Monaco"})
ALL_COUNTRIES["MC"] = MC
MN = CountryCode("MN", "MNG", "976", 0, 1565000, {
    "CN": "蒙古",
    "EN": "Mongolia"
})
ALL_COUNTRIES["MN"] = MN
ME = CountryCode("ME", "MNE", "382", 9, 14026, {
    "CN": "黑山共和国",
    "EN": "Montenegro"
}, "Yugoslavia西南部的地方")
ALL_COUNTRIES["ME"] = ME
MS = CountryCode("MS", "MSR", "1-664", 9, 102, {
    "CN": "蒙特色拉特岛",
    "EN": "Montserrat"
}, "位于美洲")
ALL_COUNTRIES["MS"] = MS
MA = CountryCode("MA", "MAR", "212", -6, 446550, {
    "CN": "摩洛哥",
    "EN": "Morocco"
})
ALL_COUNTRIES["MA"] = MA
MZ = CountryCode("MZ", "MOZ", "258", -6, 801590, {
    "CN": "莫桑比克",
    "EN": "Mozambique"
})
ALL_COUNTRIES["MZ"] = MZ
MM = CountryCode("MM", "MMR", "95", -1.3, 678500, {"CN": "缅甸", "EN": "Burma"})
ALL_COUNTRIES["MM"] = MM
NA = CountryCode("NA", "NAM", "264", -7, 825418, {
    "CN": "纳米比亚",
    "EN": "Namibia"
})
ALL_COUNTRIES["NA"] = NA
NR = CountryCode("NR", "NRU", "674", 4, 21, {"CN": "瑙鲁", "EN": "Nauru"})
ALL_COUNTRIES["NR"] = NR
NP = CountryCode("NP", "NPL", "977", -2.3, 140800, {
    "CN": "尼泊尔",
    "EN": "Nepal"
})
ALL_COUNTRIES["NP"] = NP
NL = CountryCode("NL", "NLD", "31", -7, 41526, {
    "CN": "荷兰",
    "EN": "Netherlands"
})
ALL_COUNTRIES["NL"] = NL
AN = CountryCode("AN", "ANT", "599", 9, 960, {
    "CN": "荷属安的列斯",
    "EN": "Netherlands Antilles"
}, "荷属安的列斯群岛拉丁美洲群岛")
ALL_COUNTRIES["AN"] = AN
NC = CountryCode("NC", "NCL", "687", 9, 19060, {
    "CN": "新喀里多尼亚",
    "EN": "New Caledonia"
}, "位于南太平洋")
ALL_COUNTRIES["NC"] = NC
NZ = CountryCode("NZ", "NZL", "64", 9, 268680, {
    "CN": "新西兰",
    "EN": "New Zealand"
}, "太平洋南部岛国")
ALL_COUNTRIES["NZ"] = NZ
NI = CountryCode("NI", "NIC", "505", -14, 129494, {
    "CN": "尼加拉瓜",
    "EN": "Nicaragua"
})
ALL_COUNTRIES["NI"] = NI
NE = CountryCode("NE", "NER", "227", -8, 1267000, {"CN": "尼日尔", "EN": "Niger"})
ALL_COUNTRIES["NE"] = NE
NG = CountryCode("NG", "NGA", "234", -7, 923768, {
    "CN": "尼日利亚",
    "EN": "Nigeria"
})
ALL_COUNTRIES["NG"] = NG
NU = CountryCode("NU", "NIU", "683", 9, 260, {
    "CN": "纽埃岛",
    "EN": "Niue"
}, "南太平洋中部,在汤加群岛以东，属新西兰")
ALL_COUNTRIES["NU"] = NU
KP = CountryCode("KP", "PRK", "850", 9, 120540, {
    "CN": "北韩，北朝鲜;",
    "EN": "North Korea"
})
ALL_COUNTRIES["KP"] = KP
MP = CountryCode("MP", "MNP", "1-670", 9, 477, {
    "CN": "北马里亚纳群岛",
    "EN": "Northern Mariana Islands"
})
ALL_COUNTRIES["MP"] = MP
NO = CountryCode("NO", "NOR", "47", -7, 324220, {"CN": "挪威", "EN": "Norway"})
ALL_COUNTRIES["NO"] = NO
OM = CountryCode("OM", "OMN", "968", -4, 212460, {"CN": "阿曼", "EN": "Oman"})
ALL_COUNTRIES["OM"] = OM
PK = CountryCode("PK", "PAK", "92", -2.3, 803940, {
    "CN": "巴基斯坦",
    "EN": "Pakistan"
})
ALL_COUNTRIES["PK"] = PK
PW = CountryCode("PW", "PLW", "680", 9, 458, {"CN": "钯金，金钯合金;", "EN": "Palau"})
ALL_COUNTRIES["PW"] = PW
PS = CountryCode("PS", "PSE", "970", 9, 5970, {
    "CN": "巴勒斯坦",
    "EN": "Palestine"
}, "亚洲西部一地区")
ALL_COUNTRIES["PS"] = PS
PA = CountryCode("PA", "PAN", "507", -13, 78200, {"CN": "巴拿马", "EN": "Panama"})
ALL_COUNTRIES["PA"] = PA
PG = CountryCode("PG", "PNG", "675", 9, 462840, {
    "CN": "巴布亚新几内亚;",
    "EN": "Papua New Guinea"
})
ALL_COUNTRIES["PG"] = PG
PY = CountryCode("PY", "PRY", "595", -12, 406750, {
    "CN": "巴拉圭",
    "EN": "Paraguay"
})
ALL_COUNTRIES["PY"] = PY
PE = CountryCode("PE", "PER", "51", -13, 1285220, {"CN": "秘鲁", "EN": "Peru"})
ALL_COUNTRIES["PE"] = PE
PH = CountryCode("PH", "PHL", "63", 0, 300000, {
    "CN": "菲律宾",
    "EN": "Philippines"
})
ALL_COUNTRIES["PH"] = PH
PN = CountryCode("PN", "PCN", "64", 9, 47, {"CN": "皮特克恩", "EN": "Pitcairn"})
ALL_COUNTRIES["PN"] = PN
PL = CountryCode("PL", "POL", "48", -7, 312685, {"CN": "波兰", "EN": "Poland"})
ALL_COUNTRIES["PL"] = PL
PT = CountryCode("PT", "PRT", "351", -8, 92391, {
    "CN": "葡萄牙",
    "EN": "Portugal"
})
ALL_COUNTRIES["PT"] = PT
PR = CountryCode("PR", "PRI", "1-787 1-939", 9, 9104, {
    "CN": "波多黎各;",
    "EN": "Puerto Rico"
})
ALL_COUNTRIES["PR"] = PR
QA = CountryCode("QA", "QAT", "974", -5, 11437, {"CN": "卡塔尔", "EN": "Qatar"})
ALL_COUNTRIES["QA"] = QA
CG = CountryCode("CG", "COG", "242", -7, 342000, {"CN": "刚果", "EN": "Congo"})
ALL_COUNTRIES["CG"] = CG
RE = CountryCode("RE", "REU", "262", 9, 2517, {"CN": "留尼旺岛", "EN": "Reunion"})
ALL_COUNTRIES["RE"] = RE
RO = CountryCode("RO", "ROU", "40", -6, 237500, {
    "CN": "罗马尼亚",
    "EN": "Romania"
})
ALL_COUNTRIES["RO"] = RO
RU = CountryCode("RU", "RUS", "7", -5, 17100000, {"CN": "俄罗斯", "EN": "Russia"})
ALL_COUNTRIES["RU"] = RU
RW = CountryCode("RW", "RWA", "250", 9, 26338, {
    "CN": "卢旺达",
    "EN": "Rwanda"
}, "非洲国家")
ALL_COUNTRIES["RW"] = RW
BL = CountryCode("BL", "BLM", "590", 9, 21, {
    "CN": "圣巴泰勒米岛;",
    "EN": "Saint Barthelemy"
})
ALL_COUNTRIES["BL"] = BL
SH = CountryCode("SH", "SHN", "290", 9, 410, {
    "CN": "圣赫勒拿岛;",
    "EN": "Saint Helena"
})
ALL_COUNTRIES["SH"] = SH
KN = CountryCode("KN", "KNA", "1-869", 9, 261, {
    "CN": "圣克里斯托弗和尼维斯岛",
    "EN": "Saint Kitts and Nevis"
}, "西印度群岛;SaintChristopherandNevis(French=WestIndiesislands)")
ALL_COUNTRIES["KN"] = KN
LC = CountryCode("LC", "LCA", "1-758", -12, 616, {
    "CN": "圣卢西亚",
    "EN": "St.Lucia"
})
ALL_COUNTRIES["LC"] = LC
MF = CountryCode("MF", "MAF", "590", 9, 53, {
    "CN": "圣马丁;法属圣马丁;",
    "EN": "Saint Martin"
})
ALL_COUNTRIES["MF"] = MF
PM = CountryCode("PM", "SPM", "508", 9, 242, {
    "CN": "圣皮埃尔和密克隆;",
    "EN": "Saint Pierre and Miquelon"
})
ALL_COUNTRIES["PM"] = PM
VC = CountryCode("VC", "VCT", "1-784", -12, 389, {
    "CN": "圣文森特",
    "EN": "St.Vincent"
})
ALL_COUNTRIES["VC"] = VC
WS = CountryCode("WS", "WSM", "685", 9, 2944, {
    "CN": "萨摩亚群岛",
    "EN": "Samoa"
}, "南太平洋")
ALL_COUNTRIES["WS"] = WS
SM = CountryCode("SM", "SMR", "378", 9, 61, {
    "CN": "圣马力诺",
    "EN": "San Marino"
}, "意大利半岛东部的国家")
ALL_COUNTRIES["SM"] = SM
ST = CountryCode("ST", "STP", "239", 9, 1001, {
    "CN": "圣多美和普林西比;",
    "EN": "Sao Tome and Principe"
}, "[地名][阿非利加洲]")
ALL_COUNTRIES["ST"] = ST
SA = CountryCode("SA", "SAU", "966", 9, 1960582, {
    "CN": "沙特阿拉伯;",
    "EN": "Saudi Arabia"
})
ALL_COUNTRIES["SA"] = SA
SN = CountryCode("SN", "SEN", "221", -8, 196190, {
    "CN": "塞内加尔",
    "EN": "Senegal"
})
ALL_COUNTRIES["SN"] = SN
RS = CountryCode("RS", "SRB", "381", 9, 88361, {
    "CN": "塞尔维亚",
    "EN": "Serbia"
}, "南斯拉夫成员共和国名")
ALL_COUNTRIES["RS"] = RS
SC = CountryCode("SC", "SYC", "248", -4, 455, {
    "CN": "塞舌尔",
    "EN": "Seychelles"
})
ALL_COUNTRIES["SC"] = SC
SL = CountryCode("SL", "SLE", "232", 9, 71740, {
    "CN": "塞拉利昂;",
    "EN": "Sierra Leone"
})
ALL_COUNTRIES["SL"] = SL
SG = CountryCode("SG", "SGP", "65", 0.3, 693, {"CN": "新加坡", "EN": "Singapore"})
ALL_COUNTRIES["SG"] = SG
SX = CountryCode("SX", "SXM", "1-721", 9, 34, {
    "CN": "荷属圣马丁",
    "EN": "Sint Maarten"
}, "圣马丁;圣马丁岛;圣马丁节;荷属马丁尼;")
ALL_COUNTRIES["SX"] = SX
SK = CountryCode("SK", "SVK", "421", -7, 48845, {
    "CN": "斯洛伐克",
    "EN": "Slovakia"
})
ALL_COUNTRIES["SK"] = SK
SI = CountryCode("SI", "SVN", "386", -7, 20273, {
    "CN": "斯洛文尼亚",
    "EN": "Slovenia"
})
ALL_COUNTRIES["SI"] = SI
SB = CountryCode("SB", "SLB", "677", 9, 28450, {
    "CN": "所罗门群岛;",
    "EN": "Solomon Islands"
}, "[地名][大洋洲]")
ALL_COUNTRIES["SB"] = SB
SO = CountryCode("SO", "SOM", "252", -5, 637657, {"CN": "索马里", "EN": "Somali"})
ALL_COUNTRIES["SO"] = SO
ZA = CountryCode("ZA", "ZAF", "27", 9, 1219912, {
    "CN": "南非",
    "EN": "South Africa"
}, "非洲南部的一个国家")
ALL_COUNTRIES["ZA"] = ZA
KR = CountryCode("KR", "KOR", "82", 1, 98480, {"CN": "韩国", "EN": "Korea"})
ALL_COUNTRIES["KR"] = KR
SS = CountryCode("SS", "SSD", "211", 9, 644329, {
    "CN": "南苏丹;苏丹南部;",
    "EN": "South Sudan"
})
ALL_COUNTRIES["SS"] = SS
ES = CountryCode("ES", "ESP", "34", -8, 504782, {"CN": "西班牙", "EN": "Spain"})
ALL_COUNTRIES["ES"] = ES
LK = CountryCode("LK", "LKA", "94", 9, 65610, {
    "CN": "斯里兰卡",
    "EN": "Sri Lanka"
}, "南亚岛国")
ALL_COUNTRIES["LK"] = LK
SD = CountryCode("SD", "SDN", "249", -6, 1861484, {"CN": "苏丹", "EN": "Sudan"})
ALL_COUNTRIES["SD"] = SD
SR = CountryCode("SR", "SUR", "597", -11.3, 163270, {
    "CN": "苏里南",
    "EN": "Suriname"
})
ALL_COUNTRIES["SR"] = SR
SJ = CountryCode("SJ", "SJM", "47", 9, 62049, {
    "CN": "斯瓦尔巴和扬马延",
    "EN": "Svalbard and Jan Mayen"
}, "扬马延;斯瓦爾巴島和揚馬延島")
ALL_COUNTRIES["SJ"] = SJ
SZ = CountryCode("SZ", "SWZ", "268", -6, 17363, {
    "CN": "斯威士兰",
    "EN": "Swaziland"
})
ALL_COUNTRIES["SZ"] = SZ
SE = CountryCode("SE", "SWE", "46", -7, 449964, {"CN": "瑞典", "EN": "Sweden"})
ALL_COUNTRIES["SE"] = SE
CH = CountryCode("CH", "CHE", "41", -7, 41290, {
    "CN": "瑞士",
    "EN": "Switzerland"
})
ALL_COUNTRIES["CH"] = CH
SY = CountryCode("SY", "SYR", "963", -6, 185180, {"CN": "叙利亚", "EN": "Syria"})
ALL_COUNTRIES["SY"] = SY
TW = CountryCode("TW", "TWN", "886", 0, 35980, {"CN": "台湾省", "EN": "Taiwan"})
ALL_COUNTRIES["TW"] = TW
TJ = CountryCode("TJ", "TJK", "992", -5, 143100, {
    "CN": "塔吉克斯坦",
    "EN": "Tajikstan"
})
ALL_COUNTRIES["TJ"] = TJ
TZ = CountryCode("TZ", "TZA", "255", -5, 945087, {
    "CN": "坦桑尼亚",
    "EN": "Tanzania"
})
ALL_COUNTRIES["TZ"] = TZ
TH = CountryCode("TH", "THA", "66", -1, 514000, {"CN": "泰国", "EN": "Thailand"})
ALL_COUNTRIES["TH"] = TH
TG = CountryCode("TG", "TGO", "228", -8, 56785, {"CN": "多哥", "EN": "Togo"})
ALL_COUNTRIES["TG"] = TG
TK = CountryCode("TK", "TKL", "690", 9, 10, {
    "CN": "托克劳",
    "EN": "Tokelau"
}, "南太平洋的环状珊瑚岛")
ALL_COUNTRIES["TK"] = TK
TO = CountryCode("TO", "TON", "676", 4, 748, {"CN": "汤加", "EN": "Tonga"})
ALL_COUNTRIES["TO"] = TO
TT = CountryCode("TT", "TTO", "1-868", 9, 5128, {
    "CN": "特立尼达和多巴哥",
    "EN": "Trinidad and Tobago"
}, "拉丁美洲岛国")
ALL_COUNTRIES["TT"] = TT
TN = CountryCode("TN", "TUN", "216", -7, 163610, {
    "CN": "突尼斯",
    "EN": "Tunisia"
})
ALL_COUNTRIES["TN"] = TN
TR = CountryCode("TR", "TUR", "90", -6, 780580, {"CN": "土耳其", "EN": "Turkey"})
ALL_COUNTRIES["TR"] = TR
TM = CountryCode("TM", "TKM", "993", -5, 488100, {
    "CN": "土库曼斯坦",
    "EN": "Turkmenistan"
})
ALL_COUNTRIES["TM"] = TM
TC = CountryCode("TC", "TCA", "1-649", 9, 430, {
    "CN": "特克斯和凯科斯群岛",
    "EN": "Turks and Caicos Islands"
}, "巴哈马群岛东南部的两组群岛，英国殖民地")
ALL_COUNTRIES["TC"] = TC
TV = CountryCode("TV", "TUV", "688", 9, 26, {
    "CN": "图瓦卢",
    "EN": "Tuvalu"
}, "西太平洋岛国，旧称埃利斯群岛")
ALL_COUNTRIES["TV"] = TV
VI = CountryCode("VI", "VIR", "1-340", 9, 352, {
    "CN": "美属维尔京群岛;",
    "EN": "U.S. Virgin Islands"
})
ALL_COUNTRIES["VI"] = VI
UG = CountryCode("UG", "UGA", "256", -5, 236040, {"CN": "乌干达", "EN": "Uganda"})
ALL_COUNTRIES["UG"] = UG
UA = CountryCode("UA", "UKR", "380", -5, 603700, {
    "CN": "乌克兰",
    "EN": "Ukraine"
})
ALL_COUNTRIES["UA"] = UA
AE = CountryCode("AE", "ARE", "971", 9, 82880, {
    "CN": "阿拉伯联合酋长国",
    "EN": "United Arab Emirates"
}, "(=UAE);")
ALL_COUNTRIES["AE"] = AE
GB = CountryCode("GB", "GBR", "44", 9, 244820, {
    "CN": "联合王国;",
    "EN": "United Kingdom"
}, "大不列颠")
ALL_COUNTRIES["GB"] = GB
US = CountryCode("US", "USA", "1", 9, 9629091, {
    "CN": "美国;",
    "EN": "United States"
})
ALL_COUNTRIES["US"] = US
UY = CountryCode("UY", "URY", "598", -10.3, 176220, {
    "CN": "乌拉圭",
    "EN": "Uruguay"
})
ALL_COUNTRIES["UY"] = UY
UZ = CountryCode("UZ", "UZB", "998", -5, 447400, {
    "CN": "乌兹别克斯坦",
    "EN": "Uzbekistan"
})
ALL_COUNTRIES["UZ"] = UZ
VU = CountryCode("VU", "VUT", "678", 9, 12200, {
    "CN": "瓦努阿图",
    "EN": "Vanuatu"
}, "西南太平洋岛国")
ALL_COUNTRIES["VU"] = VU
VA = CountryCode("VA", "VAT", "379", 9, 0, {
    "CN": "梵蒂冈;罗马教廷;",
    "EN": "Vatican"
})
ALL_COUNTRIES["VA"] = VA
VE = CountryCode("VE", "VEN", "58", -12.3, 912050, {
    "CN": "委内瑞拉",
    "EN": "Venezuela"
})
ALL_COUNTRIES["VE"] = VE
VN = CountryCode("VN", "VNM", "84", -1, 329560, {"CN": "越南", "EN": "Vietnam"})
ALL_COUNTRIES["VN"] = VN
WF = CountryCode("WF", "WLF", "681", 9, 274, {
    "CN": "瓦利斯群岛和富图纳群岛",
    "EN": "Wallis and Futuna"
}, "法属，位于南太平洋的斐济与萨摩亚之间。")
ALL_COUNTRIES["WF"] = WF
EH = CountryCode("EH", "ESH", "212", 9, 266000, {
    "CN": "西撒哈拉",
    "EN": "Western Sahara"
}, "[地名][阿非利加洲]西撒哈拉")
ALL_COUNTRIES["EH"] = EH
YE = CountryCode("YE", "YEM", "967", -5, 527970, {"CN": "也门", "EN": "Yemen"})
ALL_COUNTRIES["YE"] = YE
ZM = CountryCode("ZM", "ZMB", "260", -6, 752614, {"CN": "赞比亚", "EN": "Zambia"})
ALL_COUNTRIES["ZM"] = ZM
ZW = CountryCode("ZW", "ZWE", "263", -6, 390580, {
    "CN": "津巴布韦",
    "EN": "Zimbabwe"
})
ALL_COUNTRIES["ZW"] = ZW


def __export(outfiPath: str):
    if os.path.exists(outfiPath) and os.path.isfile(outfiPath):
        os.remove(outfiPath)

    with open(outfiPath, mode='a', encoding='utf-8') as fs:
        for c in ALL_COUNTRIES.values():
            c: CountryCode = c
            line = "%s\t%s\t%s\t%s\t%s\t%s\t%s" % (c.iso2, c.ios3,
                                                   c.countrycode, c.timediffer,
                                                   c.country_names["CN"],
                                                   c.country_names["EN"],
                                                   c.remark)
            fs.write(line + '\n')


def __search_iso2(key):
    res = []
    if key is None or key == '':
        return res
    if ALL_COUNTRIES.__contains__(key):
        res.append(ALL_COUNTRIES[key])
    else:
        return res
    return res


def __search_iso3(key):
    if key is None or key == '':
        return []
    res = []
    for c in ALL_COUNTRIES.values():
        if c.ios3 == key:
            res.append(c)
            break
    return res


def __search_en(key):
    if key is None or key == '':
        return []
    res = []
    for c in ALL_COUNTRIES.values():
        if key in c.country_names["EN"]:
            res.append(c)
    return res


def __search_cn(key):
    if key is None or key == '':
        return []
    res = []
    for c in ALL_COUNTRIES.values():
        if key in c.country_names["CN"]:
            res.append(c)
    return res


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("useage:\n\
        python countrycode.py --en America\n\
        \n\
        --iso2           search by 2 character based country short name, like: US, UK .etc.\n\
        --iso3           search by 3 character based country short name, like: USA, CHN .etc.\n\
        --en             search by country name by English\n\
        --cn             search by country name in Chinese\n\
        --version        print countrycodepy %s\n\
        --export=[path]  export all data to a file, if [path] is not specified, will export to './countrycode.txt'\n\n\
        If passed mutiple arguments, will search and print them all" % VERSION)
        sys.exit(0)

    args = []
    currkey = None
    currval = None
    iskey = True
    isfirst = True
    printV = False
    isexport = False
    exportTo = './countrycode.txt'
    for a in sys.argv:
        if isfirst:
            isfirst = False
            continue
        if a == '--version':
            printV = True
            iskey = True
            continue
        if a.startswith('--export'):
            export = True
            if '=' in a:
                tmp = a.split('=')[1]
                if not tmp is None and not tmp == '':
                    exportTo = tmp
            continue
        if iskey:
            currkey = a.lower()
            iskey = False
        else:
            currval = a.upper()
            args.append([currkey, currval])
            iskey = True

    if printV:
        print("countrycodepy %s" % VERSION)

    if export:
        __export(exportTo)

    items = []
    for k, v in args:
        if k == '--iso2':
            items.extend(__search_iso2(v))
        elif k == '--iso3':
            items.extend(__search_iso3(v))
        elif k == '--en':
            items.extend(__search_en(v))
        elif k == '--cn':
            items.extend(__search_cn(v))

        if not items is None and not len(items) < 1:
            for c in items:
                print("%s\t%s\t%s\t%s\t%s\t%s" %
                      (c.iso2, c.ios3, c.countrycode, c.country_names["CN"],
                       c.country_names["EN"], c.remark))
            items.clear()
