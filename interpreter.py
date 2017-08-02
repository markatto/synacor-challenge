#! /usr/bin/env python
import array
import sys
import signal
import inspect
import pickle
from datetime import datetime

# VM implementing the architecture defined in the file "arch-spec"
# arch-spec comes from https://challenge.synacor.com/

INT_SIZE = 2 ** 15
MAX_INT = INT_SIZE - 1
REGISTER_COUNT = 8
class Machine(object):
    def __init__(self):
        # 15-bit address space
        self.memory = [0] * INT_SIZE
        self.m = self.memory # short alias
        self.registers = [0] * REGISTER_COUNT
        self.r = self.registers # alias
        self.stack = []
        # program counter / instruction pointer
        self.pc = 0
        self.input_buffer = []

    def load_program(self, filename='challenge.bin'):
        ''' load the contents of a file into the start of memory '''
        with open(filename, 'rb') as f:
            data = f.read()
        data = array.array('H', data)

        #insert at the beginning of memory
        self.memory[:len(data)] = data

    @staticmethod
    def eval_reg(x):
        ''' turn a "direct format number" into a register '''
        assert MAX_INT < x <= MAX_INT + REGISTER_COUNT
        return x - INT_SIZE

    def eval_num(self, x):
        assert x <= MAX_INT + REGISTER_COUNT
        #numbers 0..32767 mean a literal value
        if x <= MAX_INT:
            return x
        return self.registers[self.eval_reg(x)]


    def i_halt(self):
        ''' halt '''
        sys.exit(0)
    def i_set(self, a, b):
        ''' set register a to value of <b> '''
        self.registers[self.eval_reg(a)] = self.eval_num(b)
    def i_push(self, a):
        ''' push register a onto the stack '''
        self.stack.append(self.registers[self.eval_reg(a)])
    def i_pop(self, a):
        ''' pop stack into register a '''
        self.r[self.eval_reg(a)] = self.stack.pop()
    def i_eq(self, a, b, c):
        ''' <a> = 1 if b == c else 0 '''
        self.r[self.eval_reg(a)] = int(self.eval_num(b) == self.eval_num(c))
    def i_gt(self, a, b, c):
        ''' register a is 1 if b > c '''
        self.r[self.eval_reg(a)] = int(self.eval_num(b) > self.eval_num(c))
    def i_jmp(self, a):
        ''' jump to <a> '''
        self.pc = self.eval_num(a)
    def i_jt(self, a, b):
        ''' jump to location <b> if <a> is true (nonzero)'''
        if self.eval_num(a) != 0:
            self.pc = self.eval_num(b)
    def i_jf(self, a, b):
        ''' jump to location <b> if <a> is false (0)'''
        if self.eval_num(a) == 0:
            self.pc = self.eval_num(b)
    def i_add(self, a, b, c):
        ''' <a> = <b> + <c> '''
        self.r[self.eval_reg(a)] = (self.eval_num(b) + self.eval_num(c)) % INT_SIZE
    def i_mult(self, a, b, c):
        ''' <a> = <b> * <c> '''
        self.r[self.eval_reg(a)] = (self.eval_num(b) * self.eval_num(c)) % INT_SIZE
    def i_mod(self, a, b, c):
        ''' <a> = <b> % <c> '''
        self.r[self.eval_reg(a)] = (self.eval_num(b) % self.eval_num(c)) % INT_SIZE
    def i_and(self, a, b, c):
        ''' <a> = <b> & <c> '''
        self.r[self.eval_reg(a)] = (self.eval_num(b) & self.eval_num(c)) % INT_SIZE
    def i_or(self, a, b, c):
        ''' <a> = <b> | <c> '''
        self.r[self.eval_reg(a)] = (self.eval_num(b) | self.eval_num(c)) % INT_SIZE
    def i_not(self, a, b):
        ''' <a> = ~<b> '''
        self.r[self.eval_reg(a)] = (~self.eval_num(b)) % INT_SIZE
    def i_rmem(self, a, b):
        ''' read memory at address <b> and write it to <a> '''
        self.r[self.eval_reg(a)] = self.memory[self.eval_num(b)]
    def i_wmem(self, a, b):
        ''' write the value from <b> into memory at address <a>'''
        self.memory[self.eval_num(a)] = self.eval_num(b)
    def i_call(self, a):
        ''' write the address of the next instruction to the stack and jump to <a> '''
        self.stack.append(self.pc)
        self.pc = self.eval_num(a)
    def i_ret(self):
        ''' remove the top element from the stack and jump to it; empty stack = halt '''
        if len(self.stack) == 0:
            sys.exit(0)
        self.pc = self.stack.pop()
    def i_out(self, a):
        ''' print char w/ ascii code <a> to stdout '''
        sys.stdout.write(unichr(self.eval_num(a)))
    def i_in(self, a):
        ''' read a character from the terminal and write its ascii code to <a> '''
        if len(self.input_buffer) == 0:
            self.input_buffer = list(reversed(raw_input('Input: ') + "\n"))
        self.r[self.eval_reg(a)] = ord(self.input_buffer.pop())
    def i_noop(self):
        ''' do nothing '''
        pass

    # lookup table for opcodes
    opcodes = [
            i_halt, #0
            i_set,  #1
            i_push, #2
            i_pop,  #3
            i_eq,   #4
            i_gt,   #5
            i_jmp,  #6
            i_jt,   #7
            i_jf,   #8
            i_add,  #9
            i_mult, #10
            i_mod,  #11
            i_and,  #12
            i_or,   #13
            i_not,  #14
            i_rmem, #15
            i_wmem, #16
            i_call, #17
            i_ret,  #18
            i_out,  #19
            i_in,   #20
            i_noop, #21
    ]

    def do_instruction(self):
        if self.pc == len(self.memory):
            print('EXECUTION REACHED END OF MEMORY')
            sys.exit(0)

        instruction = self.opcodes[self.memory[self.pc]]
        instruction_size = len(inspect.getargspec(instruction).args)
        args = self.memory[self.pc + 1: self.pc + instruction_size]
        self.pc += instruction_size
        instruction(self, *args)

    def save_state(self, signum, frame):
        timestamp = str(datetime.datetime.now())
        with open('saves/%s' % timestamp, 'w') as f:
            pickle.dump(self, f)
        print("SAVED STATE. TIMESTAMP: %s" % timestamp)

    def run(self):
        # set up save handling
        signal.signal(signal.SIGUSR1, self.save_state)
        while True:
            self.do_instruction()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        m = Machine()
        m.load_program()
    else:
        filename = sys.argv[1]
        with open(filename) as f:
            m = pickle.load(f)

    print(m.pc)
    m.run()
