"""
异常处理
createby swm 20180514
"""

class ZYY:

    def __init__(self, num):
        self.num = num

    def changhe(self):
        self.num = 123
        print(self.num)

    def getnum(self):
        print(self.num)


#
# def divide(x, y):
#     try:
#         res = x/y
#     except:
#         print("division by zero")
#     else:
#         print("result is:", res)
#     finally:
#         print("finally clause!")
#
# # divide(2, 1)
#
#
# def this_fails():
#     x = 1/0
#
# try:
#     this_fails()
# except Exception as err:
#     print('Handling run-time error:', err)

if __name__ == '__main__':
    z = ZYY(111)
    z.changhe()
    z.getnum()