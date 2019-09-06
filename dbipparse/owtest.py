"""
一千万条数据的测试
"""

import sqlite3
import time

conn = sqlite3.connect('example.db')

c = conn.cursor()

# Create table
# c.execute('''CREATE TABLE stocks
#              (id int, uniquedata text)''')

# Insert a row of data
# count = 0
# with open("C:\\Users\\october\\Desktop\\allCountries.txt", 'r', encoding='utf-8') as f:
#     for line in f:
#         count += 1
#         str_md5 = helper_crypto.get_md5_from_str(line)
#         sql = "INSERT INTO stocks(id, uniquedata) VALUES (?, ?)"
#         val = (count, str_md5)
#         c.execute(sql, val)
#         print(f"Store {count} data, str:{str_md5}")
sql = 'select count(1) from stocks where uniquedata=?'
val = ('7500685737dc503deff5ad7c338e0756',)
time1 = int(time.time())
for i in range(10000000):
    c.execute(sql, val)
    print(i)
time2 = int(time.time())
print(f'使用时间：{(time2 - time1) / 60}')
# Save (commit) the changes
conn.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()
