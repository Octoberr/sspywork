import maxminddb
import json

reader = maxminddb.open_database('./dbip.mmdb')
res = reader.get('0.0.0.0')
# print(json.dumps(res, ensure_ascii=False))
print(res, type(res))
reader.close()
