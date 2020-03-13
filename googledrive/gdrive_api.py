import io
import os.path
import pickle
# import ssl
import traceback
import json
import requests

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = [
    # 'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive'
]

# When running locally, disable OAuthlib's HTTPs verification. When
# running in production *do not* leave this option enabled.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# os.environ['http_proxy'] = 'http://127.0.0.1:1080'
# os.environ['https_proxy'] = 'http://127.0.0.1:1080'
os.environ['http_proxy'] = 'http://127.0.0.1:1081'
os.environ['https_proxy'] = 'http://127.0.0.1:1081'


# os.environ['http_proxy'] = 'http://127.0.0.1:8888'
# os.environ['https_proxy'] = 'http://127.0.0.1:8888'
# os.environ['no_proxy'] = 'localhost,127.0.0.1,192.168.0.0/16'


class GItem:

    @property
    def fullpath(self) -> str:
        fpath = self._name
        if not self.parent is None:
            fpath = self.parent.fullpath.rstrip('/') + '/' + fpath.rstrip('/')
        return fpath

    def __init__(self, id, name, type):
        self._id = id
        self._name = name
        self._type = type

        self.parent: GItem = None

        # 结构： <fullpath, GItem>
        self._childs: dict = {}

    def append_child(self, child):
        if not isinstance(child, GItem):
            raise Exception("Invalid child")
        self._childs[child.fullpath] = child
        child.parent = self


class GDrive:
    def __init__(self):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                print(creds.token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                # creds = flow.run_local_server(port=0)
                creds = flow.run_console()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

    def get_tree(self):
        """
        获取网盘文件树
        :return:
        """
        # 首先要有个root
        root = GItem("root", "/", "folder")
        self.get_tree_recusively(root)
        print(root._childs)

    def get_tree_recusively(self, parent: GItem):
        for gi in self.get_child_items_api(parent._id):
            parent.append_child(gi)
            if gi._type == "application/vnd.google-apps.folder":
                self.get_tree_recusively(gi)

    def get_child_items_api(self, fileid: str) -> iter:
        """"""
        # results = self.service.files().list(
        #     q=f"'{fileid}' in parents",
        #     pageSize=100,
        #     fields="nextPageToken, files(id, name, mimeType, parents)").execute()
        nextpage = True
        url = f'https://www.googleapis.com/drive/v3/files?q=%27{fileid}%27+in+parents+and+trashed%3Dfalse&fields=nextPageToken%2C+files%28id%2C+name%2C+mimeType%2C+parents%29&alt=json'
        headers = {
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate',
            'user-agent': '(gzip)',
            'x-goog-api-client': 'gdcl/1.7.11 gl-python/3.7.5',
            'content-length': '0',
            'authorization': 'Bearer ya29.a0Adw1xeX5oApGu9zUlPAJ2WxYOv9WzFCO4vCBNeLh5TH87WngkBYEXkWBd328JCimG2asKOYmcxhlruc2wOtDuKEIb_QkU8jzyTvB8mRTD-wd6wgSNs-SPIHmxKSEKEWL05eUchf2s3l5yGF2YPCGO98KeN3eXoraFo22'
        }

        while nextpage:
            response = requests.get(url, headers=headers)
            results = json.loads(response.text)

            items = results.get('files', [])
            nextpagetoken = results.get('nextPageToken')
            if nextpagetoken is not None:
                url = f'https://www.googleapis.com/drive/v3/files?q=%27{fileid}%27+in+parents+and+trashed%3Dfalse&pageToken={nextpagetoken}&fields=nextPageToken%2C+files%28id%2C+name%2C+mimeType%2C+parents%29&alt=json'
            else:
                nextpage = False
            for i in items:
                gi = GItem(i["id"], i["name"], i["mimeType"])
                yield gi

    def files_list(self):
        """获取所有文件"""
        # Call the Drive v3 API
        # 1、获取root文件夹下的所有文件
        treefile = []
        files = self.get_folder_files('root')
        while len(files) > 0:
            tmp = []
            for el in files:
                mtype = el.get('mimeType')
                if mtype == 'application/vnd.google-apps.folder':
                    tmp.append(el.get('id'))

    def get_folder_files(self, fileid):
        """
        获取一个指定文件夹下的所有文件
        :return:
        """
        results = self.service.files().list(
            q=f"'{fileid}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, parents)").execute()
        nextpagetoken = results.get('nextPageToken')
        items = results.get('files', [])
        if nextpagetoken is not None:
            while nextpagetoken is not None:
                results = self.service.files().list(
                    q=f"'{fileid}' in parents and trashed=false",
                    pageToken=nextpagetoken,
                    fields="nextPageToken, files(id, name, mimeType, parents)").execute()
                nextpagetoken = results.get('nextPageToken')
        print(items)
        return items

    def upload_file(self):
        """
        上传文件，大文件和小文件都没问题
        :return:
        """
        headers = {
            "Authorization": "Bearer ya29.Il-_B253Ji9Q4gVfaZ4jm7sgnXgZp6KWMtmrtsjoQSgsOdjKVG-8-hLM9unSzh7NSK9b0JRR9_0uln5YWxN8GubVE7qvg-YAYoB4NSxONR7j5dQU6xKgLisg0-8fjqOLaA"
        }
        para = {
            "name": "anconda.exe",
            "parents": ["1v6tk9DiamzzzsW_V8BMv9o8m5ejWMpP5"]
        }
        files = {
            'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'),
            'file': open(r"D:\迅雷下载\Anaconda3-2019.10-Windows-x86_64.exe", "rb")
        }
        r = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers=headers,
            files=files
        )
        print(r.text)
        # file_metadata = {'name': 'photo.jpg'}
        # media = MediaFileUpload('files/photo.jpg',
        #                         mimetype='image/jpeg')
        # file = self.service.files().create(body=file_metadata,
        #                                     media_body=media,
        #                                     fields='id').execute()
        # print('File ID: %s' % file.get('id'))

    def download_file(self, fileid):
        """
        下载文件
        1、二进制文件下载
        2、文档型文件下载
        :return:
        """
        # 下载二进制或者媒体文件
        # url = f'https://www.googleapis.com/drive/v3/files/{fileid}?alt=media'
        # headers = {
        #     'x-goog-api-client': 'gdcl/1.7.11 gl-python/3.7.5',
        #     'range': 'bytes=0-104857600',
        #     'authorization': 'Bearer ya29.ImC_BzgCWKw8ujkTHOda0wSBo5mZEUe-8y-RmNHirlnBz-LUI5R1JrAjRmbEEtYbHKbQh8wbRZBk4u9BuH6vcRCBTa0Ps9sjfArb-b0Nd0f387UDqj4yj2Yo3pKMCGUuSKM'
        # }
        # response = requests.get(url, headers=headers)

        # 下载文档型文件，文档类型https://developers.google.com/drive/api/v3/ref-export-formats
        url = f'https://www.googleapis.com/drive/v3/files/{fileid}/export?mimeType=application%2Fpdf&alt=media'
        headers = {
            'x-goog-api-client': 'gdcl/1.7.11 gl-python/3.7.5',
            'range': 'bytes=0-104857600',
            'authorization': 'Bearer ya29.ImC_BzgCWKw8ujkTHOda0wSBo5mZEUe-8y-RmNHirlnBz-LUI5R1JrAjRmbEEtYbHKbQh8wbRZBk4u9BuH6vcRCBTa0Ps9sjfArb-b0Nd0f387UDqj4yj2Yo3pKMCGUuSKM'
        }
        response = requests.get(url, headers=headers)
        # file_id = '1VXAQ4HkJ2oqRhT59twYERWTzs6m8d7b8'
        # file_id = '1eTzqAhcPo-R17IuAumhosKZP-JRs9xgp6Y99MjtwsKc'
        # request = self.service.files().export_media(fileId=file_id,
        #                                      mimeType='application/pdf')
        # fh = io.BytesIO()
        # downloader = MediaIoBaseDownload(fh, request)
        # done = False
        # while done is False:
        #     status, done = downloader.next_chunk()
        #     print("Download %d%%." % int(status.progress() * 100))

    def mkdir(self):
        """
        创建文件夹
        :return:
        """
        url = 'https://www.googleapis.com/drive/v3/files?fields=id%2C+name%2C+mimeType&alt=json'

        # file_metadata = {
        #     'name': 'october2',
        #     'mimeType': 'application/vnd.google-apps.folder',
        #     'parents': ['1v6tk9DiamzzzsW_V8BMv9o8m5ejWMpP5']
        # }
        # file_metadata = {
        #     'name': 'october3',
        #     'mimeType': 'application/vnd.google-apps.folder'
        # }
        body = '{"name": "october3", "mimeType": "application/vnd.google-apps.folder"}'
        headers = {
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate',
            'user-agent': '(gzip)',
            'x-goog-api-client': 'gdcl/1.7.11 gl-python/3.7.5',
            'content-type': 'application/json',
            'content-length': '70',
            'authorization': 'Bearer ya29.ImC_BzgCWKw8ujkTHOda0wSBo5mZEUe-8y-RmNHirlnBz-LUI5R1JrAjRmbEEtYbHKbQh8wbRZBk4u9BuH6vcRCBTa0Ps9sjfArb-b0Nd0f387UDqj4yj2Yo3pKMCGUuSKM'
        }
        r = requests.post(
            url,
            headers=headers,
            data=body
        )

        print(json.loads(r.text))
        # file_metadata = {
        #     'name': 'october2',
        #     'mimeType': 'application/vnd.google-apps.folder'
        # }
        # file_metadata = {
        #     'name': 'october2',
        #     'mimeType': 'application/vnd.google-apps.folder',
        #     'parents': ['1v6tk9DiamzzzsW_V8BMv9o8m5ejWMpP5']
        # }
        # file = self.service.files().create(body=file_metadata,
        #                                    fields='id, name, mimeType').execute()
        # print(file)

    def delete(self, fileid):
        """
        删除1LxjDNEIiQkIWtJOqziqKJtoq6TDdMCUb
        :return:
        """
        # file = self.service.files().delete(fileId='1LxjDNEIiQkIWtJOqziqKJtoq6TDdMCUb').execute()

        # print(file)
        # 删除文件
        url = f'https://www.googleapis.com/drive/v3/files/{fileid}?'
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate',
            'user-agent': '(gzip)',
            'x-goog-api-client': 'gdcl/1.7.11 gl-python/3.7.5',
            'content-length': '0',
            'authorization': 'Bearer ya29.a0Adw1xeXEVdSLBz5I5QqCPtkL-WPoiH1X7ky0tA8M3USAHSF0CxtRxOtIyxmRwvbTpnBfUdvSS86o24Y64qatYteiCWiK-3wC49HucWJCyiLS6D-vtd1y_vK3CO2-o_7OsJK-liGsdSO1tKBfvtZIG7TJE-yIUy2IXYXn'
        }
        res = requests.delete(url, headers=headers)

        # 清空回收站

    def emptytrash(self):
        """
        清空垃圾箱
        :return:
        """
        url = 'https://www.googleapis.com/drive/v2/files/trash'
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate',
            'user-agent': '(gzip)',
            'x-goog-api-client': 'gdcl/1.7.11 gl-python/3.7.5',
            'content-length': '0',
            'authorization': 'Bearer ya29.a0Adw1xeXEVdSLBz5I5QqCPtkL-WPoiH1X7ky0tA8M3USAHSF0CxtRxOtIyxmRwvbTpnBfUdvSS86o24Y64qatYteiCWiK-3wC49HucWJCyiLS6D-vtd1y_vK3CO2-o_7OsJK-liGsdSO1tKBfvtZIG7TJE-yIUy2IXYXn'
        }
        res = requests.delete(url, headers=headers)
        print(res.text)


if __name__ == '__main__':
    try:
        gd = GDrive()

        gd.get_tree()
        # gd.get_folder_files('16nk8rqIF6AY0seMAwT1hnFiufomNMNC8')
        # gd.upload_file()
        # gd.download_file(123)
        # gd.get_file_list()
        # gd.mkdir()
        # gd.delete()
        # gd.emptytrash()
        print("OK")
    except Exception:
        traceback.print_exc()
