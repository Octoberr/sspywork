from requests import session, Request
from bs4 import BeautifulSoup as bs
session_req=session()
postdata = {
    "user": "sepjudy@gmail.com",
    "pass": "ADSZadsz123"
}
loginurl = "https://web.voxer.com/login"
req = Request('post', loginurl, data=postdata, headers=dict(referer=loginurl))

prepped=req.prepare()
resp = session_req.send(prepped)
soup = bs(resp.content, "html.parser")
print(soup.prettify())



