a = []

for i in range(100):
    a.append(i)

if (n := len(a)) > 10:
    print(f"List is too long ({n} elements, expected <= 10)")