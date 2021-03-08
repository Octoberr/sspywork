"""
拷贝
"""

import copy

a = [1, 2, 3, 4, [5, 6], 7]
b = copy.copy(a)
c = copy.deepcopy(a)

# b.append(8)
# b[4].append(7)
c.append(8)
c[4].append(7)

print(b)
print(a)
