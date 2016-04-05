#! /usr/bin/env python
import sys
import datetime
import signal
import inspect
import struct
import collections
import pickle

# VM implementing the architecture defined in the file "arch-spec"
# arch-spec comes from https://challenge.synacor.com/

#TODO: break out parsing code into a full assembler/disassembler

#TODO: bitwise operators probably need more logic; python treats ints as
# infinitely-long 2's complement signed-values, but we want unsigned

INT_SIZE = 32768 # 2**15
MAX_INT = INT_SIZE - 1
REGISTER_COUNT = 8
class Machine(object):
    def __init__(self):
        # 15-bit address space
        self.memory = [0] * INT_SIZE
        self.m = self.memory # short alias
        # 8 registers
        self.registers = [0] * REGISTER_COUNT
        self.r = self.registers # alias
        # can grow/shrink
        # our imaginary computer has infinite magical stack space
        self.stack = []
        # program counter / instruction pointer
        self.pc = 0
        # REMEMBER: ints wrap at 2**15 ; everything is % 32768

        # this is really only a deque because it's more convenient
        # to debug when strings aren't backwards in memory
        self.input_buffer = collections.deque()

    def load_program(self, filename='challenge.bin'):
        ''' load the contents of a file into the start of memory '''

        # Sadly the array.array binary loading silently uses unsigned
        # longs even when you ask for unsigned shorts.
        # Therefore, we hack together a super-long format string
        # for the struct loader.
        with open(filename, 'rb') as f:
            data = f.read()
        data = struct.unpack('<' + 'H' * (len(data) / 2), data)

        #insert at the beginning of memory
        self.memory[:len(data)] = data


    def eval_num(self, x):
        #numbers 0..32767 mean a literal value
        if x <= MAX_INT:
            return x
        # numbers 32768..32775 instead mean registers 0..7
        if x <= MAX_INT + REGISTER_COUNT:
            register = x - INT_SIZE
            return self.registers[register]
        assert False # illegal

    @staticmethod
    def eval_reg(x):
        ''' turn a "direct format number" into a register '''
        if MAX_INT < x <= MAX_INT + REGISTER_COUNT:
            return x - INT_SIZE
        else:
            assert False

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
        self.r[self.eval_reg(a)] = 1 if self.eval_num(b) == self.eval_num(c) else 0
    def i_gt(self, a, b, c):
        ''' register a is 1 if b > c '''
        self.r[self.eval_reg(a)] = 1 if self.eval_num(b) > self.eval_num(c) else 0
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
        #print("STDOUT: %s" % unichr(self.eval_num(a)))
        #TODO: turn this on in the end
        sys.stdout.write(unichr(self.eval_num(a)))
    def i_in(self, a):
        ''' read a character from the terminal and write its ascii code to <a> '''
        if len(self.input_buffer) == 0:
            self.input_buffer.extend(raw_input('Input: ') + "\n")
        self.r[self.eval_reg(a)] = ord(self.input_buffer.popleft())
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
        # this is why python is cool
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
    m.run()
