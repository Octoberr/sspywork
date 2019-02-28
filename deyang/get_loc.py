import csv
import json

import requests


class GetLoc(object):

    def __init__(self):
        self.key = '77f1918496c8576615ef569eaa2e5ff6'

    def readfile(self):
        with open('deyangfangjia.csv', newline='', encoding='utf-8') as csvfile:
            dialect = csv.Sniffer().has_header(csvfile.read(1024))
            csvfile.seek(0)
            if dialect:
                next(csvfile)
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                yield row

    def get_loc(self):
        csvfile = open('deyangloc.csv', 'w', newline='', encoding='utf-8')
        fieldnames = ['areaname', 'price', 'gglat', 'gglng']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in self.readfile():
            url = 'https://restapi.amap.com/v3/geocode/geo?key={}&address={}&city=德阳'.format(self.key, data[0])
            print(url)
            res = requests.get(url)
            res_json = json.loads(res.text)
            try:
                locdata = res_json.get('geocodes')[0].get('location')
                location = locdata.split(',')
                lng = location[0]
                lat = location[1]
            except:
                lng = '0000'
                lat = '0000'
            writer.writerow({'areaname': data[0], 'price': data[-1], 'gglat': lat, 'gglng': lng})
        csvfile.close()


if __name__ == '__main__':
    gl = GetLoc()
    gl.get_loc()
    # gl.readfile()
