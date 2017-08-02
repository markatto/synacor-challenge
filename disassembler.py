#! /usr/bin/env python
import inspect
import sys
from interpreter import Machine, INT_SIZE, MAX_INT, REGISTER_COUNT

# reuse the loader and some other stuff from the Machine class
m = Machine()
m.load_program()
data = m.memory

def eval_num(x):
    assert x <= MAX_INT + REGISTER_COUNT
    #numbers 0..32767 mean a literal value
    if x <= MAX_INT:
        return str(x)
    # numbers 32768..32775 instead mean registers 0..7
    register = x - INT_SIZE
    return 'r%d' % register

def decode_instruction(pos):
    instruction_num = data[pos]
    instruction = Machine.opcodes[instruction_num]
    instruction_name = instruction.__name__[2:] # strip off the "I_" prefix
    instruction_size = len(inspect.getargspec(instruction).args)
    args = data[pos + 1: pos + instruction_size]

    args = map(eval_num, args)
    # if out, convert to character
    if instruction_name == 'out':
        a = args[0]
        if a[0] != 'r':
            args[0] = unichr(int(a))

    print("{}\t{}\t{}".format(pos, instruction_name.upper(), "\t".join(args)))
    return instruction_size


pos = int(sys.argv[1])
while pos < len(data):
    try:
        pos += decode_instruction(pos)
    except Exception as e:
        print("%d\tDATA\t%d" % (pos, data[pos]))
        pos += 1
