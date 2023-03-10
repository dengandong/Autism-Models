file = open('ESDB_test.txt', 'r').readlines()

n0 = 0
n1 = 0
n2 = 0
n3 = 0
for i in file:
    id = i.split(' ')[-1]
    if int(id) == 0:
        n0 += 1
    elif int(id) == 1:
        n1 += 1
    elif int(id) == 2:
        n2 += 1
    else:
        n3 += 1

print(n0, n1, n2, n3)
