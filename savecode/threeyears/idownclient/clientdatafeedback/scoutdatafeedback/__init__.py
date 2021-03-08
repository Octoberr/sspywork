"""Scout dataset"""

# -*- coding:utf-8 -*-

from datacontract.iscoutdataset import EObjectType

from .component import Component
from .domain import Domain
from .email import Email
from .geoinfo import GeoInfo
from .ip import IP
from .ipwhois_data import IPWhoisData, IPWhoisEntityData
from .mailserver import MailServer
from .networkid import NetworkId
from .networkiddata import (
    EResourceType,
    NetworkGroup,
    NetworkMsg,
    NetworkMsgs,
    NetworkPost,
    NetworkPosts,
    NetworkProfile,
    NetworkProfiles,
    NetworkResource,
)
from .phone import Phone
from .portinfo import (
    Certificate,
    CertIssuer,
    CertSubject,
    PortInfo,
    SiteInfo,
    SslCert,
    SshInfo,
    SMTP,
    MySql,
    MongoDB,
    Redis,
    FTP,
    Imap,
    Mssql,
    Ntp,
    POP3,
    Telnet,
    Ubiquiti,
    WeblogicT3
)
from .rangechost import RangeCHost
from .scoutfeedbackbase import ScoutFeedBackBase
from .scoutjsonable import ScoutJsonable
from .screenshotse import ScreenshotSE
from .screenshoturl import ScreenshotUrl
from .searchengine import SearchEngine
from .searchfile import SearchFile
from .sidesite import SideSite
from .url import URL
from .whois import Whois
from .whoisr import Whoisr

ALL_SCOUT_ROOT_OBJ_TYPES = {
    EObjectType.Domain: Domain,
    EObjectType.Ip: IP,
    EObjectType.Url: URL,
    EObjectType.EMail: Email,
    EObjectType.PhoneNum: Phone,
    EObjectType.NetworkId: NetworkId,
}
