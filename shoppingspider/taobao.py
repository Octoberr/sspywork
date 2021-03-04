"""
淘宝的功能尝试
"""
import requests
from bs4 import BeautifulSoup


class TaoBao(object):
    def __init__(self) -> None:
        super().__init__()

    def cookie_login(self):
        """
        docstring
        """
        url = "https://member1.taobao.com/member/fresh/account_security.htm"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "cookie": '_m_h5_tk=9a6c9658ade935840dbcd372af53fe74_1610446528632; _m_h5_tk_enc=aaf811ace7cb73fa2b80e2f02383f1da; t=9dae347b4fd55f2eb95fecafdbca7163; v=0; _tb_token_=ef3eee1336b1f; xlly_s=1; cookie2=163ccb4279eff4086c4f941a22bc3f3c; _samesite_flag_=true; cna=ZkmEGN93amQCAXDBMU9uB1Nz; sgcookie=E100kaR982joXYBveTTl9nhajiqTHzCbZ34mpafY4G5ZkQOr9RLWuVlDJT2ZXpYpcB3F5LhnnoDxLaOKofYMNR9VVg%3D%3D; unb=1831188414; uc3=vt3=F8dCuAFdYcZOb74Ul%2BA%3D&id2=UonYsJWYEbDKTA%3D%3D&nk2=qTwMGDW%2BRpMUSw%3D%3D&lg2=UtASsssmOIJ0bQ%3D%3D; csg=aba04142; lgc=%5Cu5341%5Cu6708%5Cu54E5%5Cu54E5%5Cu54E5; cookie17=UonYsJWYEbDKTA%3D%3D; dnk=%5Cu5341%5Cu6708%5Cu54E5%5Cu54E5%5Cu54E5; skt=144601eb94155eaf; existShop=MTYxMDQzOTU0OQ%3D%3D; uc4=nk4=0%40q3nVTfQccrdbIx1VOy0B8oLDXITO&id4=0%40UOEy134Tlglv4En8aaOvGy664u6I; tracknick=%5Cu5341%5Cu6708%5Cu54E5%5Cu54E5%5Cu54E5; _cc_=UIHiLt3xSw%3D%3D; _l_g_=Ug%3D%3D; sg=%E5%93%A545; _nk_=%5Cu5341%5Cu6708%5Cu54E5%5Cu54E5%5Cu54E5; cookie1=UINB9M%2BcxzLI5oMh%2Fd9LAnrXi%2Fh2RlcHPzL%2FgF%2Bk%2Bq4%3D; mt=ci=0_1; thw=cn; uc1=cookie16=VT5L2FSpNgq6fDudInPRgavC%2BQ%3D%3D&existShop=false&cookie14=Uoe1gqzHK9VaoA%3D%3D&cookie15=Vq8l%2BKCLz3%2F65A%3D%3D&cookie21=VT5L2FSpccLuJBreK%2BBd&pas=0; isg=BJeXuiy0hBNqFwCfgowoVn4mJgvh3Gs-Zva2YOnEs2bNGLda8az7jlU6ergG60O2; l=eBrz6DbIOq1ucBhtBOfanurza77OSIRYYuPzaNbMiOCPOQfB5XsRWZ8C0P86C3GVh6JvR3yEBP-WBeYBqQAonxv9v7kR5NMmn; tfstk=cBmOBOshvBAMZVwKUVLhlN9d-Qdlw4dYOONcDLJ64g-SsW1Dh0m-PzY_h1Epp; _twitter_sess=BAh7CiIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ADoPY3JlYXRlZF9hdGwrCGsaIKtrAToMY3NyZl9p%250AZCIlNzIyZDlhODdlMTVjYjU3MTRkYTBlY2Y4NGQ5MDQzMjQ6B2lkIiVjZTgw%250ANDQ0ZmIyOTAyY2U0MjQ0NjI4ZTFmNjU0MjgwOToJdXNlcmwrCQHglUis2NwN--8ae08c231e9599f1c5868e6518664b987d936c79; personalization_id="v1_DWS0pDCpXtGGNYQxXPYQXQ=="; guest_id=v1%3A156620567551494069',
            "pragma": "no-cache",
            "sec-ch-ua": '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
        }
        response = requests.get(url, headers=headers)
        soup1 = BeautifulSoup(response.text, "html.parser")
        account = soup1.find_all("span", {"class": "default grid-msg "})

        if account:
            self.userid = account + "-taobao"
            return True
        else:
            return False


if __name__ == "__main__":
    tb = TaoBao()
    tb.cookie_login()
