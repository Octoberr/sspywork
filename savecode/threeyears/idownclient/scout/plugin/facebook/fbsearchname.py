"""facebook search name"""

# -*- coding:utf-8 -*-

import html as ht
import random
import re
import time
import traceback
import uuid
import urllib
from urllib import parse

from commonbaby.helpers import (helper_crypto, helper_num, helper_str,
                                helper_time)

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import (Email, NetworkProfile,
                                                      Phone)

from .fbsearchuserid import FBSearchUserid


class FBSearchName(FBSearchUserid):
    """"""

    # "/bluebar/modern_settings_menu/?help_type=364455653583099&show_contextual_help=1",
    _re_helptype = re.compile(
        r'"/bluebar/modern_settings_menu/?help_type=(\d+)&show_contextual_help=1',
        re.S | re.M)

    # data-bt=\"&#123;&quot;id&quot;:100007287519376,&quot;
    # \u003Ca title=\"Tom Canada\" class=\"_2ial\" href=\"https:\/\/www.facebook.com\/tom.canada.37?ref=br_rs\">\u003Cimg class
    __re_searchuser = re.compile(
        r'data-bt=\\"&#123;&quot;id&quot;:(\d+?),.*?a\s*?title=\\"([^"]+?)\\"\s*?class=\\".*?\\"\s*?href=\\"(.*?)\\"',
        re.S)
    __re_searchuser2 = re.compile(
        r'data-bt="&#123;&quot;id&quot;:(\d+?),.*?a\s*?title="([^"]+?)"\s*?class=".*?"\s*?href="(.*?)"',
        re.S)

    # \u003Ca href=\"https:\/\/www.facebook.com\/profile.php?id=100015857955946&amp;fref=pb&amp;hc_location=profile_browser\" data-gt=\"&#123;&quot;engagement&quot;:&#123;&quot;eng_type&quot;:&quot;1&quot;,&quot;eng_src&quot;:&quot;2&quot;,&quot;eng_tid&quot;:&quot;100015857955946&quot;,&quot;eng_data&quot;:[]&#125;&#125;\" data-hovercard=\"\/ajax\/hovercard\/user.php?id=100015857955946&amp;extragetparams=\u00257B\u002522hc_location\u002522\u00253A\u002522profile_browser\u002522\u00257D\" data-hovercard-prefer-more-content-show=\"1\">\u674e\u4e54\u003C\/a>

    __re2 = re.compile(
        r'a\s*?href=\\"(https:\\/[^"]*?hc_location=friends_tab)\\"\s*?data-gt=.*?eng_tid&quot;:&quot;(\d{3,})&quot;.*?>([^\\]+?)\\u003C\\/a>',
        re.S)

    __re3 = re.compile(
        r'<a\s*?href="(https:[^"]+?)"\s*?data-gt=.*?eng_tid":"(\d{3,})",.*?>([^<]+?)</a',
        re.S)

    __re4 = re.compile(
        r'a\s*?href="(https://[^"]+?)"\s*?data-gt=.*?eng_tid&quot;:&quot;(\d{3,})&quot;,.*?>([^<]+?)</a',
        re.S)

    __re5 = re.compile(
        r'a\s*?href=\\"(https:[^"]+?)"\s*?data-gt=.*?eng_tid&quot;:&quot;(\d{3,})&quot;,.*?>([^<]+?)\\u003C\\/a',
        re.S)

    __re_contacts: list = [__re2, __re3, __re4, __re5]

    def __init__(self, task: IscoutTask):
        super(FBSearchName, self).__init__(task)

    def _search_users(self,
                      account: str,
                      level: int,
                      reason,
                      search_index: int = 0,
                      search_count: int = 10) -> iter:
        """返回 NetworkProfile """
        try:

            if not self._is_logined:
                return

            for profile in self.__search_users(account, level, reason,
                                               search_index, search_count):
                yield profile

        except Exception as ex:
            self._logger.error("搜索用户关键字出错: {}".format(ex.args))

    def _init_search_page(self, keyword: str) -> (bool, str, str):
        ''''''
        succ: bool = False
        session_id: str = None
        ajaxpipe_token: str = None
        # url = 'https://www.facebook.com/search/people/?q={}&epa=SERP_TAB&epa=SEARCH_BOX&fb_dtsg_ag={}&__user={}&__a=1&__csr=&__req=fetchstream_4&__be=1&__pc=PHASED%3ADEFAULT&dpr=1&__rev={}&jazoest={}&__spin_r={}&__spin_b=trunk&__spin_t={}'.format(
        #     parse.quote(keyword),
        #     parse.quote(self.fb_dtsg_ag),
        #     self._userid,
        #     self._rev,
        #     self.jazoest,
        #     self._rev,
        #     self._spin_t,
        # )

        url = 'https://www.facebook.com/search/people/?q={}&epa=SEARCH_BOX'.format(
            parse.quote(keyword))
        html = self._ha.getstring(url,
                                  headers='''
        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
        accept-encoding: gzip, deflate
        accept-language: en-US,en;q=0.9
        cache-control: no-cache
        pragma: no-cache
        sec-fetch-mode: navigate
        sec-fetch-site: none
        sec-fetch-user: ?1
        upgrade-insecure-requests: 1
        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36
        viewport-width: 1600''')

        if not isinstance(html, str):
            self._logger.error("Init search page failed, html is None.")
            return (succ, session_id, ajaxpipe_token)

        # "filter_type":"keywords_users","session_id":"5e8b2c170595a9450d7efdedd86f5274","nav_type":"normal
        succ, session_id = helper_str.substringif(html, '"session_id":"', '"')
        if not succ:
            self._logger.error(
                "Init search page failed, session_id not found.")
            return (succ, session_id, ajaxpipe_token)

        # "ajaxpipe_token":"AXjzNayYumU1MhpD"
        succ, ajaxpipe_token = helper_str.substringif(html,
                                                      '"ajaxpipe_token":"',
                                                      '"')
        if not succ:
            self._logger.error(
                "Init search page failed, ajaxpipe_token not found.")
            return (succ, session_id, ajaxpipe_token)

        return (succ, session_id, ajaxpipe_token)

    def __search_users(self,
                       account: str,
                       level: int,
                       reason,
                       search_index: int = 0,
                       search_count: int = 10) -> iter:
        """返回 NetworkProfile/Email/Phone """
        try:
            if reason is None or reason == "":
                raise Exception("Invalid param 'reason', cannot be None.")

            succ, session_id, ajaxpipe_token = self._init_search_page(account)
            if not succ:
                succ, h = self._refresh_neccessary_fields()
                if not succ:
                    return

            isfirst = True
            count = 0
            pagenum = 1
            sid = str(random.randint(1000000000000000, 9999999999999999))
            while True:
                try:
                    if count >= search_count:
                        break

                    url, isfirst = self.__build_search_url(
                        account, sid, pagenum, session_id, ajaxpipe_token,
                        isfirst)
                    pagenum += 1

                    html = self._ha.getstring(url,
                                              headers='''
                    accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
                    accept-encoding: gzip, deflate
                    accept-language: en-US,en;q=0.9
                    cache-control: no-cache
                    pragma: no-cache
                    sec-fetch-mode: navigate
                    sec-fetch-site: none
                    sec-fetch-user: ?1
                    upgrade-insecure-requests: 1
                    viewport-width: 1600
                    referer: https://www.facebook.com/search/people/?q={}&epa=SERP_TAB
                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'''
                                              .format(parse.quote(account)))

                    if not isinstance(html, str):
                        continue

                    got = False
                    for userid, username, userurl in self._parse_users(html):
                        got = True

                        profile = NetworkProfile(username, userid,
                                                 self._SOURCE)
                        profile.url = userurl
                        profile.reason = reason

                        self._logger.info(
                            'Search by name page {} count {}: {} {}'.format(
                                pagenum - 1, count, username, userurl))
                        yield profile

                        count += 1
                        if count >= search_count:
                            break

                    if not got:
                        self._logger.error(
                            'Search by name on page {} has no result'.format(
                                pagenum - 1))
                        break

                    yield None

                except Exception:
                    self._logger.error("Search user by name failed: {}".format(
                        traceback.format_exc()))

        except Exception as ex:
            self._logger.error(
                "Search user by name error: name:{} error:{}".format(
                    account, ex.args))

    def __build_search_url(self,
                           account: str,
                           sid: str,
                           pagenum: int,
                           session_id: str,
                           ajaxpipe_token: str,
                           isfirst: bool = False) -> (str, bool):
        ''''''
        url = None
        if isfirst:
            # https://www.facebook.com/search/people/?q=jaychou&ref=eyJzaWQiOiIwLjcxNzk2NTA3NzE0ODMwMzkiLCJyZWYiOiJ0b3BfZmlsdGVyIn0%3D&epa=SERP_TAB&fb_dtsg_ag=AQxoUUryaWE9SJ1CJqM8PVlidk2Dt5-xE77VaHgGxALI5w%3AAQwQFpGWrn-Jm3kN40X3WTKX0_KL7P5rDRA4ZpI7x3junQ&ajaxpipe=1&ajaxpipe_token=AXjUd4k4QHQCHGV6&quickling[version]=1000902971%3B0%3B&__user=100027859862248&__a=1&__dyn=7AgNe-4amaAxd2u6aJGeFxqeCwDKEKEW6qrWo8oeES2N6wAxu13wFU5SK9xK5WwIKaxeUW3KFUe8OdwJKdwVxCu58O5UlwpUiwBx61zwzU88eGwQwupVo7G2iu4pEtxy5Urwr8doK7UaU6XxGfKEgy9EbEcWy9pUix62PK2ilxfwEx2cGcByojzUiU98qxm2-ibxG12AgG4equV8y10xeaxq17z8oG5E98e8Wqexp2Utwwx-2y8woEcE5a2WE9Ejw&__req=fetchstream_3&__be=1&__pc=PHASED%3Aufi_home_page_pkg&dpr=1&__rev=1000902971&__s=%3A4flcl4%3A12l5x5&jazoest=27620&__spin_r=1000902971&__spin_b=trunk&__spin_t=1562034711&__adt=3&ajaxpipe_fetch_stream=1
            ref = helper_str.base64str(r'{"sid":"0.' + sid +
                                       '","ref":"top_filter"}')
            url = 'https://www.facebook.com/search/people/?q={}&ref={}&epa=SERP_TAB&fb_dtsg_ag={}&ajaxpipe=1&ajaxpipe_token={}&quickling[version]={}%3B0%3B&__user={}&__a=1&__req=fetchstream_{}&__be=1&__pc=PHASED%3Aufi_home_page_pkg&dpr=1&__rev={}&__s=%3A4flcl4%3A12l5x5&jazoest={}&__spin_r={}&__spin_b=trunk&__spin_t={}&__adt=3&ajaxpipe_fetch_stream=0'.format(
                parse.quote(account),
                parse.quote_plus(ref),
                parse.quote(self.fb_dtsg_ag),
                ajaxpipe_token,
                self._rev,
                self._userid,
                self._req.get_next(),
                self._rev,
                self.jazoest,
                self._rev,  #这个要用rev
                self._spin_t,
            )
            # 上面那种方式弃用，直接用这种
            url = 'https://www.facebook.com/search/people/?q={}&epa=SEARCH_BOX'.format(
                parse.quote(account))
            isfirst = False
        else:
            # 49a23d47c921a76cfa190bb40cdbd10f
            # helper_crypto.get_md5_from_str(
            #     str(random.randint(0, 10))
            # )

            # data = r'{"view":"list","encoded_query":"{\"bqf\":\"keywords_users(\\u0025E9\\u002582\\u002593\\u0025E7\\u0025B4\\u0025AB\\u0025E6\\u0025A3\\u00258B)\",\"browse_sid\":\"' + session_id + r'\",\"typeahead_sid\":null,\"vertical\":\"content\",\"post_search_vertical\":null,\"intent_data\":null,\"requestParams\":[],\"has_chrono_sort\":false,\"query_analysis\":null,\"subrequest_disabled\":false,\"token_role\":\"NONE\",\"preloaded_story_ids\":[],\"extra_data\":null,\"disable_main_browse_unicorn\":false,\"entry_point_scope\":null,\"entry_point_surface\":null,\"entry_point_action\":\"SERP_TAB\",\"squashed_ent_ids\":[],\"source_session_id\":null,\"preloaded_entity_ids\":[],\"preloaded_entity_type\":null,\"use_bootstrap_fallback_results\":false,\"block_preloaded_entity_ids_deduping\":false,\"high_confidence_argument\":null,\"query_source\":null,\"logging_unit_id\":\"browse_serp:' + str(
            #     uuid.uuid1()
            # ) + r'\",\"query_title\":null,\"serp_decider_outcome\":null,\"infobox_context\":{\"kgid\":null}}","encoded_title":"WyJcdTAwMjVFOVx1MDAyNTgyXHUwMDI1OTNcdTAwMjVFN1x1MDAyNUI0XHUwMDI1QUJcdTAwMjVFNlx1MDAyNUEzXHUwMDI1OEIiXQ","ref":"unknown","logger_source":"www_main","typeahead_sid":"","tl_log":false,"impression_id":"0pruOeF88rmQRyc8Y","filter_ids":{"100014202395536":100014202395536,"100029364902499":100029364902499},"experience_type":"grammar","exclude_ids":null,"browse_location":"browse_location:browse","trending_source":null,"reaction_surface":null,"reaction_session_id":null,"ref_path":"/search/people/","is_trending":false,"topic_id":null,"place_id":null,"story_id":null,"callsite":"browse_ui:init_result_set","has_top_pagelet":true,"display_params":{"crct":"none"},"cursor":"AbooVydUNCcKZbq-hf_-1RaAL4M8S604c9Op4MzLMU1itx3zWnHvXrEMq3HvasYFUO1d90ECMwqTdmVoMFIaazvLYE0c15PwyjmelyKCpyzfc3trIE2IbTQUrwheRb75lO7a2kttJIahcJ_Z_hV1JV8YkaBhSO89tmH1rOLLfpWofr634HKP90_RvZvgJBT2MbwP4X_CeiK5V8rcpPUhs9GXh7yCnA7IdxL4VviMQV1MxiWFJKP2XhxLuwLGrYTcPQKa1ueqn_BJy_FvuyMPAQXOuwtlj0k99KEofpbeUMg9-XG5bMfTgF9QZH9u0Ihe9e-4NCrYaLZ6yd_YpBNrF75QrUJgiIIKXrGUOLfQfz5ULoy9MFAJhJiobHjSOD3UiM3Sp2tjWWxbyYI_bIjNqXooBCLrWWu6rZLbvU9uB5TlLN_I97Q_0LI-fJ7Hp6Rjk9CoYvZyvhn490vGorNmDwuMv54u8yNu81U_yuzpd5UCxqbU7X0WkFeN302Qh4nQCSCAEt09Y3lP1tpPduhBNqWgp5mRGt3JaumpLt93nGNkYHGB3iPDw8ksDW-JGMFkW22PWIOnovxysFCD8DZqhyDMnNxBlDA4V7VbxXqDHzj20KBsZ8QT1epE8obMcOe9psex-tkMC2GfkYqgn3e2okLx0IVIVp1KFJRuwo9xmwNpLrDmOIIjAv-PoXhOu411WlswC-RcETLuVac_63lu9oXZCifaRMs_lge3OG3MYBTLB6KL6vPL__rd04RkOZjPUeMpGW7ikFB76i_pSXIR7b6mdS9eoSR3MvjPE_8AFNNQo8myVrl-F4DSGP-6o9kNH4nvJgkBfRgYjR0v8KHjhPmvXth4PtdhO5g9jRmAtM220c6xvvsrO6rnFMRBlb4E1WYzrHsrdBN0p974F42dD11AQM8YVYh-vICqAbjrflC41NdoMzV-lWFeskwdq5UaR9ZZb8-IGUh-84qOkED-PuaNNzXajiOFjUwrrqbDjhWK9jdw4mpNq_Ug1knvT4jXS5BR8XqX-dMLVXrQ5hYZFyzhcsxx_52xzEdalos5YOsCC0zdUijHOQyWRgQAkHhqZToySjTj0yv4HGbtet-2Wq0dQzhXyT7iY49uo9J1UMBpfL3iBR6dObWqXUgFNcnAeUGZQ7hkdNdv8Ivtn_2ExSgJ8Y3wlIsJ_GTYtCfzIKkto8qOhfOB48boGpySvmxO16tAGO7s9t6WRdZLeIVDMTeMRYaDONGM25xJF2ANfyARXWSQ-hxYEpZs4ufakYvACOde7x45_8kxbffcVj7v2DcfWykXxe4cXYc95A226LkIoM7Rz_nYNSUXIWyOzGrvR95KD5PYItpAkDKTry0XD951JF1h9bouXAydmVutWqujCC7BQS9HhXss8M1UlP-Tx9iudEyKWTCbW40Vz2K5bjkCJNmtuvrR1JDYKIXs57PNNOscwBzHOVkw0A66G9tnsAzJCUXqQRVG1A_yCW7bWqLAdKZmkSi3JOyXSg71olD1G13cjbbqUi73khtsEIVO6Iw4orOXPf9rF4XF64EJ302SOd7wh6MMqALkFyhRGrCHDT273C-lsStIWiDC3WoNHFAnRHZBalrCW08DAsOJ83NPBr5vTNrceGArwE9W62IRtRqJOIq1w7Yx6egtTOv3qpoRyTtbEE1O9RlZm0AS8TfVtiXtR_IlaBfXlRWZcH43ddVUN7xS0hQUfYwyCEh_0T8","page_number":' + str(
            #     pagenum) + r',"em":false,"tr":null}'
            data = r'{"view":"list","encoded_query":"AbqrmVWavuB_EUxHHpW0Q3fTbINHEEn6eXqRjsP64K-orR5oUcbZBkJFlD3za4jWOvoqhRqoNxZFM_lHeW3fqjbcwzxkCl797E0i-PwD1N4oWKMEx-jter60rkZkFxynUCDoLo8cHg708DCJWiF6dnhcnuXC5zISHmy8AeE9XOgW5wKap83BjIEiphUwXpTXYm3xlA_j2nlRlHav9mK1zgWstlN4TkUFfzutef8KjLn0p8X3JeTsNFw2yXggSf95naO3EZ9hLCHz2hA_j3W3CoSIUKHVzP8NRYz38EoKQSTqfyifZIMLC66iuauvCKO0Vn-7-W2z1B99h_jeXjvlI6eXb9kX7-Acc4mYKwGKFHwELGqQ7U1LhoTrROz2VblaVyhpukqBcc63uY6Mu8sEqh7Cct1GzviKjAJNL576JKEB0T4Hp4W1jgFM4Jq7WRy7AI8v0dBtFrZ98Gvi4rP5DTDX1zLq1I1n9OoZ56Z5LOcPjWIT0u1O6eAul51rxdObkpDPVuYxG96ppuJpJHiMch6-HDLzoXwJJSHJ5r76fiGP8_fV5AEONP7IErUcWYsawYlzR-2rUtxcnT_k3D_DdVwmvJa4q-yif8SLOmaUYWpeEhOFGmwVg90Kuf1vj18uFkWngKvypjs3pThUoBVksz-QoI4HuuGVevkwWWnxIjtR7Yyj2S1Wfj4jiZEgMAkLk_1SdPkIBG168udYyMhyCSdMYpjvfqL6-QTLCykoNt62qejXrfwfcfOC-wwjhzEcG4U39ggkH-ufgAQwmMtBTk6uTGFAg5DKnnd_-p2e6Nrqd-YTSawRk7vGdQVuwSQ5hYEqpymuwXluxhpXX2T1QEfPKJvjL_Xo6iyyqKW87-ixKrvM6J4S-IMqAe_KfkMiA_PY3VTdl80ghMO1B9hEpnQpSOEc7I-aO3uquNxw6tog5fiFIO0m7YRgByvzyu_LqT-jl4ssF06fXlE641AHCSxCIOp3hE-qDeUidDtSaCuxYX7LAd42fs55cXYFjVc7F8JOENEOZ0yf_fBrLUsTZxhijbTVTtLGsssuAg309Q6TjDOH0dBzZfaKfBzuE2h-xC_KcDilJuKlZ6G4fadf62gnmL0t26_4EoeFx1WYrnH0u_mDYorPoNNt6C8ebxy8weFqgqrfu9_pRmVeNMyGXqmR2gla12kOLUeQHYkgsgsD4Q","encoded_title":"WyJBbmdlbGljYStWZWxhc2NvIl0","ref":"br_tf","logger_source":"www_main","typeahead_sid":"0.9395731597757262","tl_log":false,"impression_id":"08SAR7mxLyJCtowNl","filter_ids":{"100010721407429":100010721407429,"100006201437455":100006201437455,"100012791310911":100012791310911},"experience_type":"grammar","exclude_ids":null,"browse_location":"browse_location:browse","trending_source":null,"reaction_surface":null,"reaction_session_id":null,"ref_path":"/search/people/","is_trending":false,"topic_id":null,"place_id":null,"story_id":null,"callsite":"browse_ui:init_result_set","has_top_pagelet":true,"display_params":{"crct":"none"},"cursor":"Abrkgc9lU3w6UtL9LP2tsrExEmJAGbpXW4dqRp5Ue2u2B1dVwieeAN53j8jWxnsIXtQFzfZlKlvMsnzgxUqB-Qq-eDgVHwNlYDrlX_TUm1rMTTLMaTrvOjzhEFkAXH8pZI0O2senP5py-TDEb53EKMfrAxBRt_hWWVjS_wH0ytNcrW-mZzb4AC2UAtYdoWhb6Qp2Z_D917ZXWvE5AArZd8585pRT9ibaWWyr72AAQTjCY6H48cKGJSQBoKR_7POWu--dYYFQDvxB0dWlupqHTI8YyRlr9P0GZxSwsr3KPWLlNkBGZO1YZW2q-MScKkpMqnf-ktJhWikYpuS1Yhw5B8iWgRHIGH1OSmwjX2uT4Q4dsHq076do6xCo8pB1ovg4FUxXOr2vQampnHrr6fSpq20mZT5zhDjpKlLhe8d70Sf6ZfmlL_vMp2xNMeP98Ou3u6xmyYDNtNnW1dTTHHtaAuhehtDbMLKpV475p8-TCu3lAo03iOQ1CS2oqKkvqHdM2muUHIHgzBKG8Tc-gyFasO4p23Wpt9z8NKR4ZGrjVc73DZ-lCm0ncPtfM-MVeKOm4ODd01JIqmTW7d3J_tKlhEKgVplnobEL6Xhwh-gVAL_ENM5NzYDTREPSFO8CcyHPk03l8jjMhdsQtkwLB0sEcpVJfq6iNW8huu_B3fwQzZdGNFaDC0-0uH2YxLAxkj7tSkxvJEbFjfZf_WYJkls63NlijwaMUSEZD_1g0jD7lz2QS11FHaTBAXzno9QshVjx2diuKkbJcVyrYceeM9Qx0krJlbxggd8C4oQFNUpOxxphQ3-yhk4aoiK0NhUeJ4uIDVvmq_PiGdtC8CqcJK2FyAdPf7SWxtXyNJ5wQVAHdv9Yj5A7_uKkZB5Ok9stXaXSpkUKFIo69vAHobKTomDWnZZDsZ_pNpLALu1NSb8RpcACnry3p54GimT9IsZ9WEceOKtMfW5jFywJdlgj2Sy4zN9EgGPveFOa8TZrnOJVteC8Q9ycHj7KIysz1-8tZKDI7aL02LaII31-VERQdSNfC2zWtHUAhh3bg-LEMwA-xFT7GPjFg4lo3JbW0_2uVGfNwg-KiXQEj4xZJ3nsTnvH7vdyoelaJkIgYV25Y9eZ0svTfYjnFBpzxkNqlOFzgkiRKM4L-c9ARGOQ9L7eHkUlbvr7x7OaoV7DZ94pShNIugmNu-3LMNTj58emyPDhbm2LfkI33XAPBBwCWP1sScAp2wXmWEJBd5kQTaY8PX9u9RXLyGn0B24KMWX3T7VsBgBFX54Gt3ruc8qKSRovqA9uYYVBG_MY2CgzQfy7-4sbl1a1fcBp8HKko2o2JvS7RuaEVlY6PcHKd5Zbs8m0-fw864r1OCiMtxOVEo7oym7cqBft7bF_rEnDYej1jhedAPG85XLQD3QuAAJoHQdk3zFORL4DB1dbk4lSFZMbDDIAT5Rb1OCZKRl80U8wzyfbINeTfUztr2eH6OKm1dctQ78st8VIYP3Y_Z0-3ejdy3WLpBvD-x8xdt3MLrRnJy38q_u_87oYCQGJLHYo3SrJLQ6n6j3nzfrG0wFKhwn7hFIe0LIb2q__t0tax09pQuXeW2JBbiYokJc9-kUUg7NTkJxS_QFZuTlm3vQ77NXtbtWDwSG_ubnY0jFFO1tw0IptIaYWvp4HtYFH0fD72FAHMdaciRQm6AkxduvP552AfgwxhiFY4sC3P0NHYZ7jC0o3U_OLIAMSpRezKu17TFmhzQAh4t3xACOIeOF3gtO8jLTx5p2n7M2SWRUbYPaj5eH-mD3pKd_6R5PBEOqbJfTqa5oiuv7A4YyvRTGqvS5RdW_ehcYBVu9DTV-nOdffltAl4nk_iWOOvGxk5uG1zXdC3Gw39g50PollTZhLJJrajY-GVdBkCSIm-3Htg3Uw7EmXlNTriUdf5XSKPtYib7IUEBC6cZT-_z4lAikeafzOzdSCczhshwT9HEk4zKie0uW5TlilY4mlmVE5NDyr7ny7U24u0-H6VPwNfwt7klaOZ6J36Ihaq4qd0FJFg08T5jUSxI0QrP-Lr6Vyv2qbnniqv3ZhZZmBqBR6xL6NeFXhUU87Vf_Uf8D8tuB3yPzZQIdCwMHcR1pwg5I9JKzNLAMtz566jjZN","page_number":' + str(
                pagenum) + ',"em":false,"tr":null}'

            url = 'https://www.facebook.com/ajax/pagelet/generic.php/BrowseScrollingSetPagelet?fb_dtsg_ag={}&data='.format(
                parse.quote(self.fb_dtsg_ag)
            ) + parse.quote_plus(
                data
            ) + '&__user={}&__a=1&__req={}y&__be=1&__pc=PHASED%3Aufi_home_page_pkg&dpr=1&__rev={}&__s=%3A4flcl4%3A12l5x5&jazoest={}&__spin_r={}&__spin_b=trunk&__spin_t={}'.format(
                self._userid,
                self._req.get_next(),
                self._rev,
                self.jazoest,
                self._rev,
                self._spin_t,
            )

        return (url, isfirst)

    def _parse_users(self, html) -> iter:
        """return: (userid,username,userurl)"""
        try:
            if not isinstance(html, str):
                return

            matches = FBSearchName.__re_searchuser.findall(html)
            if matches is None or len(matches) < 1:
                matches = FBSearchName.__re_searchuser2.findall(html)

            for m in matches:
                m: re.Match = m

                userid = m[0].strip()
                username = ht.unescape(m[1].strip())
                userurl = m[2].strip().replace('\\', '')

                yield (userid, username, userurl)

        except Exception:
            self._logger.error("搜索用户出错: {}".format(traceback.format_exc()))
