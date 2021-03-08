"""represents an ipwhois info"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.countrycodes import ALL_COUNTRIES

from datacontract.iscoutdataset.iscouttask import IscoutTask


class IPWhoisEntityData(object):
    """represents an entity in an ipwhois info"""

    _roles_def: list = [
        "registrant", "technical", "administrative", "abuse", "billing",
        "registrar", "reseller", "sponsor", "proxy", "notifications", "noc"
    ]

    def __init__(self, handle: str):
        if not isinstance(handle, str) or handle == "":
            raise Exception("Invalid handle for IPWhoisEntity")

        self._handle: str = handle

        self._roles: list = []
        self._roles_locker = threading.RLock()

        self.last_modified: str = None
        self.name: str = None
        self.address: str = None
        self.email: str = None
        self.phone: str = None

    def set_role(self, role: str):
        if not isinstance(role, str) or not role in self._roles_def:
            return
        if role in self._roles:
            return
        with self._roles_locker:
            if role in self._roles:
                return
            self._roles.append(role)

    def get_outputdict(self) -> dict:
        """return entity dict"""
        res: dict = {}
        res['handle'] = self._handle
        res['roles'] = self._roles
        if not self.last_modified is None:
            res['last_modified'] = self.last_modified
        if not self.address is None and self.address != "":
            res['address'] = self.address
        if not self.email is None and self.email != "":
            res['email'] = self.email
        if not self.phone is None and self.phone != "":
            res['phone'] = self.phone
        return res


class IPWhoisData(object):
    """represents a whois info\n
    ip_ver: v4/v6"""
    def __init__(
            self,
            reason: str,
            md5: str,
            raw: str,
            handle: str,
            allocate_type: str,
            netname: str,
            country_code: str,
            ip_ver: str = 'v4',
    ):
        if not isinstance(reason, str) or reason == "":
            raise Exception('Invalid param "reason" for IPWhois')
        if not isinstance(md5, str) or md5 == "":
            raise Exception('Invalid param "md5" for IPWhois')
        if not isinstance(raw, str) or raw == "":
            raise Exception('Invalid param "raw" for IPWhois')
        if not isinstance(handle, str) or handle == "":
            raise Exception('Invalid param "handle" for IPWhois')
        if not isinstance(ip_ver, str) or ip_ver == "":
            raise Exception('Invalid param "ip_ver" for IPWhois')
        if not isinstance(allocate_type, str) or allocate_type == "":
            # raise Exception('Invalid param "allocate_type" for IPWhois')
            allocate_type = "ALLOCATED PORTABLE"
        if not isinstance(netname, str) or netname == "":
            raise Exception('Invalid param "netname" for IPWhois')
        if not isinstance(country_code,
                          str) or not ALL_COUNTRIES.__contains__(country_code):
            raise Exception('Invalid param "country_code" for IPWhois')

        self._reason: str = reason
        self._md5: str = md5
        self._raw: str = raw

        self._handle: str = handle
        self._ip_ver: str = ip_ver
        self.applicable_from: str = None
        self.applicable_until: str = None
        self._allocate_type: str = allocate_type
        self._netname: str = netname
        self._country_code: str = country_code
        self.last_modified: str = None

        self.remarks: str = None

        self._cidrs: dict = {}
        self._cidrs_locker = threading.RLock()

        self._entities: dict = {}
        self._entities_locker = threading.RLock()

    def set_cidrs(self, cidr: str):
        """set cidr"""
        if not isinstance(cidr, str) or cidr == "":
            return
        if self._cidrs.__contains__(cidr):
            return
        with self._cidrs_locker:
            if self._cidrs.__contains__(cidr):
                return
            self._cidrs[cidr] = cidr

    def set_entity(self, entity: IPWhoisEntityData):
        """set entity"""
        if not isinstance(entity, IPWhoisEntityData):
            return
        # 在一个whois信息的多个entities里，每条entity的handle是唯一的
        # 后面在界面看能不能检查出问题
        if self._entities.__contains__(entity._handle):
            return
        with self._entities_locker:
            if self._entities.__contains__(entity._handle):
                return
            self._entities[entity._handle] = entity

    def get_outputdict(self) -> dict:
        """get ipwhois dict"""
        res: dict = {}
        res['reason'] = self._reason
        res['md5'] = self._md5
        res['raw'] = self._raw
        res['handle'] = self._handle
        res['ip_version'] = self._ip_ver
        if not self.applicable_from is None:
            res['applicable_from'] = self.applicable_from
        if not self.applicable_until is None:
            res['applicable_until'] = self.applicable_until
        res['allocate_type'] = self._allocate_type
        res['netname'] = self._netname
        if isinstance(self.remarks, str) and self.remarks != '':
            res['remarks'] = self.remarks
        res['country_code'] = self._country_code
        if not self.last_modified is None:
            res['last_modified'] = self.last_modified
        if len(self._cidrs) > 0:
            res['cidrs'] = []
            for c in self._cidrs.values():
                res['cidrs'].append(c)
        if len(self._entities) > 0:
            res['entities'] = []
            for e in self._entities.values():
                res['entities'].append(e.get_outputdict())
        return res