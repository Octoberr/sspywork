import logging
import copy

import connect


logger = logging.getLogger('importer')


class DriveObj():

    def __init__(self, drive_obj):
        self.id = drive_obj.get('id')
        self.name = drive_obj.get('name')

    def make_dict(self):
        props = copy.deepcopy(vars(self))
        del props['name']
        return props

    @property
    def parents(self):
        try:
            return service.files().get(fileId=self.id,
                                       fields='parents').execute()['parents']
        except KeyError:
            return []


class Directory(DriveObj):

    def __init__(self, drive_obj):
        super().__init__(drive_obj)
        self.mimeType = 'application/vnd.google-apps.folder'
        assert drive_obj.get('mimeType') == self.mimeType, 'Not dir :('
        self.children = []

    def add_content(self, drive_obj):
        self.children.append(drive_obj)


class Document(DriveObj):

    def __init__(self, drive_obj):
        super().__init__(drive_obj)
        assert 'vnd.google-apps.folder' not in drive_obj.get('mimeType')
        self.mimeType = drive_obj.get('mimeType')


def get_filelist(service):
    return service.files().list().execute()


def get_content(service):
    content = list()
    for drive_obj in get_filelist(service)['files']:
        try:
            content.append(Directory(drive_obj))
        except AssertionError:
            content.append(Document(drive_obj))
    return content


def find_id(content, id):
    for drive_obj in content:
        logger.debug('Got {}'.format(drive_obj.id))
        if drive_obj.id == id:
            logger.debug('Find id in {}'.format(drive_obj.id))
            return drive_obj
        elif type(drive_obj) == Directory and drive_obj.children:
            logger.debug('{} has children'.format(drive_obj.id))
            result = find_id(drive_obj.children, id)
            if result:
                return result


def create_corr_structure(content):
    for obj in content:
        if obj.parents:
            for parent in obj.parents:
                parent_obj = find_id(content, parent)
                if parent_obj:
                    parent_obj.add_content(obj)
                else:
                    logger.debug(
                        'There is no parent directory for {}'.format(obj.name))
    content[:] = [value for value in content if not value.parents]


if __name__ == "__main__":
    structure = dict()
    service = connect.connect_drive()
    content = get_content(service)
    create_corr_structure(content)