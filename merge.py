def btest(c):
    a = 0
    b = 0
    l3 = []
    for i in range(c):

        if l1[a] < l2[b]:
            l3.append(l1[a])
            a += 1
        else:
            l3.append(l2[b])
            b += 1
        if a == len(l1) or b == len(l2):
            break
    while a < len(l1):
        l3.append(l1[a])
        a += 1
    while b < len(l2):
        l3.append(l2[b])
        b += 1
    return l3

if __name__ == '__main__':
    l1 = [1, 8, 500]
    l2 = [1, 5, 8, 100, 200]
    c = len(l1) + len(l2)
    print btest(c)
