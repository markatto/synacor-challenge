x = 0
a = 0
b = 0
def f():
    if a != 0:
        a = b + 1
        return
    if b != 0:
        a -= 1
        b = x
        f()
        return
