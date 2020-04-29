# import argparse
#
#
# class aaa:
#
#     def __init__(self):
#         self.parser = argparse.ArgumentParser()
#         self.parser.add_argument("square", help="display a square of a given number", type=int)
#         self.parser.add_argument("-v", "--verbose", help="increase output verbosity")
#         self.args = self.parser.parse_args()
#
#     def pdata(self):
#         print(self.args.verbose)
#         print(type(self.args.verbose))
#         if self.args.verbose is None:
#             print("unsupport None")
#
#
# if __name__ == '__main__':
#     a = aaa()
#     a.pdata()

fields = ['ip', 'continent', 'country', 'province', 'city', 'lat', 'lng', 'isp', 'org']
stri = '    '.join(fields)
print(stri)