"""
出行类APP，网站下载回来的出行记录数据
create by judy 2018/10/18
"""

import json

from commonbaby.helpers import helper_crypto

from datacontract.idowndataset import Task
from datacontract.outputdata import EStandardDataType
from .feedbackbase import FeedDataBase, InnerDataBase


class ITRIP_ONE(InnerDataBase):
    """表示一个出行记录"""

    def __init__(self, task: Task, apptype: int, userid, orderid):
        super(ITRIP_ONE, self).__init__(task, apptype)
        if userid is None:
            raise Exception('User cannot be None')
        if orderid is None:
            raise Exception("Orderid cannot be None.")
        self._userid = userid
        self._orderid = orderid
        self.phone = None
        self.totalcost = None
        self.actualcost = None
        self.carno = None
        self.cartype = None
        self.carcolor = None
        self.drivername = None
        self.drivertel = None
        self.starttime = None
        self.endtime = None
        self.startarea = None
        self.endarea = None
        self.istimeout = None
        self.isrefund = None
        self.costtime = None
        self.distance = None
        self.redpacketamount = None  # 红包金额
        self.usercomment = None  # 用户评价
        self.coordinate = None  # 起点终点等坐标

    def _get_output_fields(self) -> dict:
        """"""
        self.append_to_fields('userid', self._userid)
        self.append_to_fields('orderid', self._orderid)
        self.append_to_fields('phone', self.phone)
        self.append_to_fields('totalcost', self.totalcost)
        self.append_to_fields('actualcost', self.actualcost)
        self.append_to_fields('carno', self.carno)
        self.append_to_fields('cartype', self.cartype)
        self.append_to_fields('carcolor', self.carcolor)
        self.append_to_fields('drivername', self.drivername)
        self.append_to_fields('drivertel', self.drivertel)
        self.append_to_fields('starttime', self.starttime)
        self.append_to_fields('endtime', self.endtime)
        self.append_to_fields('startarea', self.startarea)
        self.append_to_fields('endarea', self.endarea)
        self.append_to_fields('istimeout', self.istimeout)
        self.append_to_fields('isrefund', self.isrefund)
        self.append_to_fields('costtime', self.costtime)
        self.append_to_fields('distance', self.distance)
        self.append_to_fields('redpacketamount', self.redpacketamount)
        self.append_to_fields('usercomment', self.usercomment)
        self.append_to_fields('coordinate', json.dumps(self.coordinate, ensure_ascii=False))
        return self._fields

    # def _get_write_lines(self):
    #     lines = ''
    #     lines += 'userid:{}\r\n'.format(self._userid)
    #     lines += 'orderid:{}\r\n'.format(self._orderid)
    #     if self.phone is not None and self.phone != '':
    #         lines += 'phone:{}\r\n'.format(self.phone)
    #     if self.totalcost is not None and self.totalcost != '':
    #         lines += 'totalcost:{}\r\n'.format(self.totalcost)
    #     if self.actualcost is not None:
    #         lines += 'actualcost:{}\r\n'.format(
    #             helper_str.base64format(self.actualcost))
    #     if self.carno is not None:
    #         lines += 'carno:{}\r\n'.format(helper_str.base64format(self.carno))
    #     if self.cartype is not None:
    #         lines += 'cartype:{}\r\n'.format(
    #             helper_str.base64format(self.cartype))
    #     if self.carcolor is not None:
    #         lines += 'carcolor:{}\r\n'.format(
    #             helper_str.base64format(self.carcolor))
    #     if self.drivername is not None:
    #         lines += 'drivername:{}\r\n'.format(
    #             helper_str.base64format(self.drivername))
    #     if self.drivertel is not None:
    #         lines += 'drivertel:{}\r\n'.format(self.drivertel)
    #     if self.starttime is not None:
    #         lines += 'starttime:{}\r\n'.format(self.starttime)
    #     if self.endtime is not None:
    #         lines += 'endtime:{}\r\n'.format(self.endtime)
    #     if self.startarea is not None:
    #         lines += 'startarea:{}\r\n'.format(
    #             helper_str.base64format(self.startarea))
    #     if self.endarea is not None:
    #         lines += 'endarea:{}\r\n'.format(
    #             helper_str.base64format(self.endarea))
    #     if self.istimeout is not None:
    #         lines += 'istimeout:{}\r\n'.format(self.istimeout)
    #     if self.isrefund is not None:
    #         lines += 'isrefund:{}\r\n'.format(self.isrefund)
    #     if self.costtime is not None:
    #         lines += 'costtime:{}\r\n'.format(
    #             helper_str.base64format(self.costtime))
    #     if self.distance is not None:
    #         lines += 'distance:{}\r\n'.format(
    #             helper_str.base64format(self.distance))
    #     if self.redpacketamount is not None:
    #         lines += 'redpacketamount:{}\r\n'.format(
    #             helper_str.base64format(self.redpacketamount))
    #     if self.usercomment is not None:
    #         lines += 'usercomment:{}\r\n'.format(
    #             helper_str.base64format(self.usercomment))
    #     if isinstance(self.coordinate, list) and len(self.coordinate) > 0:
    #         lines += 'coordinate:{}\r\n'.format(
    #             helper_str.base64format(
    #                 json.dumps(
    #                     self.coordinate).encode().decode('unicode_escape')))
    #     return lines

    def get_display_name(self):
        return self._orderid

    def get_uniqueid(self):
        return helper_crypto.get_md5_from_str("{}{}{}".format(self._apptype, self._userid, self._orderid))


class ITRIP(FeedDataBase):
    """表示一个账号的出行记录"""

    def __init__(self, clientid: str, tsk: Task, apptype: int):
        FeedDataBase.__init__(self, '.itrip_record',
                              EStandardDataType.TripOrder, tsk, apptype,
                              clientid, True)
