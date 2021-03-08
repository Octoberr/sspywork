"""
验证手机号是否注册了亚马逊
20181023
"""
import time
import traceback

from commonbaby.helpers.helper_str import substring

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidershoppingbase import SpiderShoppingBase


class SpiderAmazon(SpiderShoppingBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderAmazon, self).__init__(task, appcfg, clientid)
        self.account = '+' + self.task.globaltelcode + self.task.account

    def _check_registration(self):
        """
        查询手机号是否注册了亚马逊
        # 中国的手机号需要加上+86
        :param account:
        :return:
        """
        html = self._ha.getstring('https://www.amazon.cn/', headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: www.amazon.cn
Pragma: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")
        html = self._ha.getstring(
            'https://www.amazon.cn/ap/signin?_encoding=UTF8&ignoreAuthState=1&openid.assoc_handle=cnflex&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.cn%2F%3Fref_%3Dnav_signin&switch_account=',
            headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: www.amazon.cn
Pragma: no-cache
Referer: https://www.amazon.cn/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")
        token = substring(html, 'name="appActionToken" value="', '"')
        to = substring(html, 'name="openid.return_to" value="', '"')
        previd = substring(html, 'name="prevRID" value="', '"')
        workflowState = substring(html, 'name="workflowState" value="', '"')
        metadata1 = substring(html, 'name="metadata1" value="', '"')
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            url = "https://www.amazon.com/ap/signin"
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 10765
Content-Type: application/x-www-form-urlencoded
Host: www.amazon.cn
Origin: https://www.amazon.cn
Pragma: no-cache
Referer: https://www.amazon.cn/ap/signin?_encoding=UTF8&ignoreAuthState=1&openid.assoc_handle=cnflex&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.cn%2F%3Fref_%3Dnav_signin&switch_account=
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"""
            postdata = f'appActionToken={token}&appAction=SIGNIN&openid.return_to={to}&prevRID={previd}&workflowState={workflowState}&email={self.task.phone}&create=0&password=654321&metadata1=ECdITeCs%3AXERdsDau92D0U3Y%2Bpv8Q7SFPHd%2Fq37%2BLiHcQ%2BOCXdToGTc5xv94%2Ff1%2B6a0CxiIqVv%2FMjvKqE7N%2BzyRMVzizt7XmiVd4JKSaW2UtqXpdUrzl6iiXGVBrt9uGd4MNCCrdlOA4J8og2AAXhkcX%2FXfhryDLMOqneLpnTYayirlFN6U0iB43Cz%2BQVlvretMtIN2g9CIHeHgIVFFaZjgrftxMAHreTTcbhzGA54qUpCi3AJ1JOnrPny3EXIbAnLurr2B7EjGovARYH4GmByXGes%2F9IAIzNe72TkeQZxjMirwbkq4gpqb1U0a8y1x%2FZiiuaAj8MIxZZNCXkPYaW5kx%2FgWDXcaGZDW4dTZvIkAiQ9ffJuXeCqaZ65ebqZtUadYfqk6g4InUwa1HaKjzXy5%2F83wUM58V4bHVDhqBlRFsgofW1NU2lPLS%2Fl3tM883vVKzajekFBa1q9BXbdUbfGKqQn33N0lZ%2B8fqI3lR75sIeh403QmPOoDx88mbxfs4E7HFNzPuZ84coELXLJltmmKkhfOfz6VL2dBJ%2FRZZVekRA6MfdOFXujNLMQH%2FyHXzKfp0tA4vVdPQmFniW4SKWCZzecQcDb%2FA2X59cEGqgAJnbG8dkj%2BrsRHgzUknivVhIX2Cx1aYJNkPFveGSEPTl4Fn6s0hL9gEvI9r0akC0w1gSwp6iBYvTX9W0Opwjm0eQJoyXimMAKxgzswwmcRChsSq83LTmqjM0Ia7QvxdID%2BWrhofUpK%2FKJkGE8WHC5FXC1zYRyhUQuNdCMVhN2DBZVF37%2FZltBzY2p1SKsLtBIHNfnlru%2FX9wqy16FRCefJNpACg0XIrJzByG%2FNqcBebu5jeAuAtDylNLUHBikACOv2fc0B2WIZpqaFtdxIeazJk343OrU9Ui9mZ4Tq4Gm%2BV4lWdyTqn4C5fbCLRnNG8UMqVhJJx9lEt4F3BJCsjWZCGYpcfDR4mlsmEwReKy8e3T2CCz%2Bg0%2BAjxUKFDPaTdL8szMgw1aSc91sYCQkvEI6WM7k1Z%2BSeOGHCSgUSi0TzXkXx5JDD6ecjHFdnpfPpKqTyNOp5n3iU8CGzYqjv86U9yd0RKBCVREYHUG7nf%2BFUEdPIRLe5Xyfh9V%2Bgh%2Bbl2iGfRrnRtyFLN%2B7nrYOEgVqxgJ8eKMkum6sMDJmrAiH%2BgOLT1zVuMbxeb6sBS%2Bta7CO0wYFdh8iPRReaAAwHsw5qiXsoo0zMgcICixOLYI2EI2BE0%2Fiit%2Br3FEvUYMIoaxv24JFz5csnKNcpvxa9AcHRLNswyjY82eJ1mptx5Zhr%2FWa2qOqv0a0vxT997L8SVaUfWZYemiR%2Fa6gTNphjtZH56Y%2BZP8ffDxUT%2BPKtr1UTur2%2Fb18drU9MP5xaFwxerz%2BbBitJr1rO3ei83Drp6hvT1NP8XQfS87ylL3Gliivj8A1u83Njtml1M6EwggaJrJ%2FFH8boyIfBjW7eGBxQyGRJNL5A73c7KMJu%2FIpnoD1zrWEC%2B2vGwT4ME7BKCzgy%2BWewjl90hxajgNc0yxAV5rzF2ULQ62MQ0lglWNVUB0wORQx76zm34MAR3VFSi42uWgpFag9ypUvNJLW0D1OT2bmVg73XRXKeM2Qe2G0mQNVU0KimFonCtE1bAGKqLyUM5DjeHLWA9mdIh7TkGYTfvDlSKmvIxXhvxe0P1mzuRqCTMbH0woBCLsB84i2pE7vI5Dx4Wk5GSo1SsDLlYyfFXbxA0KaJL8rexUAy9oZ0dQkTweIZV7lskwH8hOvhucB50hTUnimN6ckRETcDk56w7u4DRmx2uM%2FiTLz9ydw27ynL1S1a%2BErS4H%2F%2Bj9sbj08ll3NyuGadzmmGjrEHxpMvwKk40l%2BPoL8dGMiU%2FDqgRzNdgLMNkDA3zW0YbvP4dMtP8B%2F2dBqN8YQ4Ab4fXABlzfwys84GeP7EnQZ%2B7i0YN7QEIxb8uJrEB%2BmPi2LVxwC47r%2Fmo0i5p%2Fv8WC2ePAlF5fCciV0NNyyuUR%2BSDeKTHHaHI56P8ZXtzGQJ80KtbccQZQLttQSuOnelHuEo5nDn41HmvqD%2Bw4Ja3%2BTFtMS%2BK4FDxRJWvUzub%2FClQaSLeV2xt%2Fj9kCjOrkAA5DiCA2voQyCW1etRmihw00KDRsA%2FoufS5QcPCM%2FWtii3%2BqvlBS%2FAgj9%2BM9xYQ3XdAOJ8h7pL2YEDHG0E3drvn0uEs4696UMWXvyYGiB490fMoh8LlewNCbGIYdGInpAgbZ7urltye2NDCCa%2Ffy5JRP%2BO0dfGx68BSdXpZKafWFl8qjlShEHm7D6yXwZZhlXkRWSXedUTrQQAZ19nYvLLphz%2Bzgpcf7hqefW3GkOodu3zMTlx%2B%2FSfixuyapTTo%2BzmWEx46QS0j5KFCBoMwBQDZ%2BdzJtfLkq9gCVYoLscReSLPjMo4Vc82qAsCrFrQ0qCfMVfVzxXtczVd1m5nEpgY8FO5hq%2Bx%2BhYaK4%2B4yb3zLdP49yedSgLHsLgw3ph3vmzGNq%2Bax%2FeN9SZ%2B1zAr8M%2BoDogtkbc%2F18edil9QtFf02g6v86rbYOCLQzeUPwKb%2B9BB6VZFW5vcl5s1gTRp1gDwjXhtQR%2BQFvSuu%2F5udUHLwjNlmeqOC6bXFDyr8BxBaaXxvnKyjJrPrQYJ8XpA3JZJvoUdF60epgmVjOSFnAYQNgPoBDYUf89XfukJudPyR86c3W2%2Bo%2B31Q%2FTkjbpUjl73TRQFESxxGUw%2BgMoanlmBLebUh%2BUrlApc04w1IY42NeGmHU%2Fj707%2Bhcqt%2Fxs7%2BEyfp9sHUacrincJeFPhCR5vhfp4RRM17Bns6XF%2FY0fPUY79aDbv5EVGg1QKx0P5xTAeRH5GI8evF1doFkSdrqBosI4z%2FFhA6ruSxqd8AmfKZWPNUpkQxit12D5h1%2BAK0GN9Su%2FdITK0kQjw2FUMKI4VO61qbDrZ2TWI8qFDY5lzegznSw9Zs1%2F%2BMA%2FEC%2FW%2BCmnp2UQ%2FtjKRBfvzZnQ8EpYnKpVm%2BWnFAI8%2BHybPnRfkvNvdKMbT7s0DPhX4NP91Hr4liQjlsnvBN0Si0Wjrh9d8zyZs5J7azMrkH0f7PZB%2Bw0C0i6nbv8FAIUWiUlgBiFerU2ulWyTm0dy%2BQmKAItKKEeyP3GKIHcgjNsh7OULEACK2F084AdQQjdXLusABy15w2YeQBO14HptNpIfHeeLsMS4sjUlElO4%2FkAi5C5YDrBQwDsi2y%2B51x7BAGQWOlHRemeKKClTtnYJ%2F5mt2QMSZw%2Bqw3t%2B2tirkpqspFtQP3V14Wk%2FAyvn%2BaP5H10UnxxEKdpgdId7bhu2G%2B7LoCwiMjK8fdfXVWgWilcYk7kiwVxYsS2%2FOw%2BQfiAGi8oKnz6%2BiBImI3vooycHvpLXhFtjXyupGhM7PIy6%2B53WV6MWUBHZZ8Iu2FOQEvTsEmX5HikpHEb6QqNiuvuyS1xRuNEyOuJ2%2B284c%2BN1%2BlqPYkNWE0wkh83lNOVMlipoTf0xY6xeJ0bbQiS1TqtqgVrnn%2BhjHv%2BEdiJuwHv%2BC6XZF5LVd%2BltF3ZwWNxe19z7Z5jqQUcZZDZiFP5Klr1tRD98kZpcArTW0TL1oJ%2Bu98qeSlGQTuOFINWyWIgNGZj6q4YryzdKsj2N%2FX3a9VD7wyCeaX%2FPWvKkegFtnwyVv5QQu7N2P0j9lTSchMvoZpJg4ZXoylfNnA0TU1ej%2F7h9tak4HrP2FgWYhQxCJLRAjK%2Fq4XrSlOmKXmK53gt2XPrIGiBZxlrzJX%2FEG9yAjBS3zoXKqGL%2FKuAwXZDiJSn1nETPXSYLxWyiJdB8aduPtOI0OnoOmLutpq%2B%2BwGYuMPTN%2FxQAeiE%2B26DuscxaSXekTxRuPRnbFPkmku4Hb6tJkyTSdF%2BXUqPfIhDSqwP%2F%2FEFwduaAmsj9XUFnmaFwKe3ORRmn627ZTIwp2oIFmz6IRgiLPoKfgpgI4SsIR4K9A%2FARuiYAeypHwfmQTygYCdJSNAThIO3BOTLsUQ2VGcTO07py6LIBegv1SrpffFtZfjWjpLvUTZNjMy2fQdYmR1xBtdzAxjF2Y2RvXZ2CMsqXsMdq%2F8oT4iBacus4Kvzu%2FL1YsPAm8YLulgQjBgqgr6Nn5J1L31r05jqpWIPChCYtFuSTXNxVycENRhq83QLjLMiV2W6FqzwsWzdmrJ7%2FUpLNaUpgyHYojl4QJAefD0F2pawaxUZCl4kAQhbEIgehTXmDTbo2jYdjiD43CWmEonfc4DheHSI02oCOhl2zhj2rDj%2FiRkTJ9xTULtBhoQy50WIzMZxnX40xCckGODY4i8ShQNEu2KjbLHwGw%2F5GFccYzkvMub5OiscM4O1Q1VcHOs%2F1b2WXC63OqrzejIVhViBjpjg0hp6164k5QneQR4%2FP7mKb31d1h2Y%2F3J%2FOhVMIHejIJ476EBVgVbz0tB1gz%2Bdo9us3GrvaCnCWS3UpFlqsRmXJlxpp493tyaTJt%2BjyxPF5IE7vYEDvW7rMG%2FeplmpyUdutn6jUd6cimeb6RILJ%2Bvg88%2FtoTGrmrZwyz85jUdEcctNonmSunBdgUV5dXzhLbxU4v7zP984V5FBPivbsqoRsX4Hxz6loyzWiZJAxP%2BNavJBptVFQXRh2JSIPWmpFQrmhHbRsjM7KtNkw2qTwweVQ9MTSUEv9pexbaL394fNb3DRGQFnjMfyfYXMTEf5rdY0eR7i4Tu8kCCzzXJVdcikBmPP807RqjuKN6dJzR1nTS7pL%2F2hYDbW5HLbR6VUgtWT3qiLcPdUx1akC2%2B%2ByB%2B%2FgJulgVi6X2u0R1efXQE3JWEr8ryuwY9T8d4NeqW3Am%2B9uqMrNks5f3Czj97uFRd14zEbCls1fYcKt%2BjzSImbEGXI4lfUCwKUW5bVUaJAg1nVoY%2Bs1K2Y4yxhYLCC7gm8YIxgHviXv025fgJQyQyUbmo0Mlqis6XQ0rGsBwBdtGNRihOVtlhzdgV%2BWHiEImi2R%2FGnIOdWYrv6h8MaxZYuJQhs3n89imvbvzGWNNeIXN0LAXlEcPQg%2FRMvQHodgEduE7ksF9zH0QJV0k5GfWt6qWyzMegmw9XPfNvPqOdOKb5R649dm4fQG77J1yDk3RbqRWArN9Rwr4h%2Fmd9bdg1aagoieD9kals9GwAuw661ltUniZzmqhdc02%2B5CVguH3A41LBKKrWTeNvagkYuLbc0tQfIcMXpfQGpAp57IuG9ZMaecmtSW1T2ltU%2Fu4HysegnJZxjET8EMDgRly1DgSSI9NIBtSsBbZx4aBaPNz2CTbXnPgtaD%2FKOv7Lso%2F16OQRRWPakQ3J79A7wZNO6IWxrNEDEVk%2FVdPo9z5cPPasZFv21kAfAcRVtwu4qChBKn9J4dnJ7SKr6gc26jufMIcgkXxwZv%2FJxrB65QbNR3pJXX%2Fs7ZkV5YzRyz5Kc0YgqTKsH9sfhuTmVUddGOPeMOLn8WSnOCb4x%2FCFrc%2BO3LCfXQtTJQh081WZfGzar5SAeQtpe%2BtdZPMxO%2BUvbhmn5%2FwB5b9EfW7GSiMq%2BfnOSbWdI6NCXAb9C5K%2BidB89S8j4YVCUQCzx0a3e3Tq7iVOLIclpGpbdA3bvUrXCpa4fs1HOwljpkrwlerdSKMGrgeBrzM9NK%2F95Dsz0qfjSCc%2FD8X0o4EUuSXl69eyPOUhHi6gDaazv27HBR4hQaGybFbHqYAwGncdSZaj1cu%2B2c9LvuaXu%2FxJYBp3TVWRKy52mwOxXffpONSji7XZEgFwIS4IpESPFyxsCBOwgDHitxuxGcMWZJ79oW%2B5mzEnuMiGlxcZrpwf6xv5cubyjBkj6jREDFSLu3kRMB4hk2MToxjd1uVJJubbL0y9uy6LCU6oiZ3mNi6UUaqzyI8oWUx79MG7z6PVlLT7FJ0kDD52Xj%2FllTTxCTQrOmHr%2FO2AdCgaChLW8zQ1pLM5C8o9ElKvegdadpJj%2By%2BU7k%2BMe4PQI0kw1ULG7DMNYHLWNbf5BuHtWMknLgNWp96jHxPneJdrndWrsokPltsSmeSLcOtIMwa91jhgyAV7jiGVFnKfnYnejjeNjlsvgoFyXKSKSbkXDA68DSHlkCzm1DUNnFiiSLlwR12dnDXGeZUU%2FGT%2Bn%2FLBLnDsxWa1QDYIoyHO8kGZkSFKy5Y88qK4QuXec5bb8GoitcBcdF%2FZ%2BFAxAex2JkmnGOPaS9kCr41SSzGT4bqCJobH7xMTcDVelWzgmnx9eC3RE0iZ5UTPHZ6g5DnUtkyyWGN3HV8dBmSK0zhi6%2FDvMLzVcoWIhv0q5oqbAJqhWX%2B1FJIQ%2BJqpa6V9K8bFt72cFBZStF8sRp9jf%2Bvr7Pps%2FajAM%2FD0fS6nAMUINS9Sgbfi28RNBkIAeTagPB4iDN9J1jn%2FqsB%2F3zvaCzLceb7pF%2FktUia7RVSnQO2H%2B3RhNsrksPfiQeoi%2FU9AqliCEjFJt1dLArSLRF1s5CiZMDCrCgnhWh4W%2FkCKTBCMiBOo4Kq6SBwL%2F6nRB%2Fkm0GD%2BDdL3el6r0dR0CzhvAEOy6FRpsJtnBJYFHiopF4bnD6dJobxSHBQ%2BYKxnfHxNGSofk%2F3m2YPvPjwoj76fO039UE7EaNYjhO35y4GoiwBbY2r%2BRpgylA9uOCl8t8a8Iu7i%2Bj%2FBVflB5naHf%2F1fdg2tiNGgFSaVhEoTzkJEryDSKnlYKNq9KYhmgX%2BLeG8Z0d11rTge6mq%2FnhwbeRCxYHYv9lSwtOOIVNGo9zv1vSwBPAQDJPK6Co921pfb7O0IghInaaU8VHcY%2BiRaFk%2F%2BtqHJPaTBExtv8bg7NSUWwZW%2FiBSES%2FME7%2F3fDGxu0rzfaawaJAZfwYFgCVHUAUIofnMbk8PNXHhrvbtd76oUcAsCRO0%2BUafyULklIAYtawm1VlRnY5J80uKAJWRLBSNOcz9vWk%2BW0LcvKrQVknZCDoE%2Bsph2fRHmV1rs6mCMUncENCBd%2F8IQUdv8UNnN%2BKbZajVrOFnQFSB0ejuaLdnrfQbZaCpZPewcoujnB2sUarhks6eMQPkJO4mU9uOg59gyM3TSL8%2BMVOsB8hXqs6%2BACgBph16Ex6QXrdg6F37uWx1JoY4geGmJvp45OAjCCOgh2c1JPeCQKS99h2HLVErCWhoiIjlDiD3RW8KCQqnXDp%2FyovHQZ0eTPRbABYpOlj8F38XYUKwyuOAF7r6jhTns5uld%2BXeh9rGlm4I%2FOSSACPnCvOg9%2Bibwex%2BHEmk%2B2xnxmvAr5v8b1aoPe7Dx%2BvUQBW82%2F5lpVvbivq5q4x1n7SXxzyhDTND3M%2FyR2ylAOnEh7BbVgJsPvSOzeeaMcUb6y4XUOUsEO1cBn5pjGPg3DuuK1j2Hyis3tz1kMdWrh0c1N4wgnJC05dwjFajJwcv0JXoOFfv%2B7FUGbjc1YpLgoLTRdTkW8O5UY8CBoBvqGpDKRwkATdKKj%2Bh3O29KWLpYyVrxliEQXetM8MUXU2M%2FaT7Chg6ORN1mbUghnKvVHlpb9SCqIMdsTK0Vac7UI8to3RglR6hhMFlB3RN4rkO%2B%2FbW6Ym3lsc4FEVzyY%2F0Rw3JqNpRUavBUSgKFSojcFtK4cRyBwD1%2FccLkL8VsH2Pr29LIKdCo57JVG%2FAVcP%2B9G69%2FpjM%2FxKj1gwa8SMMGuOiz6Z0dpSJSvNjAPXxt2vQZNVmyf22N49hk3aIpPGOyLnbgCKkWuTitLrH0Ib2iX2gVIDnbptle%2BgR5SV79H4%2B8mTxQuqqEmN6A75xE8PykgB7Eus%2FqGoREb%2BZ38GPtCA0tqKRhvG6PTpCS7W9K8HOVAUGr7BRtl2eH2v1n36%2Fgn14SljxKuJO49unOnfCNQl6b0ef53vrHhIRRbzW5Qh0TLWgg26X68tIRqVIT%2F%2BM%2F2xc%2FpzeTZn2RgiU6zuGB8J6xqqSL7AzR9SqAd3jNpIQ4dHjc3cDHXNN06LNrkuIDJ5cCg7Fh0vcPvdemtJMucKsSRjRuvJlvnS2Ciq1Y23K3knQ%2BShO21ERWZozZPPdgo5Y7KyrZfWirEUX3Fud7RHfOGJEUPjL%2BL5PN%2BBiBG4Daq6afIIJ8hfP9uvYv24oyY3fPTTJHJKQO5Fsq0beHn8Ccz3yo0e74KjyFa9zRnJMY3z7fi3RSYXnxu%2FlU43GX2McIJSycz8q7iMcJ1JhHk5KTm9CNlXQ9kTymzq85%2FHCKHRwbnYIIRPByduVLMdvYvqR1xXeNcnOfsDouV%2BkIV6MJFv1VLihjtBDTfF%2Bm3kZ3%2F2EMjdYeefBuMVSFaUVJ6fKq1uxBytCDBuJ20Prt7bF3rPCB8SatLV7%2B8OtWVxRv6hdy8shxixi3ORJy0jH2bj0uaJXxEvblxikHJC1eQyXPbCF9Qcp3YQTiz5JKIsHLnWsYcAeBM62zP4%2FTAgj4LzYBF%2Bp5Sn99wvSdjhecDWJY%2B4ku2ogyebYkyCof2YjYguors%2FX%2Bg2o%2BsL9VAJPdzGph5uQf1bEtze9va8tgtIa8Jh5pP%2FabF8pMYOsty7obdemqRr7Oe%2FVLNsGyIbqLNz%2BAlh7iVbKXBN79Lqp%2Bm0P%2FsLBWDC185%2FjRaL4ehYvA15Mwr1SIPnUaifv64CoeJiCTGr2mQIUosZlPbCYc6%2Bkay1HychQ48BgeUhtCsybfNgzZzJ1rWS0lhXSwSyOztxaz5dpAZty%2BAoTQL8U2Ns4RSyTpHsv37pzOtccjXXT4u3Vs0gwMrZPjTrh98hYKlCm0oQmQYtsrkw3rqToH8bmhfDug13sWbVUNKdi9Uf4ThEmC6umIgMqUz1zSIJLwOOG9cjFMt0oofC8iPLJ70vvqxqB0Sa%2FwYMxlePd6OIhkuVpdOmOUeV4noy1r2NpIHcRG1CZyOVc5%2Biec2ODDZYRm4rsBUeH1daZGxv9EKJB2y%2BZc7jcazg62IKDkOT6AW2YP1jjtNzQ5xRRsZwSs6820OR6QYR51ixTMChPpL1jEmFi%2BFQ7SfUgTtms72vFA2h0NLPCJnxdvi1aJZTybReBgRaRPwGjiKaC4zPXO7u5aVgUjm2OBrSx8pecb7ptAcNSyI7mgpnN%2FncY7P%2BLSXvk53RDoCBKLSMJBeSTfTzP3hOJHriGFi8YlndesisOuEgCOQd3RgDm2aY%2BLEyfdgNa%2B83cITaxJS2PHc0g%2B2X1J8VuzIft47UFEVGVaIuLQ%2FxfRv6W%2BmTSPixe5CBUJtik5pNus4RCoCr%2F93n9h1e1fei7NHb86bJkVup6mq4ZL8wUlK0%2F%2FTUGvM1RAB0fmEyONZCBVLeGfACtpKGhzkQhQCjSpMNRbAgqraPIswtavDDSMQD25dxaiubMJLHqlECfkBHf8PLMbyxo3zWTtCwcBlwouPUzgBOeUR5%2FuSCDcmeNojDfO2X6eBmechMD9%2BVmf23OMFBHGz9Td%2FagEQWtM%2BbjiCCuI3Se7ISx5Dr7ohErLqGpb1X5Or9opY0qKiolEO0Xuq5hSLdK7OnG9J4mqRrq1pXWC4zKRN4otqjP9e8WX3u1xy2xAvFNyg'
            r = self._ha.getstring(url, headers=headers, req_data=postdata)
            if '密码错误' in r:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Uber check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return
