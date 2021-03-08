"""
带文件体的数据
"""


class ExpStreamData(object):

    def __init__(self, datasource, id, name, url, stream):
        self.datasource = datasource
        self.id = id
        self.name = name
        self.url = url
        self.stream = stream

    def get_outputlines(self):
        """
        获取需要输出的字段，子类根据需要重写
        :return:
        """
        lines = ''
        lines += f'datasource:{self.datasource}\n'
        lines += f'id:{self.id}\n'
        lines += f'name:{self.name}\n'
        lines += f'url:{self.url}\n'
        return lines


class ExpDBexp(ExpStreamData):

    def __init__(self, datasource, id, name, url, stream):
        ExpStreamData.__init__(self, datasource, id, name, url, stream)


class ExpDBapp(ExpStreamData):

    def __init__(self, datasource, id, name, url, stream):
        ExpStreamData.__init__(self, datasource, id, name, url, stream)


class ExpDBscreenshot(ExpStreamData):

    def __init__(self, datasource, id, name, url, stream):
        ExpStreamData.__init__(self, datasource, id, name, url, stream)
        # 1：缩略图，2：原图
        self.type = None

    def get_outputlines(self):
        """
        获取需要输出的字段，子类根据需要重写
        :return:
        """
        lines = ''
        lines += f'datasource:{self.datasource}\n'
        lines += f'id:{self.id}\n'
        lines += f'name:{self.name}\n'
        lines += f'url:{self.url}\n'
        lines += f'type:{self.type}\n'
        return lines


class ExpDBdoc(ExpStreamData):

    def __init__(self, datasource, id, name, url=None, stream=None):
        ExpStreamData.__init__(self, datasource, id, name, url, stream)

    def get_outputlines(self):
        """
        子类重写输出
        """
        lines = ''
        lines += f'datasource:{self.datasource}\n'
        lines += f'id:{self.id}\n'
        lines += f'name:{self.name}\n'
        return lines
