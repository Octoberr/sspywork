"""HttpErrorProcessor"""

# -*- coding:utf-8 -*-

from urllib import request


class MyHttpErrorProcessor(request.HTTPErrorProcessor):
    """replace the old one"""

    def __init__(self, allow_redirect: bool = True, *args, **kwargs):
        super(MyHttpErrorProcessor, self).__init__(*args, **kwargs)
        self._allow_redirect = True
        if isinstance(allow_redirect, bool):
            self._allow_redirect = allow_redirect

    def http_response(self, request, response):
        return self._deal_response(request, response)

    def https_response(self, request, response):
        return self._deal_response(request, response)

    def _deal_response(self, request, response):
        if 300 <= response.status < 400:
            if not self._allow_redirect:
                return response
            else:
                return super(MyHttpErrorProcessor, self).https_response(
                    request, response)
        else:
            return super(MyHttpErrorProcessor, self).https_response(
                request, response)


# class MyHttpErrorHandler(request.HTTPDefaultErrorHandler):

#     def __init__(self):
#         pass

#     def test(self):
#         self.
