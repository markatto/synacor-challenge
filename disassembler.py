#!/usr/bin/env python3
import sys
from interpreter import Machine, INT_SIZE, MAX_INT, REGISTER_COUNT

# reuse the loader and some other stuff from the Machine class
m = Machine()
m.load_program()
data = m.m


def eval_num(x: int) -> str:
    assert x <= MAX_INT + REGISTER_COUNT
    # numbers 0..32767 mean a literal value
    if x <= MAX_INT:
        return str(x)
    # numbers 32768..32775 instead mean registers 0..7
    register = x - INT_SIZE
    return f'r{register}'


def decode_instruction(pos: int) -> int:
    instruction_num = data[pos]
    if instruction_num not in m.opcodes:
        raise IndexError(f'Invalid opcode: {instruction_num}')
    instruction = m.opcodes[instruction_num]
    instruction_name = instruction.name
    instruction_size = 1 + instruction.arity
    raw_args = data[pos + 1 : pos + instruction_size]

    args = list(map(eval_num, raw_args))
    # if out, convert to character
    if instruction_name == 'out' and args:
        a = args[0]
        if a[0] != 'r':
            args[0] = chr(int(a))

    print('{}\t{}\t{}'.format(pos, instruction_name.upper(), '\t'.join(args)))
    return instruction_size


pos = int(sys.argv[1])
while pos < len(data):
    try:
        pos += decode_instruction(pos)
    except Exception:
        print(f'{pos}\tDATA\t{data[pos]}')
        pos += 1
