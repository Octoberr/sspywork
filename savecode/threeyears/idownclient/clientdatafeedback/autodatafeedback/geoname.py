"""
geoname
create by judy 2019/08/23
"""


class Geoname(object):

    def __init__(self, geonameid, name):
        if geonameid is None:
            raise Exception('Region geonameid cant be None.')
        if name is None:
            raise Exception('Region name cant be None.')
        self.geonameid = geonameid
        self.name = name
        self.asciiname = None
        self.latitude = None
        self.longitude = None
        self.feature_class = None
        self.featurecode = None
        self.population = None
        self.timezone = None
        self.modification = None
        self.continent = None
        self.self_admin_code = {}
        self.parent_admin_code = {}

    def set_parent_admin_code(self, pac: dict):
        """
        如果当前这个地区有父级地区，那么就会给父级地区赋值
        :param pac:
        :return:
        """
        self.parent_admin_code = pac

    def set_self_admin_code(self, sac: dict):
        """
        如果当前这个地区是一级行政区或者二级行政区那么就会有值
        :param sac:
        :return:
        """
        self.self_admin_code = sac
