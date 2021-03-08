"""test httpaccess"""

# -*- coding:utf-8 -*-

import os
import traceback
import unittest
import warnings

import requests
from commonbaby.helpers import helper_str
from commonbaby.httpaccess.httpaccess import (HttpAccess, ManagedCookie,
                                              Response, ResponseIO)
from commonbaby.timer.timer import Timeout, timeout


class TestCaseHttpAccess(unittest.TestCase):
    """"""

    def __init__(self, methodName="runTest"):
        unittest.TestCase.__init__(self, methodName=methodName)
        warnings.simplefilter('ignore', ResourceWarning)
        self._ha: HttpAccess = None

    @classmethod
    def setUpClass(cls):
        # print('Previous condition for all')
        pass

    @classmethod
    def tearDownClass(cls):
        # print('Post condition for all')
        pass

    def setUp(self):
        # print('Previous condition for each')
        if not isinstance(self._ha, HttpAccess):
            self._ha = HttpAccess()

    def tearDown(self):
        # print('Post condition for each')
        pass

    # 测试用例的命名必须以test开头，否则不予执行

    # @unittest.skip('')
    @unittest.skip
    def test_skip(self):
        pass

    def test_instruct(self):
        self.assertIsNotNone(self._ha)

    def test_getstring(self):
        self.assertIsNotNone(self._ha)
        url = 'https://www.baidu.com'
        html = self._ha.getstring(url, headers='''
        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
        Accept-Encoding: gzip, deflate, br
        Accept-Language: zh-CN,zh;q=0.9
        Cache-Control: no-cache
        Connection: keep-alive
        Host: www.baidu.com
        Pragma: no-cache
        Upgrade-Insecure-Requests: 1
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36'''
                                  )
        self.assertFalse(html is None and html == '')
