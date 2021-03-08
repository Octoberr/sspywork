"""helper for number"""

# -*- coding:utf-8 -*-

import math


class MakeNumber:
    """make new number"""

    def __init__(self, chars: [], initIdx=-1):
        if chars is None or len(chars) < 1:
            raise Exception("Chars cannot be empty.")
        self._chars = chars
        self._currIdx = -1
        if isinstance(initIdx, int) and initIdx > -1:
            self._currIdx = initIdx

    def get_next(self):
        """get the next number of this instance."""
        res: list = []
        self._currIdx += 1
        tmp = self._currIdx
        if tmp == 0:
            return ''.join(self._chars[0])
        di = 1
        while di > 0 and tmp >= di:
            currCharIdx = int((tmp / di) % len(self._chars))
            res.insert(0, self._chars[currCharIdx])

            if di == 1:
                di = len(self._chars)
            else:
                di = math.pow(di, 2)

        return ''.join(res)


if __name__ == "__main__":
    # 创建一个36进制数，每次调用get_next()即取下一个数
    mk = MakeNumber([
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d",
        "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r",
        "s", "t", "u", "v", "w", "x", "y", "z"
    ])
    for i in range(10000):
        print(mk.get_next())
    a = 0
