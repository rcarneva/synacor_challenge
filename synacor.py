from itertools import zip_longest
import sys
from collections import defaultdict

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)

lmap = lambda fn, x: list(map(fn, x))

code = open("challenge.bin", "rb").read()
code = [n1+n2*256 for n1, n2 in grouper(code, 2)]

REG_OFFSET = 32768
regs = {v: 0 for v in range(8)}

reg8 = int(sys.argv[1]) if len(sys.argv) >= 2 else 0

mem = defaultdict(int, {i: v for i, v in enumerate(code)})

inputbuffer = []


def deref(a):
    return a if a < REG_OFFSET else regs[a-REG_OFFSET]

def halt():
    return "HALT"

def _set(a, b):
    global regs
    regs[a-REG_OFFSET] = deref(b)

def eq(a, b, c):
    global regs
    regs[a-REG_OFFSET] = 1 if deref(b) == deref(c) else 0

def gt(a, b, c):
    global regs
    regs[a-REG_OFFSET] = 1 if deref(b) > deref(c) else 0

def add(a, b, c):
    global regs
    try:
        regs[a-REG_OFFSET] = (deref(b) + deref(c)) % REG_OFFSET
    except TypeError as e:
        print(ip, a, b, c, REG_OFFSET, list(map(type, [a,b,c])))
        raise e

def mult(a, b, c):
    global regs
    regs[a-REG_OFFSET] = (deref(b) * deref(c)) % REG_OFFSET

def mod(a, b, c):
    global regs
    regs[a-REG_OFFSET] = deref(b) % deref(c)

def _and(a, b, c):
    global regs
    regs[a-REG_OFFSET] = deref(b) & deref(c)

def _or(a, b, c):
    global regs
    regs[a-REG_OFFSET] = deref(b) | deref(c)

def _not(a, b):
    global regs
    regs[a-REG_OFFSET] = ~deref(b) & 0x7FFF

def out(a):
    print(chr(deref(a)), end="")

def jmp(a):
    global ip
    ip = deref(a)-1

def jt(a, b):
    global ip
    if deref(a) != 0:
        ip = deref(b)-1

def jf(a, b):
    global ip
    if deref(a) == 0:
        ip = deref(b)-1

def push(a):
    global stack
    stack.append(deref(a))

def pop(a):
    global stack
    regs[a-REG_OFFSET] = stack.pop()

def call(a):
    global stack, ip
    stack.append(ip+1)
    ip = deref(a)-1

def ret():
    global stack, ip
    ip = stack.pop()-1

def rmem(a, b):
    global mem
    regs[a-REG_OFFSET] = mem[deref(b)]

def wmem(a, b):
    global mem
    mem[deref(a)] = deref(b)

inhistory = []

def _in(a):
    global inputbuffer, regs
    regs[7] = reg8
    shorts = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west'}
    if len(inputbuffer) == 0:
        i = input()
        if i == "quit":
            print("-"*120)
            print('\n'.join(inhistory))
            exit()
        if i in shorts:
            i = shorts[i]
        inhistory.append(i)
        for c in i:
            inputbuffer.append(c)
        inputbuffer.append("\n")
    regs[a-REG_OFFSET] = ord(inputbuffer.pop(0))

def noop():
    pass

def not_impl(*args):
    print("{}".format(args), file=sys.stderr, end=" ")

insts = {0: halt, 1: _set,
         2: push, 3: pop,
         4: eq, 5: gt,
         6: jmp, 7: jt, 8: jf,
         9: add, 10: mult, 11: mod,
         12: _and, 13: _or, 14: _not,
         15: rmem, 16: wmem,
         17: call, 18: ret, 19: out,
         20: _in,
         21: noop}

s = 'hlt: 0\nset: 1 a b\npush: 2 a\npop: 3 a\neq: 4 a b c\ngt: 5 a b c\njmp: 6 a\njt: 7 a b\njf: 8 a b\nadd: 9 a b c\nmult: 10 a b c\nmod: 11 a b c\nand: 12 a b c\nor: 13 a b c\nnot: 14 a b\nrmem: 15 a b\nwmem: 16 a b\ncall: 17 a\nret: 18\nout: 19 a\nin: 20 a\nnoop: 21'
code_takes = {int(l[1]): len(l)-2 for l in lmap(str.split, s.split("\n"))}

program = []
left = 0
for c in code:
    if left > 0:
        program[-1].append(c)
        left -= 1
    else:
        program.append([c])
        left = code_takes.get(c, 0)

ip = 0
stack = []
regs = {v: 0 for v in range(8)}
mem = defaultdict(int, {i: v for i, v in enumerate(code)})

def exec():
    global ip
    left = 0
    res = None
    while res != "HALT":
        c = mem[ip]
        if left == 0:
            fn = insts.get(c, not_impl)
            cmd = c
            left = code_takes[c]
            args = []
            if fn == not_impl:
                args.append(c)
        else:
            args.append(c)
            left -= 1
        if left == 0:
            res = fn(*args)
        ip += 1
exec()
