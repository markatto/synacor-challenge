# _ + _ * _^2 + _^3 - _ = 399

# tried: 
# x + x * x**2 + x**3 - x = 399
# put that into wolfram alpha, ~5.8432

from itertools import permutations

coins = {
    2: 'red',
    7: 'concave',
    3: 'corroded',
    9: 'blue',
    5: 'shiny'
}

def f(a, b, c, d, e):
    return a + b * c**2 + d**3 - e == 399


order = [i for i in permutations(coins.keys()) if f(*i)][0]
for num in order:
    print("use %s coin" % coins[num])

