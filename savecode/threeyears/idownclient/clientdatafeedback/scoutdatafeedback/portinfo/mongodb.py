"""
An port of mongodb info
"""
import json


class MongoDB:
    def __init__(self):
        self.is_master = None
        self.build_info = None
        self.banner = 'mongodb banner'

    def build_banner(self) -> str:
        """
        build banner string
        """
        bannerdict = {}
        if self.is_master is not None:
            for k, v in self.is_master.items():
                bannerdict[k] = v
        if self.build_info is not None:
            # 然后就可以直接拿build info里面的信息
            for k, v in self.build_info.items():
                bannerdict[k] = v

        banner = json.dumps(bannerdict)

        if not banner is None and banner != "":
            banner = "MongoDB:\n" + banner

        return banner

    def get_outputdict(self) -> dict:
        """return mongodb dict"""
        res: dict = {}
        if self.banner is not None:
            res['banner'] = self.banner
        if self.is_master is not None:
            imlist = []
            for k, v in self.is_master.items():
                imlist.append({'key': k, 'value': v})
            res["is_master"] = imlist
        if self.build_info is not None:
            blist = []
            for k, v in self.build_info.items():
                blist.append({'key': k, 'value': v})
            res["build_info"] = blist
        return res
