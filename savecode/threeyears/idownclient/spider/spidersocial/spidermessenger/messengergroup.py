"""messenger group download"""

# -*- coding:utf-8 -*-

import traceback

from commonbaby.helpers import helper_str
from commonbaby.httpaccess import ResponseIO

from datacontract.idowndataset import Task
from .messengercontact import MessengerContact
from ....clientdatafeedback import (CONTACT_ONE, ICHATGROUP_ONE, RESOURCES,
                                    EResourceType, ESign)


class MessengerGroup(MessengerContact):
    """"""

    def __init__(self, task: Task, appcfg, clientid):
        MessengerContact.__init__(self, task, appcfg, clientid)

    def _get_groups_(self) -> iter:
        """fetch groups"""
        try:
            # js_res在获取联系人时已经处理完毕并保存了的
            if not self.js_res:
                self._logger.error(f'Get groups error: js_res is empty')
                return

            for data in self._parse_group_js_res():
                yield data

        except Exception:
            self._logger.error(
                "Fetch groups error:%s" % traceback.format_exc())

    def _get_group_contacts(self, grp: ICHATGROUP_ONE) -> iter:
        """获取群组成员，作为 CONTACT_ONE 返回"""
        try:
            if grp.participants_empty:
                self._logger.info(
                    "Group member is empty: groupid={}, groupname={}, user={}".
                        format(grp._groupid, grp.groupname, self.uname_str))
                return

            for pid in grp.participants:
                try:
                    pid: str = pid
                    if not isinstance(pid, str) or pid == "":
                        continue
                    # 自己就不返回了
                    if pid != self._userid:
                        gct: CONTACT_ONE = CONTACT_ONE(
                            self._userid, pid, self.task, self._appcfg._apptype)
                        if pid not in self.messenger_thread_id:
                            gct.isfriend = 0
                            gct.bothfriend = 0
                            gct.isdeleted = 0

                        yield gct
                except Exception:
                    self._logger.error(
                        "Generate one group participant error:\ngroupid:{}\ngroupname:{}\nparticipantid:{}\nerror:{}"
                            .format(grp._groupid, grp.groupname, pid,
                                    traceback.format_exc()))

        except Exception:
            self._logger.error(
                "Get group members error:\ntaskid:{}\ngroupname:{}\ngroupid:{}\nerror:{}"
                    .format(grp._task.taskid, grp.groupname, grp._groupid,
                            traceback.format_exc()))

    def _parse_group_js_res(self):
        try:
            for dict_one in self.js_res:
                # 返回群聊
                if dict_one['type'] == 'threads' and dict_one['is_group'] == 1:
                    grp: ICHATGROUP_ONE = ICHATGROUP_ONE(
                        self.task, self._appcfg._apptype, self._userid, dict_one['thread_id'])
                    # 头像
                    if dict_one['pic_url'] != 'undefined':
                        uri = dict_one['pic_url']
                        try:
                            respstm: ResponseIO = self._ha.get_response_stream(uri)
                            if not respstm is None:
                                rsc: RESOURCES = RESOURCES(
                                    self._clientid, self.task, uri,
                                    EResourceType.Picture, self._appcfg._apptype)
                                rsc.io_stream = respstm
                                rsc.sign = ESign.PicUrl
                                grp.append_resource(rsc)
                                yield rsc
                        except:
                            self._logger.debug(f'get group avatar failed: {uri}')
                    # 名字
                    if dict_one['group_name'] != 'undefined':
                        grp.groupname = dict_one['group_name']

                    # 群成员
                    for temp_one in self.js_res:
                        if temp_one['type'] == 'participants' and temp_one['thread_id'] == dict_one['thread_id']:
                            pid = temp_one['member_id']
                            grp.append_participants(pid)

                    yield grp
        except:
            self._logger.error("Parse group js_res error: {}".format(
                traceback.format_exc()))
