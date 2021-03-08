"""Facebook Messenger"""

# -*- coding:utf-8 -*-

from datacontract.idowndataset import Task

from ....clientdatafeedback import CONTACT_ONE, ICHATGROUP_ONE
from .messengercheckregister import MessengerCheckRegister

# inherit route:
# SpiderMessenger:MessengerCheckRegister:
# MessengerChatlog:MessengerGroup:MessengerContact:
# MessengerProfile:MessengerLogout:MessengerLogin
# :MessengerBase


class SpiderMessenger(MessengerCheckRegister):
    """Download Messenger"""

    def __init__(self, task: Task, appcfg, clientid):
        MessengerCheckRegister.__init__(self, task, appcfg, clientid)

    def _sms_login(self) -> bool:
        return self._sms_login_()

    def _cookie_login(self) -> bool:
        return self._cookie_login_()

    def _check_registration(self) -> iter:
        return self._check_registration_()

    def _get_profile(self) -> iter:
        return self._get_profile_()

    def _get_contacts(self) -> iter:
        return self._get_contacts_()

    def _get_contact_chatlogs(self, ct: CONTACT_ONE) -> iter:
        return self._get_contact_chatlogs_(ct)

    def _get_groups(self) -> iter:
        return self._get_groups_()

    def _get_group_chatlogs(self, grp: ICHATGROUP_ONE) -> iter:
        return self._get_group_chatlogs_(grp)
