# import pymysql
#
# db = pymysql.connect(host="192.168.90.42", user="root", password="123456", database="14yidata")
# db_curs = db.cursor()
# sql = '''
# INSERT INTO alla(email, password) VALUES (%s, %s);
# '''
# manydata = [('test1@gmail.com', '12313'), ('test2@gmail.com', '12421212')]
# db_curs.executemany(sql, manydata)
# db.commit()
# print(f'Insert 4W data ok')
# db.close()
# a = "017208e7510e6c042f8cf3a1605d9ad9	wooden@doctorsmb.info	,r#d8S\\3ngX%P.~lq<&B7HXkxsEnk"
# print(a.split('\t')[1:])
from pathlib import Path

road = Path(r"E:\safedata\BreachCompilation\data")


def get_file(path: Path):
    a = []
    for el in path.iterdir():
        if el.is_dir():
            get_file(el)
        else:
            print(el.as_posix())



get_file(road)