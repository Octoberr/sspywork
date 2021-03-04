"""
随机全球的ip
create by judy 20201230
"""
import random
import sqlite3
import traceback
import IPy
import json


class RangeIP(object):

    def __init__(self) -> None:
        self.count = 22009743

    def get_sqlinfo(self, id_str):
        """
        docstring
        """
        sql_path = r"D:\gitcode\idown_new\_ip_location_dbs\dbipsqlite\2020-12.sqlite"
        conn = sqlite3.connect(sql_path)
        c = conn.cursor()
        sql = '''select * from  dbip where ID=? '''
        pars = (id_str, )
        c.execute(sql, pars)
        res = c.fetchall()
        conn.close()
        return res[0]

    def process_ips(self, sqlinfo):
        """
        docstring
        """
        st = IPy.IP(sqlinfo[1])
        sp = IPy.IP(sqlinfo[2])
        if sp.int() - st.int() >= 255:
            for i in range(st.int(), sp.int() + 1):
                ipstr: str = IPy.IP(i).strNormal()
                if ipstr.endswith(".0"):
                    return ipstr + "/24" + '\n'
        else:
            return None

    def start(self):
        """
        随机获取全球20个ip
        """
        ips = ''
        count = 0
        while count < 20:

            id_str = random.randint(1, self.count)
            sqlinfo = self.get_sqlinfo(id_str)
            ip = self.process_ips(sqlinfo)
            if ip is not None:
                ips += ip
                count += 1

        return ips


if __name__ == "__main__":
    rip = RangeIP()
    for i in range(20):
        res = rip.start()
        with open('./扫描速率测试使用ip段.txt', 'a', encoding='utf-8') as fp:
            fp.write(res+'\n\n')
