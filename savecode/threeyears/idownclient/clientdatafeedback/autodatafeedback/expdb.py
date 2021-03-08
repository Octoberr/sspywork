"""
expdb的数据回馈
create by judy 2019/08/14
"""


class Target(object):

    def __init__(self):
        self.type = None
        self.platform = None
        self.program = None
        self.version = {}
        self.exptoolids = []


class Code(object):
    def __init__(self, code_type, code):
        self.code_type = code_type
        self.code = code


class ExpDB(object):

    def __init__(self, name, datasource, id, date_published, verified):
        if name is None:
            raise Exception('ExpDB name cannot be None.')
        if datasource is None:
            raise Exception('ExpDB datasource cannot be None.')
        if id is None:
            raise Exception('ExpDB id cannot be None.')
        if date_published is None:
            raise Exception('ExpDB data_published cannot be None.')
        if verified is None:
            raise Exception('ExpDB verified cannot be None.')
        # 必要字段
        self.name = name
        self.datasource = datasource
        self.id = id
        self.date_published = date_published
        self.verified = verified

        # 详情字段,3:高， 2：中， 1：低
        self.level = None
        self.description = []
        self.alias = []
        self.tags = []
        self.target = []
        self.author = {}
        self.code = []
        self.app = []
        self.exploit = []
        self.screenshot = []
        self.doc = []

    def set_tasget(self, target: Target):
        """
        添加target
        :param target:
        :return:
        """
        if target is not None:
            self.target.append(target.__dict__)

    def set_code(self, code: Code):
        """
        添加code
        :param code:
        :return:
        """
        if code is not None:
            self.code.append(code.__dict__)

    def get_outputdict(self):
        """
        获取需要输出的dict
        :return:
        """
        return self.__dict__
