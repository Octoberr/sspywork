"""
google drive 上传文件功能
"""
import json
import time

import requests


class GoogleDrive(object):

    def __init__(self):
        self.cookies = """COMPASS=drivev2=ELmszvIFGrIBAAlriVeMMFH7Rg1b7nKyc7krgKAC1xrpvgt_Y4yEw1h6KeP_sSrrFkpfEzPdOXXNFbXjSFCDI2_Mcea0jeyOLAazW2qWPSs5n9p7pZenCHDLlRUDQPxQG4pQax7Ze-z3xmEoSmAdAR00BkYEXN8RoF8-2ZgO2hGGBCLVR16ndRIPXCBQHSR-LYpIrRyMBUy6iegVzXeaC1Hc9JcejlOQTgmlHS6PV16sY-AfS9YIXPPZUQ; OGPC=19016257-1:; OGP=-19016257:; SID=uAfe47HgWETPeeS0WdN1-NAHQmq0BgoqAGfv6arPRI8Jei2NYOx4mC6Mq0rLmnq_6caV4w.; __Secure-3PSID=uAfe47HgWETPeeS0WdN1-NAHQmq0BgoqAGfv6arPRI8Jei2NmSBwQ6gLfVUgN3oXnhJetg.; HSID=AcfKvaSo1bSZW_JzG; SSID=Au6NTDoifHOix0BnI; APISID=_7vhhwFoh6o4ADIU/AEkC2vHGekuTSk6Md; SAPISID=OGOY1F-4zOe4QypZ/AEAQi_TmBsON0XC1w; __Secure-HSID=AcfKvaSo1bSZW_JzG; __Secure-SSID=Au6NTDoifHOix0BnI; __Secure-APISID=_7vhhwFoh6o4ADIU/AEkC2vHGekuTSk6Md; __Secure-3PAPISID=OGOY1F-4zOe4QypZ/AEAQi_TmBsON0XC1w; CONSENT=YES+IT.zh-CN+20170702-09-0; SEARCH_SAMESITE=CgQIjI8B; NID=198=Yfay0JV5ht04nOD7JVD9Pi3vRMZLpJGbzzCwSqbKqJqylPZ0-Sx64hnMWEiGXp0XUs27tPTleb73-DkdeBesbn0X5r_mjwFKkqPAycyBo0LHAGFVih8-9CXsdTouO5y-e3e1xT34wx0yyDPjwe0Y-JvRetU6oktDDsPjZhB3kik9-EU4Ln6T_o29XKliOpIfsu5_85ZPCCbkXXRYr0cR0rlvSOsWLtgTqxFZ; 1P_JAR=2020-2-24-9; SIDCC=AN0-TYv7RN_46s-FEOCoZnth87gF81NmrVbOG6oMJwnhGxLdhp1xgYEy9pg8Agx8Ua5p_sXqaQ"""
        self.key = """AIzaSyAy9VVXHSpS2IJpptzYtGbLP3-3_l0aBk4"""
        self.authorization = """SAPISIDHASH 1582531738_32249901ccfe01b843ed85d476f2eec4ab4f6792_u"""
        self.sa = requests.session()
        self.inicookie()

    def inicookie(self):
        """
        判断下cookie是否有效，同时初始化requests里面的Session
        :return:
        """
        url = 'https://drive.google.com/drive/my-drive'

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'cookie': self.cookies,
            'pragma': 'no-cache',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36'
        }

        response = self.sa.get(url, headers=headers)
        if "我的云端硬盘" in response.text:
            print("cookie登陆成功")
        time.sleep(5)

    def gmkdir(self):
        """
        创建文件夹
        :return:
        """
        # 进行文件夹创建工作，url中的key需要登陆去拿到
        url = """https://clients6.google.com/drive/v2internal/files?openDrive=false&reason=204&syncType=0&errorRecovery=false&fields=kind%2CmodifiedDate%2ChasVisitorPermissions%2CcontainsUnsubscribedChildren%2CmodifiedByMeDate%2ClastViewedByMeDate%2CfileSize%2Cowners(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cdomain%2Cid)%2ClastModifyingUser(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cid)%2CancestorHasAugmentedPermissions%2ChasThumbnail%2CthumbnailVersion%2Ctitle%2Cid%2Cshared%2CsharedWithMeDate%2CuserPermission(role)%2CexplicitlyTrashed%2CmimeType%2CquotaBytesUsed%2Ccopyable%2Csubscribed%2CfolderColor%2ChasChildFolders%2CfileExtension%2CprimarySyncParentId%2CsharingUser(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cid)%2CflaggedForAbuse%2CfolderFeatures%2Cspaces%2CsourceAppId%2Crecency%2CrecencyReason%2Cversion%2CactionItems%2CteamDriveId%2ChasAugmentedPermissions%2CcreatedDate%2CprimaryDomainName%2CorganizationDisplayName%2CpassivelySubscribed%2CtrashingUser(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cid)%2CtrashedDate%2Cparents(id)%2Ccapabilities(canMoveItemIntoTeamDrive%2CcanUntrash%2CcanMoveItemWithinTeamDrive%2CcanMoveItemOutOfTeamDrive%2CcanTrashChildren%2CcanAddMyDriveParent%2CcanRemoveMyDriveParent%2CcanShareChildFiles%2CcanShareChildFolders%2CcanRead%2CcanCopy%2CcanDownload%2CcanEdit%2CcanAddChildren%2CcanDelete%2CcanRemoveChildren%2CcanShare%2CcanTrash%2CcanRename%2CcanReadTeamDrive%2CcanMoveTeamDriveItem)%2CcontentRestrictions(readOnly)%2CshortcutDetails(targetId%2CtargetMimeType%2CtargetLookupStatus%2CtargetFile%2CcanRequestAccessToTarget)%2Clabels(starred%2Ctrashed%2Crestricted%2Cviewed)&supportsTeamDrives=true&key=AIzaSyAy9VVXHSpS2IJpptzYtGbLP3-3_l0aBk4"""
        paload = '{"title":"october2","mimeType":"application/vnd.google-apps.folder","parents":[{"id":"0AIj1GZky9BXBUk9PVA"}]}'
        # title,表示要创建文件夹的名字，参数里面的id是要把文件夹建在哪里的父id，这个账号网盘的根id就是0AIj1GZky9BXBUk9PVA
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'authorization': 'SAPISIDHASH 1582533767_066e1ced0a9b0b16671c05504b06ecc62d45be41_u',
            'cache-control': 'no-cache',
            'content-length': '109',
            'Content-Type': 'application/json',
            'cookie': self.cookies,
            'origin': 'https://drive.google.com',
            'pragma': 'no-cache',
            'referer': 'https://drive.google.com/drive/my-drive',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36',
            'x-goog-authuser': '0'
        }
        gresponse = self.sa.post(url, headers=headers, data=paload)
        restext = gresponse.text
        print(restext)
        # 创建成功后从返回的数据中可以取到创建好的文件夹的id
        res = """
        {
 "kind": "drive#file",
 "id": "1U3eyr6P0em_WJjmTsCwexf4qTno1JU_h",
 "thumbnailVersion": "0",
 "title": "october2",
 "mimeType": "application/vnd.google-apps.folder",
 "hasChildFolders": true,
 "labels": {
  "starred": false,
  "trashed": false,
  "restricted": false,
  "viewed": true
 },
 "createdDate": "2020-02-24T08:57:11.655Z",
 "modifiedDate": "2020-02-24T08:57:11.655Z",
 "modifiedByMeDate": "2020-02-24T08:57:11.655Z",
 "lastViewedByMeDate": "2020-02-24T08:57:11.655Z",
 "recency": "2020-02-24T08:57:11.860Z",
 "recencyReason": "createdByMe",
 "version": "1",
 "parents": [
  {
   "id": "0AIj1GZky9BXBUk9PVA"
  }
 ],
 "userPermission": {
  "role": "owner"
 },
 "quotaBytesUsed": "0",
 "owners": [
  {
   "kind": "drive#user",
   "displayName": "sb nm",
   "id": "113532497580613589902",
   "permissionId": "13393928096485412760",
   "emailAddress": "nmsbgg@gmail.com"
  }
 ],
 "lastModifyingUser": {
  "kind": "drive#user",
  "displayName": "sb nm",
  "id": "113532497580613589902",
  "permissionId": "13393928096485412760",
  "emailAddress": "nmsbgg@gmail.com"
 },
 "capabilities": {
  "canAddChildren": true,
  "canAddMyDriveParent": false,
  "canCopy": false,
  "canDelete": true,
  "canDownload": true,
  "canEdit": true,
  "canMoveItemIntoTeamDrive": true,
  "canRead": true,
  "canRemoveChildren": true,
  "canRemoveMyDriveParent": true,
  "canRename": true,
  "canShare": true,
  "canShareChildFiles": false,
  "canShareChildFolders": false,
  "canTrash": true,
  "canUntrash": true
 },
 "copyable": false,
 "shared": false,
 "explicitlyTrashed": false,
 "primarySyncParentId": "0AIj1GZky9BXBUk9PVA",
 "folderColor": "0",
 "subscribed": true,
 "passivelySubscribed": false,
 "flaggedForAbuse": false,
 "sourceAppId": "691301496089",
 "spaces": [
  "drive",
  "DRIVE"
 ],
 "hasThumbnail": false,
 "containsUnsubscribedChildren": false
}
        """

    def g_upload_file(self):
        """
        上传文件
        :return:
        """
        # key需要登陆拿到
        getidurl = 'https://clients6.google.com/drive/v2internal/files/generateIds?openDrive=false&reason=304&syncType=0&errorRecovery=false&space=drive&maxResults=1000&key=AIzaSyAy9VVXHSpS2IJpptzYtGbLP3-3_l0aBk4'
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'authorization': 'SAPISIDHASH 1582531738_32249901ccfe01b843ed85d476f2eec4ab4f6792_u',
            'cache-control': 'no-cache',
            'cookie': self.cookies,
            'origin': 'https://drive.google.com',
            'pragma': 'no-cache',
            'referer': 'https://drive.google.com/drive/my-drive',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36',
            'x-goog-authuser': '0'
        }
        # authorization也需要登陆拿到
        idresponse = self.sa.get(getidurl, headers=headers)
        restext = idresponse.text
        ids = json.loads(restext)['ids']
        aid = ids[0]
        # 拿到的这个id是那边服务器生成的id，必须使用它id库里面的id不然上传文件不会成功
        print(aid)
        # key需要登陆拿到
        url = """https://clients6.google.com/upload/drive/v2internal/files?uploadType=multipart&supportsTeamDrives=true&pinned=true&convert=false&fields=kind%2CmodifiedDate%2ChasVisitorPermissions%2CcontainsUnsubscribedChildren%2CmodifiedByMeDate%2ClastViewedByMeDate%2CfileSize%2Cowners(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cdomain%2Cid)%2ClastModifyingUser(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cid)%2CancestorHasAugmentedPermissions%2ChasThumbnail%2CthumbnailVersion%2Ctitle%2Cid%2Cshared%2CsharedWithMeDate%2CuserPermission(role)%2CexplicitlyTrashed%2CmimeType%2CquotaBytesUsed%2Ccopyable%2Csubscribed%2CfolderColor%2ChasChildFolders%2CfileExtension%2CprimarySyncParentId%2CsharingUser(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cid)%2CflaggedForAbuse%2CfolderFeatures%2Cspaces%2CsourceAppId%2Crecency%2CrecencyReason%2Cversion%2CactionItems%2CteamDriveId%2ChasAugmentedPermissions%2CcreatedDate%2CprimaryDomainName%2CorganizationDisplayName%2CpassivelySubscribed%2CtrashingUser(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cid)%2CtrashedDate%2Cparents(id)%2Ccapabilities(canMoveItemIntoTeamDrive%2CcanUntrash%2CcanMoveItemWithinTeamDrive%2CcanMoveItemOutOfTeamDrive%2CcanTrashChildren%2CcanAddMyDriveParent%2CcanRemoveMyDriveParent%2CcanShareChildFiles%2CcanShareChildFolders%2CcanRead%2CcanCopy%2CcanDownload%2CcanEdit%2CcanAddChildren%2CcanDelete%2CcanRemoveChildren%2CcanShare%2CcanTrash%2CcanRename%2CcanReadTeamDrive%2CcanMoveTeamDriveItem)%2CcontentRestrictions(readOnly)%2CshortcutDetails(targetId%2CtargetMimeType%2CtargetLookupStatus%2CtargetFile%2CcanRequestAccessToTarget)%2Clabels(starred%2Ctrashed%2Crestricted%2Cviewed)&openDrive=false&reason=202&syncType=0&errorRecovery=false&key=AIzaSyAy9VVXHSpS2IJpptzYtGbLP3-3_l0aBk4"""
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'authorization': 'SAPISIDHASH 1582531739_d7d20176c6b9ad48cf302d0d6f45b42438aaa703_u',
            'cache-control': 'no-cache',
            'content-length': '6313',
            'content-type': 'multipart/related; boundary="jtkspbrk5nhd"',
            'cookie': self.cookies,
            'origin': 'https://drive.google.com',
            'pragma': 'no-cache',
            'referer': 'https://drive.google.com/drive/my-drive',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36',
            'x-goog-authuser': '0'
        }
        # authorization也需要登陆拿到
        payload = f"""--jtkspbrk5nhd
content-type: application/json; charset=UTF-8

{{"title":"field.txt","mimeType":"text/plain","parents":[{{"id":"0AIj1GZky9BXBUk9PVA"}}],"id":["{aid}"]}}
--jtkspbrk5nhd
content-transfer-encoding: base64
content-type: text/plain

77u/ZG9ja2VyIOerr+WPo+aYoOWwhCAgIOWuv+S4u+acuu+8muWuueWZqA0KaHR0cDovL2xvY2FsaG9zdDo1MDAwLz9kYXRlPTIwMTctMDYtMTUNCg0KZG9ja2VyIHJ1biAtLXJlc3RhcnQgYWx3YXlzIC1wIDgwMTQ6ODAxNCAtLW5hbWU9J3NjaGVkdWxlXzIwMTcwOTI3X3Byb2QnIHNjaGVkdWxlX3NjaGVkdWxlDQoNCg0KcHl0aG9uIEY6XGdpdGh1YlxDaGluZXNlLUNoYXJhY3Rlci1SZWNvZ25pdGlvblxjaGluZXNlX2NoYXJhY3Rlcl9yZWNvZ25pdGlvbl9ibi5weSAtLW1vZGU9dHJhaW4gLS1tYXhfc3RlcHM9MTYwMDIgLS1ldmFsX3N0ZXBzPTEwMCAtLXNhdmVfc3RlcHM9NTAwDQoNCuS4iuS8oOaWh+S7tu+8mnJ6DQrliJflh7rlgqjlrZjvvJogZG9ja2VyIHZvbHVtZSBscw0K5p+l55yL6K+m57uG5L+h5oGv77yaIGRvY2tlciB2b2x1bWUgaW5zcGVjdA0K5ZCv5Yqo5a655ZmoOiBkb2NrZXItY29tcG9zZSB1cCAtZCDkuI3opoHml6Xlv5cNCgkJCSBkb3duIOWFs+mXrSANCuS4i+i9veaWh+S7tjpzeg0K6L+b5YWlZG9ja2Vy5a655Zmo77yaZG9ja2VyIGV4ZWMgLWl0IGhvcGVmdWxfaHVnbGUgL2Jpbi9iYXNoDQoNCg0Kb3BlbmZhY2UgIGh0dHA6Ly9ibG9nLnRvcHNwZWVkc25haWwuY29tL2FyY2hpdmVzLzEwOTMzDQrmj5Dlj5blkoxhbGlnbmVkDQouL3V0aWwvYWxpZ24tZGxpYi5weSAuL2RhdGFpbWFnZS90cmFpbi8gYWxpZ24gb3V0ZXJFeWVzQW5kTm9zZSAuL2RhdGFpbWFnZS9hbGlnbmVkLWltYWdlcy8gLS1zaXplIDk2DQrmj5Dlj5bnibnlvoENCi4vYmF0Y2gtcmVwcmVzZW50L21haW4ubHVhIC1vdXREaXIgLi9kYXRhaW1hZ2UvZ2VuZXJhdGVkLWVtYmVkZGluZ3MvIC1kYXRhIC4vZGF0YWltYWdlL2FsaWduZWQtaW1hZ2VzLw0K5byA5aeL6K6t57uDDQouL2RlbW9zL2NsYXNzaWZpZXIucHkgdHJhaW4gLi9kYXRhaW1hZ2UvZ2VuZXJhdGVkLWVtYmVkZGluZ3MvDQror4bliKsNCi4vZGVtb3MvY2xhc3NpZmllci5weSBpbmZlciAuL2RhdGFpbWFnZS9nZW5lcmF0ZWQtZW1iZWRkaW5ncy9jbGFzc2lmaWVyLnBrbCAuL2RhdGFpbWFnZS90ZXN0L3Rlc3Q1LmpwZw0KDQpkb2NrZXIgY29weSANCuWuueWZqOWIsOacrOacuu+8mg0KZG9ja2VyIGNwIGNjYWE5YzZmNTM3Mjovcm9vdC9vcGVuZmFjZS9kZW1vcy93ZWIgLi93ZWINCg0K5Li75py65Yiw5a655Zmo77ya5oyC6L29bXYNCmRvY2tlciBydW4gLXYgIOacrOacuuWcsOWdgO+8muWuueWZqOWcsOWdgA0KZG9ja2VyIGNwIOimgeaLt+i0neeahOaWh+S7tui3r+W+hCDlrrnlmajlkI3vvJropoHmi7fotJ3liLDlrrnlmajph4zpnaLlr7nlupTnmoTot6/lvoQNCg0Kb3BlbmZhY2UgZGVtbyB3ZWI6DQovcm9vdC9vcGVuZmFjZS9kZW1vcy93ZWIvc3RhcnQtc2VydmVycy5zaA0KDQpvcGVuZmFjZSBydW46DQpkb2NrZXIgcnVuIC1wIDkwMDA6OTAwMCAtcCA4MDAwOjgwMDAgLXYgRjpcZ2l0aHViXHN3bW9wZW5mYWNlXGRlbW9zOi9yb290L29wZW5mYWNlL2RlbW9zIC10IC1pIGJhbW9zL29wZW5mYWNlIC9iaW4vYmFzaA0KDQpkb2NrZXLlm73lhoXplZzlg4/vvJpodHRwczovL2RvY2tlci5taXJyb3JzLnVzdGMuZWR1LmNuDQpzeXN0ZW1jdGwgZGFlbW9uLXJlbG9hZA0KdmltIC9ldGMvZG9ja2VyL2RhZW1vbi5qc29uDQp7DQogInJlZ2lzdHJ5LW1pcnJvcnMiOiBbImh0dHBzOi8vZG9ja2VyLm1pcnJvcnMudXN0Yy5lZHUuY24iXQ0KfQ0KDQpkb2NrZXLov5vlhaXns7vnu58NCmRvY2tlciBydW4gLWl0IFlPVVJfSU1BR0UgL2Jpbi9zaA0KDQp0aCBuZXVyYWxfc3R5bGUubHVhIC1zdHlsZV9pbWFnZSBzd21zdHlsZS9zdHlsZTguanBnIC1jb250ZW50X2ltYWdlIHN3bWRhdGEvZGF0YTEuanBnIC1vdXRwdXRfaW1hZ2Ugc3dtZ2V0ZGF0YS9nZXQxLnBuZyAtbW9kZWxfZmlsZSBtb2RlbHMvbmluX2ltYWdlbmV0X2NvbnYuY2FmZmVtb2RlbCAtcHJvdG9fZmlsZSBtb2RlbHMvdHJhaW5fdmFsLnByb3RvdHh0IC1ncHUgLTEgLWJhY2tlbmQgY2xubiAtbnVtX2l0ZXJhdGlvbnMgMTAwMCAtc2VlZCAxMjMgLWNvbnRlbnRfbGF5ZXJzIHJlbHUwLHJlbHUzLHJlbHU3LHJlbHUxMiAtc3R5bGVfbGF5ZXJzIHJlbHUwLHJlbHUzLHJlbHU3LHJlbHUxMiAtY29udGVudF93ZWlnaHQgMTAgLXN0eWxlX3dlaWdodCAxMDAwIC1pbWFnZV9zaXplIDUxMiAtb3B0aW1pemVyIGFkYW0NCua4heWNjumVnOWDj++8mnBpcDMgaW5zdGFsbCAtaSBodHRwczovL3B5cGkudHVuYS50c2luZ2h1YS5lZHUuY24vc2ltcGxlIA0KcGlwIGluc3RhbGwgLWkgaHR0cHM6Ly9weXBpLnR1bmEudHNpbmdodWEuZWR1LmNuL3NpbXBsZSBzb21lLXBhY2thZ2UNCnBpcOWuieijheS4jeimgee8k+WtmDotLW5vLWNhY2hlLWRpcg0K5ZCv5YqodWJ1YW50deiZmuaLn+eOr+Wig++8mnNvdXJjZSB+L3RlbnNvcmZsb3cvYmluL2FjdGl2YXRlIA0KDQpkb2NrZXIgdGFnIHN3bS93ZWJzb2NrZXQ6MjAxNzExMDYgMTE2LjYyLjcwLjEyMDo1MDAwL3N3bS93ZWJzb2NrZXQ6MjAxNzExMDYNCg0K5p+l55yLbGludXjniYjmnKzkv6Hmga/vvJpsc2JfcmVsZWFzZSAtYQ0KY2F0IC9wcm9jL3ZlcnNpb24NCg0KY29uZGEgaW5zdGFsbCBvcGVuY3YzDQpjb25kYSBpbnN0YWxsIG51bXB5DQpjb25kYSBpbnN0YWxsIGFuYWNvbmRhLWNsaWVudA0KY29uZGEgaW5zdGFsbCAtLWNoYW5uZWwgaHR0cHM6Ly9jb25kYS5hbmFjb25kYS5vcmcvbWVucG8gb3BlbmN2Mw0KDQpkb2NrZXLkv67mlLnplZzlg4/lkI3lrZcNCi1kIOacjeWKoeWZqOaMgui1t+WcqOWQjuWPsA0KZG9ja2VyIHRhZyBpbWFnZWlkIG5hbWU6dGFnDQoNCnNjcmFweSBjcmF3bCBUd2VldFNjcmFwZXIgLWEgcXVlcnk9IlRydW1wIg0KDQpzc3LlkK/liqjvvJovZXRjL2luaXQuZC9zaGFkb3dzb2Nrcy1yIHN0YXJ0IHwgc3RvcCB8IHJlc3RhcnQgfCBzdGF0dXMNCmRvY2tlcuWvuemVnOWDj+eahOaTjeS9nA0KLuS/neWtmHNhdmUgLSDliqDovb0gbG9hZA0Kd2dldCBqYXZhIC0tbm8tY29va2llcyAtLWhlYWRlciAiQ29va2llOiBvcmFjbGVsaWNlbnNlPWFjY2VwdC1zZWN1cmViYWNrdXAtY29va2llIg0KDQpkb2NrZXIgcnVuIC0tcmVzdGFydCBhbHdheXMgLS1uYW1lPSd0ZWxlZ3JhbV9zd21fMDcyNCcgLXYgL2hvbWUvdGVsZWdyYW0vOi9ob21lL3RlbGVncmFtLyAtZCB0ZWxlZ3JhbToyMDE4MDcyNA0K5a6J6KOFbHNiX3JlYWxlYXNlIDogeXVtIGluc3RhbGwgLXkgcmVkaGF0LWxzYg0KDQrkv67mlLlyb2905a+G56CB77yaIHBhc3N3ZCByb290DQoNCmJ1aWxkIOWMhe+8mnB5dGhvbiBzZXR1cC5weSBiZGlzdF93aGVlbA0K5LiK5Lyg5oiW6ICF5pu05paw5YiwcHlwaXRlc3QNCnB5cGkgdGVzdDp0d2luZSB1cGxvYWQgLS1yZXBvc2l0b3J5LXVybCBodHRwczovL3Rlc3QucHlwaS5vcmcvbGVnYWN5LyBkaXN0LyoNCuS4iuS8oOaIluiAheabtOaWsHB5cGkNCnR3aW5lIHVwbG9hZCBkaXN0LyoNCg0K5a6J6KOF77yacGlwIGluc3RhbGwgdHdpbmUNCnB5cGnnmoTotKblj7dnbWFpbCx1c2VybmFtZTpvY3RvYmVyDQoNCmdpdGh1YuS4u+mhtQ0KaHR0cHM6Ly9naXRodWIuY29tL09jdG9iZXJyP3RhYj1yZXBvc2l0b3JpZXMNCnB5dGhvbuekvuWMunB5cGnkuLvpobUNCmh0dHBzOi8vcHlwaS5vcmcvcHJvamVjdC9zd210b29scy8NCmRvY2tlcuekvuWMumRvY2tlcmh1YuS4u+mhtQ0KaHR0cHM6Ly9odWIuZG9ja2VyLmNvbS91L3NoaXl1ZQ0KSnVzdCBNeSBTb2Nrcw0K6LSm5Y+377yaZ21haWwganVkeQ0KDQrllIkNClRvZGF5YHMgd2luZCBpcyBhIGxpdHRsZSB1cHJvYXJpb3VzLiANCg0K5a655Zmo5YaFc3No5ZCv5YqoDQovZXRjL2luaXQuZC9zc2ggcmVzdGFydA0KDQrkv67mlLlpcHRhYmxlcyANCi9ldGMvc3lzY29uZmlnL2lwdGFibGVzICANCi1BIElOUFVUIC1wIHVkcCAtbSBzdGF0ZSAtLXN0YXRlIE5FVyAtbSB1ZHAgLS1kcG9ydCA0NTU2IC1qIEFDQ0VQVA0KLUEgSU5QVVQgLXAgdGNwIC1tIHN0YXRlIC0tc3RhdGUgTkVXIC1tIHRjcCAtLWRwb3J0IDQ1NTYgLWogQUNDRVBUDQotQSBJTlBVVCAtcCB0Y3AgLW0gc3RhdGUgLS1zdGF0ZSBORVcgLW0gdGNwIC0tZHBvcnQgODAwOSAtaiBBQ0NFUFQNCi1BIElOUFVUIC1wIHRjcCAtbSBzdGF0ZSAtLXN0YXRlIE5FVyAtbSB0Y3AgLS1kcG9ydCA4MDEwIC1qIEFDQ0VQVA0KLUEgSU5QVVQgLXAgdGNwIC1tIHN0YXRlIC0tc3RhdGUgTkVXIC1tIHRjcCAtLWRwb3J0IDIyIC1qIEFDQ0VQVA0KLUEgSU5QVVQgLXAgdGNwIC1tIHN0YXRlIC0tc3RhdGUgTkVXIC1tIHRjcCAtLWRwb3J0IDEwMDIyIC1qIEFDQ0VQVA0KY3VybCBodHRwOi8veW91ci1zZXJ2ZXItaXA6NTAwMC92Mi9fY2F0YWxvZw0KDQrmi4nlj5ZzZXJ2ZXLkuIrnmoTplZzlg48NCuS/ruaUueaWh+S7tiAvZXRjL2RvY2tlci9kYWVtb24uanNvbg0KICAiaW5zZWN1cmUtcmVnaXN0cmllcyI6IFsNCiAgICAiMTE1LjE0NC4xNzguNDU6NTAwMCINCiAgXQ0KIA0KIA0KbGludXgg6K6h5pWwIGZpbmQgX3NlcnZlcmlucHV0IC10eXBlIGYgfCB3YyAtbA0KDQoNCg0KDQoNCg0KDQoNCg0KDQo=
--jtkspbrk5nhd--"""
        # jtkspbrk5nhd这个字符需要和headers里面的content-type相同，可以直接使用，目前还不知道是如何生成的

        # 文件是读二进制然后进行base64加密，parents里面的id为要上传的文件夹，要想指定文件夹，得先做一个文件夹id的对照表
        response = self.sa.post(url, headers=headers, data=payload)
        print(response.text)

    def g_upload_big_file(self):
        """
        上传大文件
        :return:
        """

    def g_upload_files(self):
        """
        上传文件夹
        :return:
        """

    def g_rename_file(self):
        """
        重命名文件
        :return:
        """
        # url里面有3个东西
        # field 是需要修改的文件的id，文件的名字随便改但是id是不会改变的
        # expectedParentIds 这是父级目录的id,这个账号根目录的id就是下面那个
        # key需要登陆拿到
        url = """https://clients6.google.com/drive/v2internal/files/1BlRX_-MswLH6zeCUup9XXOwj6I1TsWbrT1xMqf3sV8g?openDrive=false&reason=912&syncType=0&errorRecovery=false&fields=kind%2CmodifiedDate%2ChasVisitorPermissions%2CcontainsUnsubscribedChildren%2CmodifiedByMeDate%2ClastViewedByMeDate%2CfileSize%2Cowners(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cdomain%2Cid)%2ClastModifyingUser(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cid)%2CancestorHasAugmentedPermissions%2ChasThumbnail%2CthumbnailVersion%2Ctitle%2Cid%2Cshared%2CsharedWithMeDate%2CuserPermission(role)%2CexplicitlyTrashed%2CmimeType%2CquotaBytesUsed%2Ccopyable%2Csubscribed%2CfolderColor%2ChasChildFolders%2CfileExtension%2CprimarySyncParentId%2CsharingUser(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cid)%2CflaggedForAbuse%2CfolderFeatures%2Cspaces%2CsourceAppId%2Crecency%2CrecencyReason%2Cversion%2CactionItems%2CteamDriveId%2ChasAugmentedPermissions%2CcreatedDate%2CprimaryDomainName%2CorganizationDisplayName%2CpassivelySubscribed%2CtrashingUser(kind%2CpermissionId%2CdisplayName%2Cpicture%2CemailAddress%2Cid)%2CtrashedDate%2Cparents(id)%2Ccapabilities(canMoveItemIntoTeamDrive%2CcanUntrash%2CcanMoveItemWithinTeamDrive%2CcanMoveItemOutOfTeamDrive%2CcanTrashChildren%2CcanAddMyDriveParent%2CcanRemoveMyDriveParent%2CcanShareChildFiles%2CcanShareChildFolders%2CcanRead%2CcanCopy%2CcanDownload%2CcanEdit%2CcanAddChildren%2CcanDelete%2CcanRemoveChildren%2CcanShare%2CcanTrash%2CcanRename%2CcanReadTeamDrive%2CcanMoveTeamDriveItem)%2CcontentRestrictions(readOnly)%2CshortcutDetails(targetId%2CtargetMimeType%2CtargetLookupStatus%2CtargetFile%2CcanRequestAccessToTarget)%2Clabels(starred%2Ctrashed%2Crestricted%2Cviewed)&modifiedDateBehavior=DRIVE_UI&updateViewedDate=false&fileId=1BlRX_-MswLH6zeCUup9XXOwj6I1TsWbrT1xMqf3sV8g&languageCode=zh-CN&supportsTeamDrives=true&expectedParentIds=0AIj1GZky9BXBUk9PVA&key=AIzaSyAy9VVXHSpS2IJpptzYtGbLP3-3_l0aBk4"""
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'authorization': 'SAPISIDHASH 1582536000_731154be5cd52e9eeae022fcbc57908b82553ccc_u',
            'cache-control': 'no-cache',
            'content-length': '18',
            'content-type': 'application/json',
            'cookie': self.cookies,
            'origin': 'https://drive.google.com',
            'pragma': 'no-cache',
            'referer': 'https://drive.google.com/drive/my-drive',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36',
            'x-goog-authuser': '0'
        }
        payload = """{"title":"judy.txt"}"""
        # 这里的title为需要修改的名字
        response = self.sa.put(url, headers=headers, data=payload)
        rtext = response.text
        print(rtext)
        res = """
        {
 "kind": "drive#file",
 "id": "1BlRX_-MswLH6zeCUup9XXOwj6I1TsWbrT1xMqf3sV8g",
 "thumbnailVersion": "3",
 "title": "judy.txt",
 "mimeType": "application/vnd.google-apps.document",
 "labels": {
  "starred": false,
  "trashed": false,
  "restricted": false,
  "viewed": true
 },
 "createdDate": "2019-10-23T03:07:50.349Z",
 "modifiedDate": "2020-02-24T09:34:45.496Z",
 "modifiedByMeDate": "2020-02-24T09:34:45.496Z",
 "lastViewedByMeDate": "2020-02-24T09:07:03.341Z",
 "recency": "2020-02-24T09:34:45.496Z",
 "recencyReason": "modifiedByMe",
 "version": "14",
 "parents": [
  {
   "id": "0AIj1GZky9BXBUk9PVA"
  }
 ],
 "userPermission": {
  "role": "owner"
 },
 "quotaBytesUsed": "0",
 "owners": [
  {
   "kind": "drive#user",
   "displayName": "sb nm",
   "id": "113532497580613589902",
   "permissionId": "13393928096485412760",
   "emailAddress": "nmsbgg@gmail.com"
  }
 ],
 "lastModifyingUser": {
  "kind": "drive#user",
  "displayName": "sb nm",
  "id": "113532497580613589902",
  "permissionId": "13393928096485412760",
  "emailAddress": "nmsbgg@gmail.com"
 },
 "capabilities": {
  "canAddChildren": false,
  "canAddMyDriveParent": false,
  "canCopy": true,
  "canDelete": true,
  "canDownload": true,
  "canEdit": true,
  "canMoveItemIntoTeamDrive": true,
  "canRead": true,
  "canRemoveChildren": false,
  "canRemoveMyDriveParent": true,
  "canRename": true,
  "canShare": true,
  "canShareChildFiles": false,
  "canShareChildFolders": false,
  "canTrash": true,
  "canUntrash": true
 },
 "copyable": true,
 "shared": false,
 "explicitlyTrashed": false,
 "primarySyncParentId": "0AIj1GZky9BXBUk9PVA",
 "subscribed": true,
 "passivelySubscribed": false,
 "flaggedForAbuse": false,
 "sourceAppId": "619683526622",
 "spaces": [
  "drive",
  "DRIVE"
 ],
 "hasThumbnail": true,
 "containsUnsubscribedChildren": false
}
        """


if __name__ == '__main__':
    gu = GoogleDrive()
    # gu.gmkdir()
    # gu.g_upload_file()
    gu.g_rename_file()
