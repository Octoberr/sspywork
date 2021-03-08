"""client data definations"""

# -*- coding:utf-8 -*-

from .idownfeedback.contactfeedback import CONTACT, CONTACT_ONE, EGender
from .idownfeedback.emlfeedback import EML, Folder
from .idownfeedback.feedbackbase import (DetailedData, EGender, FeedDataBase, InnerDataBase,
                           OrderData, UniqueData, Resource, EResourceType,
                           ESign, ResourceData)
from .idownfeedback.ichatgroup import ICHATGROUP, ICHATGROUP_ONE
from .idownfeedback.ichatlog import ICHATLOG, ICHATLOG_ONE
from .idownfeedback.idownloginlog import IdownLoginLog, IdownLoginLog_ONE
from .idownfeedback.inetdiskfilefeedback import INETDISKFILE
from .idownfeedback.inetdisklistfeedback import INETDISKFILELIST
from .idownfeedback.ishoppingorderfeedback import ISHOPPING, ISHOPPING_ONE
from .idownfeedback.itravelorderfeedback import ITRAVELORDER, ITRAVELORDER_ONE
from .idownfeedback.itripfeedback import ITRIP, ITRIP_ONE
from .idownfeedback.profilefeedback import PROFILE
from .idownfeedback.resourcefeedback import RESOURCES
from .idownfeedback.userstatusfeedback import UserStatus
from .idownfeedback.clientlogfeedback import ClientLog
