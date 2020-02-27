# def fib2(n): # 返回到 n 的斐波那契数列
#     result = []
#     a, b = 0, 1
#     while b < n:
#         result.append(b)
#         a, b = b, a+b
#     return result
#
# a = fib2(500)
# print(a)


def recur_fibo(n):
   """递归函数
   输出斐波那契数列"""
   if n <= 1:
       return n
   else:
       return(recur_fibo(n-1) + recur_fibo(n-2))


a = recur_fibo(10)
print(a)