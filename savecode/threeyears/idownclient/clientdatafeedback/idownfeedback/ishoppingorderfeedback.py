"""
登入购物网站获取订单信息记录
create by judy 2018/10/18
"""

from commonbaby.helpers import helper_crypto

from datacontract.idowndataset import Task
from datacontract.outputdata import EStandardDataType
from .feedbackbase import FeedDataBase, InnerDataBase, OrderData


class ISHOPPING_ONE(InnerDataBase, OrderData):
    """表示一个购物订单"""

    def __init__(self, task: Task, apptype: int, userid, orderid):
        super(ISHOPPING_ONE, self).__init__(task, apptype)
        OrderData.__init__(self)
        if not isinstance(userid, str) or userid == "":
            raise Exception('Userid cant be None')
        if orderid is None:
            raise Exception("Orderid cannot be None")
        self._userid = userid
        self._orderid = orderid
        # 写入这个字段时，必须搞成标准的时间字符串:
        # 2019-01-01 00:00:00
        self.ordertime: str = None
        self.host = None

    def _get_output_fields(self) -> dict:
        """"""
        self.append_to_fields('userid', self._userid)
        self.append_to_fields('orderid', self._orderid)
        self.append_to_fields('ordertime', self.ordertime)
        self.append_to_fields('host', self.host)
        # self.append_to_fields('order', json.dumps(self._order, ensure_ascii=False))
        self.append_to_fields('order', self._format_order())
        return self._fields

    # def _get_write_lines(self):
    #     lines = ''
    #     lines += 'userid:{}\r\n'.format(self._userid)
    #     # if self.orderid is not None:
    #     lines += 'orderid:{}\r\n'.format(self._orderid)
    #     if self.ordertime is not None:
    #         lines += 'ordertime:{}\r\n'.format(self.ordertime)
    #     if self.host is not None:
    #         lines += 'host:{}\r\n'.format(helper_str.base64format(self.host))
    #     if isinstance(self._order, dict) and len(self._order) > 0:
    #         lines += 'order:{}\r\n'.format(
    #             helper_str.base64format(
    #                 json.dumps(self._order).encode().decode('unicode_escape')))
    #     return lines

    def get_display_name(self):
        return self._orderid

    def get_uniqueid(self):
        return helper_crypto.get_md5_from_str("{}{}{}".format(self._apptype, self._userid, self._orderid))


class ISHOPPING(FeedDataBase):
    """表示一个账号的购物订单数据"""

    def __init__(self, clientid: str, tsk: Task, apptype: int):
        FeedDataBase.__init__(self, '.ishopping_order',
                              EStandardDataType.ShoppingOrder, tsk, apptype,
                              clientid, True)
