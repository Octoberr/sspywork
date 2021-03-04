"""
当当网爬虫
"""
import re
import requests
from bs4 import BeautifulSoup


class DangDang(object):
    def __init__(self) -> None:
        super().__init__()
        self.ha = requests.session()

    def cookielogin(self):
        """
        docstring
        """
        url = "http://myhome.dangdang.com/"
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Cookie": 'ddscreen=2; __permanent_id=20210113094803223398217227175634934; __visit_id=20210113094803273227981310211143566; __out_refer=; permanent_key=20210113095520189604544616efff2a; smidV2=20210113095531d61fa7f77301220ac3cc3c6c56f9380400c0f10e74700a360; __dd_token_id=20210113095602962427463568712b30; USERNUM=n1W2rYKcbL0BldFpczSh4A==; login.dangdang.com=.AYH=20210113094833013328747&.ASPXAUTH=2MvACGkGDerTn5Tp8rsE8w27R5p2zF4WK4BEzGX3p46P5QNIpmpS2g==; dangdang.com=email=MTgxNjEyMjQxMzIxMjk1MkBkZG1vYmlscGhvbmVfX3VzZXIuY29t&nickname=&display_id=4071040261431&customerid=6R+EN/yZRafn31Eyjzu5AQ==&viptype=sNyzpZWFNdo=&show_name=181%2A%2A%2A%2A4132; ddoy=email=1816122413212952%40ddmobilphone__user.com&nickname=&agree_date=1&validatedflag=0&uname=18161224132&utype=&.ALFG=off&.ALTM=1610502962; sessionID=pc_b084a0c81923c300b61e722941b6c91a16601ec28310ae7e41c4d3ee40c0d69; MDD_username=linmeng123456; MDD_custId=M0vuoXP4YTvmLgAHUO1CBA%3D%3D; MDD_channelId=70000; MDD_fromPlatform=307; deal_token=1c76501fc0a15b303132409f76850f4521becd1d3c2dec6a67a0bb4e7511dd5a65ea0e55dab9927ccb; dest_area=country_id%3D9000%26province_id%3D111%26city_id%3D1%26district_id%3D1110101%26town_id%3D1110101; pos_1_start=1610503125891; pos_1_end=1610503126292; __rpm=mix_317715...1610503343344%7Cmix_317715...1610504311215; LOGIN_TIME=1610504312980; __trace_id=20210113101832997221506507002136995; _twitter_sess=BAh7CiIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ADoPY3JlYXRlZF9hdGwrCGsaIKtrAToMY3NyZl9p%250AZCIlNzIyZDlhODdlMTVjYjU3MTRkYTBlY2Y4NGQ5MDQzMjQ6B2lkIiVjZTgw%250ANDQ0ZmIyOTAyY2U0MjQ0NjI4ZTFmNjU0MjgwOToJdXNlcmwrCQHglUis2NwN--8ae08c231e9599f1c5868e6518664b987d936c79; personalization_id="v1_DWS0pDCpXtGGNYQxXPYQXQ=="; guest_id=v1%3A156620567551494069',
            "Host": "myhome.dangdang.com",
            "Pragma": "no-cache",
            "Proxy-Connection": "keep-alive",
            "Referer": "http://www.dangdang.com/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
        }
        response = self.ha.get(url, headers=headers)
        text = response.text
        soup = BeautifulSoup(text, "html.parser")
        tilte = soup.title.text
        if tilte == "我的当当":
            print("登陆成功")
        else:
            print("登陆失败")

    def get_profile(self):
        """
        docstring
        """
        url = "http://info.safe.dangdang.com/Myarchives.php"

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": 'ddscreen=2; __permanent_id=20210113094803223398217227175634934; permanent_key=20210113095520189604544616efff2a; smidV2=20210113095531d61fa7f77301220ac3cc3c6c56f9380400c0f10e74700a360; __dd_token_id=20210113095602962427463568712b30; USERNUM=n1W2rYKcbL0BldFpczSh4A==; login.dangdang.com=.AYH=20210113094833013328747&.ASPXAUTH=2MvACGkGDerTn5Tp8rsE8w27R5p2zF4WK4BEzGX3p46P5QNIpmpS2g==; dangdang.com=email=MTgxNjEyMjQxMzIxMjk1MkBkZG1vYmlscGhvbmVfX3VzZXIuY29t&nickname=&display_id=4071040261431&customerid=6R+EN/yZRafn31Eyjzu5AQ==&viptype=sNyzpZWFNdo=&show_name=181%2A%2A%2A%2A4132; ddoy=email=1816122413212952%40ddmobilphone__user.com&nickname=&agree_date=1&validatedflag=0&uname=18161224132&utype=&.ALFG=off&.ALTM=1610502962; sessionID=pc_b084a0c81923c300b61e722941b6c91a16601ec28310ae7e41c4d3ee40c0d69; MDD_username=linmeng123456; MDD_custId=M0vuoXP4YTvmLgAHUO1CBA%3D%3D; MDD_channelId=70000; MDD_fromPlatform=307; deal_token=1c76501fc0a15b303132409f76850f4521becd1d3c2dec6a67a0bb4e7511dd5a65ea0e55dab9927ccb; dest_area=country_id%3D9000%26province_id%3D111%26city_id%3D1%26district_id%3D1110101%26town_id%3D1110101; pos_1_start=1610503125891; pos_1_end=1610503126292; __visit_id=20210113141826582231466915071218244; __out_refer=; LOGIN_TIME=1610518708294; __trace_id=20210113141853873294882452216829804; __rpm=...1610518706589%7C...1610518733878; _twitter_sess=BAh7CiIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ADoPY3JlYXRlZF9hdGwrCGsaIKtrAToMY3NyZl9p%250AZCIlNzIyZDlhODdlMTVjYjU3MTRkYTBlY2Y4NGQ5MDQzMjQ6B2lkIiVjZTgw%250ANDQ0ZmIyOTAyY2U0MjQ0NjI4ZTFmNjU0MjgwOToJdXNlcmwrCQHglUis2NwN--8ae08c231e9599f1c5868e6518664b987d936c79; personalization_id="v1_DWS0pDCpXtGGNYQxXPYQXQ=="; guest_id=v1%3A156620567551494069',
            "Host": "info.safe.dangdang.com",
            "Pragma": "no-cache",
            "Referer": "http://myhome.dangdang.com/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
        }
        response = requests.get(url, headers=headers)
        response.encoding = "GBK"
        text = response.text
        soup = BeautifulSoup(text, "html.parser")
        p_div = soup.find(
            "div", attrs={"class": "account_right", "id": "your_position"}
        )
        # 唯一的昵称
        nameinfo_div = p_div.find("div", attrs={"class": "edit_message1"})
        name_div = nameinfo_div.find("input", attrs={"name": "Txt_petname"})
        name = name_div.get("value")
        # 居住地
        loc_info_div = p_div.find(
            "div", attrs={"id": "area_div", "class": "mesage_list"}
        )
        pass

    def get_orders(self):
        """
        docstring
        """
        # 初始页
        page = 1
        # while True:
        url = f"http://myhome.dangdang.com/myOrder/list?searchType=1&statusCondition=0&timeCondition=0&page_current={page}"
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": 'ddscreen=2; __permanent_id=20210113094803223398217227175634934; permanent_key=20210113095520189604544616efff2a; smidV2=20210113095531d61fa7f77301220ac3cc3c6c56f9380400c0f10e74700a360; __dd_token_id=20210113095602962427463568712b30; USERNUM=n1W2rYKcbL0BldFpczSh4A==; login.dangdang.com=.AYH=20210113094833013328747&.ASPXAUTH=2MvACGkGDerTn5Tp8rsE8w27R5p2zF4WK4BEzGX3p46P5QNIpmpS2g==; dangdang.com=email=MTgxNjEyMjQxMzIxMjk1MkBkZG1vYmlscGhvbmVfX3VzZXIuY29t&nickname=&display_id=4071040261431&customerid=6R+EN/yZRafn31Eyjzu5AQ==&viptype=sNyzpZWFNdo=&show_name=181%2A%2A%2A%2A4132; ddoy=email=1816122413212952%40ddmobilphone__user.com&nickname=&agree_date=1&validatedflag=0&uname=18161224132&utype=&.ALFG=off&.ALTM=1610502962; sessionID=pc_b084a0c81923c300b61e722941b6c91a16601ec28310ae7e41c4d3ee40c0d69; MDD_username=linmeng123456; MDD_custId=M0vuoXP4YTvmLgAHUO1CBA%3D%3D; MDD_channelId=70000; MDD_fromPlatform=307; dest_area=country_id%3D9000%26province_id%3D111%26city_id%3D1%26district_id%3D1110101%26town_id%3D1110101; pos_1_start=1610503125891; pos_1_end=1610503126292; __visit_id=20210113161121429229768897885402514; __out_refer=; LOGIN_TIME=1610525482269; pos_6_start=1610525529382; pos_6_end=1610525529721; deal_token=1a766012c0915832d15545ef31165842d8921527c75f1b6c8a24d03ecef348a73a3b379495a818bfbb; __trace_id=20210113161329655195456530245415831; __rpm=...1610525550319%7C...1610525609659; _twitter_sess=BAh7CiIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ADoPY3JlYXRlZF9hdGwrCGsaIKtrAToMY3NyZl9p%250AZCIlNzIyZDlhODdlMTVjYjU3MTRkYTBlY2Y4NGQ5MDQzMjQ6B2lkIiVjZTgw%250ANDQ0ZmIyOTAyY2U0MjQ0NjI4ZTFmNjU0MjgwOToJdXNlcmwrCQHglUis2NwN--8ae08c231e9599f1c5868e6518664b987d936c79; personalization_id="v1_DWS0pDCpXtGGNYQxXPYQXQ=="; guest_id=v1%3A156620567551494069',
            "Host": "myhome.dangdang.com",
            "Pragma": "no-cache",
            "Referer": "http://myhome.dangdang.com/myOrder",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        response = self.ha.get(url, headers=headers)
        text = response.text
        re_info = re.compile("var info=eval\((\{.+?\})\);")
        info_res = re_info.search(text)
        if info_res:
            orderjson = info_res.group(1)
            print(orderjson)
            with open("./order,txt", "w", encoding="utf-8") as fp:
                fp.write(orderjson)


if __name__ == "__main__":
    dd = DangDang()
    # dd.get_profile()
    dd.cookielogin()
    dd.get_orders()
