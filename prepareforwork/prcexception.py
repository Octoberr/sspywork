"""
异常处理
createby swm 20180514
"""


def divide(x, y):
    try:
        res = x/y
    except:
        print("division by zero")
    else:
        print("result is:", res)
    finally:
        print("finally clause!")

# divide(2, 1)


def this_fails():
    x = 1/0

try:
    this_fails()
except Exception as err:
    print('Handling run-time error:', err)
