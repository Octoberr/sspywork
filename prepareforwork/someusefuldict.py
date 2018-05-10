"""
一些需要用到的字段，存入本地的mongodb数据库
createby swm 2018/05/03
"""
import json

import pymongo
import datetime


class MONGO:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def getquerydate(self):
        client = pymongo.MongoClient(host=self.host, port=self.port)
        db = client.swmdb
        eagleyedates = db.zoomeyeclass
        res = eagleyedates.find()
        return res

    def insertintomongo(self, zoomeyedata):
        client = pymongo.MongoClient(host=self.host, port=self.port)
        db = client.swmdb
        zoomeyedict = db.domainname
        zoomeyedict.insert(zoomeyedata)
        print(datetime.datetime.now(), 'insert mongodb success')


if __name__ == '__main__':
    geta = MONGO("localhost", 27017)
    res = geta.getquerydate()
    for i in res:
        del i['_id']
        with open('relation.json', 'a') as file:
           jsonres = json.dumps(i)
           file.write(jsonres)
        file.close()