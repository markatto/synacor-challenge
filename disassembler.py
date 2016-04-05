#! /usr/bin/env python
import inspect
import sys
from interpreter import Machine

INT_SIZE = 32768 # 2**15
MAX_INT = INT_SIZE - 1
REGISTER_COUNT = 8

opcode_names = [
        "halt", #0
        "set",  #1
        "push", #2
        "pop",  #3
        "eq",   #4
        "gt",   #5
        "jmp",  #6
        "jt",   #7
        "jf",   #8
        "add",  #9
        "mult", #10
        "mod",  #11
        "and",  #12
        "or",   #13
        "not",  #14
        "rmem", #15
        "wmem", #16
        "call", #17
        "ret",  #18
        "out",  #19
        "in",   #20
        "noop", #21
]

# reuse the loader and some other stuff from the Machine class
m = Machine()
m.load_program()

data = m.memory
pos = int(sys.argv[1])

def eval_num(x):
    #numbers 0..32767 mean a literal value
    if x <= MAX_INT:
        return x
    # numbers 32768..32775 instead mean registers 0..7
    if x <= MAX_INT + REGISTER_COUNT:
        register = x - INT_SIZE
        return 'r%d' % register
    assert False # illegal


def decode_instruction():
    global pos
    instruction_num = data[pos]
    instruction = Machine.opcodes[instruction_num]
    instruction_name = opcode_names[instruction_num]
    # this is why python is cool
    instruction_size = len(inspect.getargspec(instruction).args)
    args = data[pos + 1: pos + instruction_size]


    ### pretty printing ###

    args = [str(eval_num(arg)) for arg in args]
    # if out, convert to character
    if instruction_name == 'out':
        a = args[0]
        if a[0] != 'r':
            args[0] = unichr(int(a))


    print("{}\t{}\t{}".format(pos, instruction_name.upper(), "\t".join(args)))

    pos += instruction_size

while True:
    decode_instruction()
