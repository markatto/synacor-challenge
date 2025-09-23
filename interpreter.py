#! /usr/bin/env python3
import array
import sys
import signal
import pickle
import logging
import types
from datetime import datetime
from inspect import signature, getfullargspec
from typing import Dict, List, Optional, Callable, Any

# VM implementing the architecture defined in the file "arch-spec.txt"
# arch-spec comes from https://challenge.synacor.com/

INT_SIZE = 2 ** 15
MAX_INT = INT_SIZE - 1
REGISTER_COUNT = 8

# Module-level registry for opcodes
opcode_specs: Dict[int, Callable] = {}

def opcode(num: int) -> Callable[[Callable], Callable]:
    '''Decorator for registering opcodes'''
    def decorator(func: Callable) -> Callable:
        if num in opcode_specs:
            raise ValueError(f"Duplicate opcode {num}: {func.__name__} vs {opcode_specs[num].__name__}")
        opcode_specs[num] = func
        return func
    return decorator


class Opcode:
    '''
    TODO make words
    '''
    def __init__(self, num: int, impl: Callable[..., Any]) -> None:
        self.num: int = num
        self.impl: Callable[..., Any] = impl
        self.name: str = impl.__name__.lstrip('i_')
        self.params: List[str] = getfullargspec(impl).args[1:]  # Skip 'self'
        self.arity: int = len(self.params)
        self.doc: str = (impl.__doc__ or '').strip()
        # TODO: Add instance-specific profiling stats

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.impl(*args, **kwargs)

class Machine(object):
    '''
    Machine objects contain all the state of a virtual CPU, as well as the
    attached memory and I/O.
    '''

    def __init__(self) -> None:
        # 15-bit address space
        self.m: List[int] = [0] * INT_SIZE
        self.r: List[int] = [0] * REGISTER_COUNT
        self.stack: List[int] = []
        # program counter / instruction pointer
        self.pc: int = 0
        self.input_buffer: List[str] = []

        # Build instance-specific opcode list
        max_opcode = max(opcode_specs.keys())
        self.opcodes: List[Optional[Opcode]] = [None] * (max_opcode + 1)

        for num, func in opcode_specs.items():
            bound_method = types.MethodType(func, self)
            self.opcodes[num] = Opcode(num, bound_method)

    def load_program(self, filename: str = 'challenge.bin') -> None:
        ''' Load the contents of a file into the start of memory. '''
        with open(filename, 'rb') as f:
            data = f.read()
        data = array.array('H', data)

        #insert at the beginning of memory
        self.m[:len(data)] = data

    @staticmethod
    def eval_reg(x: int) -> int:
        ''' Turn a "direct format number" into a register number. '''
        assert MAX_INT < x <= MAX_INT + REGISTER_COUNT
        return x - INT_SIZE

    def eval_num(self, x: int) -> int:
        assert x <= MAX_INT + REGISTER_COUNT
        #numbers 0..32767 mean a literal value
        if x <= MAX_INT:
            return x
        return self.r[self.eval_reg(x)]


    @opcode(0)
    def i_halt(self) -> None:
        ''' Halt '''
        sys.exit(0)
    @opcode(1)
    def i_set(self, a: int, b: int) -> None:
        ''' Set register a to value of <b>. '''
        self.r[self.eval_reg(a)] = self.eval_num(b)
    @opcode(2)
    def i_push(self, a: int) -> None:
        ''' Push the value of <a> onto the stack. '''
        self.stack.append(self.eval_num(a))
    @opcode(3)
    def i_pop(self, a: int) -> None:
        ''' Pop stack into register a. '''
        self.r[self.eval_reg(a)] = self.stack.pop()
    @opcode(4)
    def i_eq(self, a: int, b: int, c: int) -> None:
        ''' <a> = 1 if b == c else 0 '''
        self.r[self.eval_reg(a)] = int(self.eval_num(b) == self.eval_num(c))
    @opcode(5)
    def i_gt(self, a: int, b: int, c: int) -> None:
        ''' register a is 1 if b > c '''
        self.r[self.eval_reg(a)] = int(self.eval_num(b) > self.eval_num(c))
    @opcode(6)
    def i_jmp(self, a: int) -> None:
        ''' jump to <a> '''
        self.pc = self.eval_num(a)
    @opcode(7)
    def i_jt(self, a: int, b: int) -> None:
        ''' jump to location <b> if <a> is true (nonzero)'''
        if self.eval_num(a) != 0:
            self.pc = self.eval_num(b)
    @opcode(8)
    def i_jf(self, a: int, b: int) -> None:
        ''' jump to location <b> if <a> is false (0)'''
        if self.eval_num(a) == 0:
            self.pc = self.eval_num(b)
    @opcode(9)
    def i_add(self, a: int, b: int, c: int) -> None:
        ''' <a> = <b> + <c> '''
        self.r[self.eval_reg(a)] = (self.eval_num(b) + self.eval_num(c)) % INT_SIZE
    @opcode(10)
    def i_mult(self, a: int, b: int, c: int) -> None:
        ''' <a> = <b> * <c> '''
        self.r[self.eval_reg(a)] = (self.eval_num(b) * self.eval_num(c)) % INT_SIZE
    @opcode(11)
    def i_mod(self, a: int, b: int, c: int) -> None:
        ''' <a> = <b> % <c> '''
        self.r[self.eval_reg(a)] = (self.eval_num(b) % self.eval_num(c)) % INT_SIZE
    @opcode(12)
    def i_and(self, a: int, b: int, c: int) -> None:
        ''' <a> = <b> & <c> '''
        self.r[self.eval_reg(a)] = (self.eval_num(b) & self.eval_num(c)) % INT_SIZE
    @opcode(13)
    def i_or(self, a: int, b: int, c: int) -> None:
        ''' <a> = <b> | <c> '''
        self.r[self.eval_reg(a)] = (self.eval_num(b) | self.eval_num(c)) % INT_SIZE
    @opcode(14)
    def i_not(self, a: int, b: int) -> None:
        ''' <a> = ~<b> '''
        self.r[self.eval_reg(a)] = (~self.eval_num(b)) % INT_SIZE
    @opcode(15)
    def i_rmem(self, a: int, b: int) -> None:
        ''' read memory at address <b> and write it to <a> '''
        self.r[self.eval_reg(a)] = self.m[self.eval_num(b)]
    @opcode(16)
    def i_wmem(self, a: int, b: int) -> None:
        ''' write the value from <b> into memory at address <a>'''
        self.m[self.eval_num(a)] = self.eval_num(b)
    @opcode(17)
    def i_call(self, a: int) -> None:
        ''' write the address of the next instruction to the stack and jump to <a> '''
        self.stack.append(self.pc)
        self.pc = self.eval_num(a)
    @opcode(18)
    def i_ret(self) -> None:
        ''' remove the top element from the stack and jump to it; empty stack = halt '''
        if len(self.stack) == 0:
            sys.exit(0)
        self.pc = self.stack.pop()
    @opcode(19)
    def i_out(self, a: int) -> None:
        ''' print char w/ ascii code <a> to stdout '''
        sys.stdout.write(chr(self.eval_num(a)))
    @opcode(20)
    def i_in(self, a: int) -> None:
        ''' read a character from the terminal and write its ascii code to <a> '''
        if len(self.input_buffer) == 0:
            self.input_buffer = list(reversed(input('Input: ') + "\n"))
        self.r[self.eval_reg(a)] = ord(self.input_buffer.pop())
    @opcode(21)
    def i_noop(self) -> None:
        ''' do nothing '''
        pass


    def do_instruction(self) -> None:
        if self.pc == len(self.m):
            logging.info('EXECUTION REACHED END OF MEMORY')
            sys.exit(0)

        opcode = self.opcodes[self.m[self.pc]]
        args = self.m[self.pc + 1: self.pc + 1 + opcode.arity]
        self.pc += 1 + opcode.arity
        opcode(*args)

    def save_state(self, signum: int, frame: Any) -> None:
        timestamp = str(datetime.datetime.now())
        with open('saves/%s' % timestamp, 'w') as f:
            pickle.dump(self, f)
        logging.info("SAVED STATE. TIMESTAMP: %s" % timestamp)

    def run(self) -> None:
        while True:
            logging.debug("\nREGISTERS: %s" % ' '.join(str(i) for i in self.r))
            logging.debug("PC: %d" % self.pc)
            self.do_instruction()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        m = Machine()
        m.load_program()
    else:
        filename = sys.argv[1]
        with open(filename, 'rb') as f:
            m = pickle.load(f)

    # set up save handling
    signal.signal(signal.SIGUSR1, m.save_state)
    # start running
    m.run()
