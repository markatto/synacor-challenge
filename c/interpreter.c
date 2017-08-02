#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#define INT_SIZE              (1 << 15)      // 15-bit address space
#define MAX_INT               (INT_SIZE - 1) // largest possible int
#define REGISTER_COUNT        8              // number of registers
#define STACK_SIZE            512            // how large the stack can grow
#define BUFFER_SIZE           256            // size of the input buffer
#define DISTINCT_INSTRUCTIONS 22             // how many instructions there are

#define instruction(name) void i_## name (uint16_t *registers, uint16_t *memory, uint16_t *stack, size_t *stack_pos, size_t *pc)

char *filename = "../challenge.bin";  // TODO read from argv

void load_file(uint16_t *memory, const char *filename);
uint16_t eval_reg(uint16_t num);
uint16_t eval_num(uint16_t *registers, uint16_t num);

struct machine {
    uint16_t registers[REGISTER_COUNT];
    uint16_t memory[INT_SIZE];
    uint16_t stack[STACK_SIZE];
    uint16_t stack_pos;
    uint16_t pc;
};

// instruction forward declarations TODO move these to a .h file
instruction(halt);
instruction(set);
instruction(push);
instruction(pop);
instruction(eq);
instruction(gt);
instruction(jmp);
instruction(jt);
instruction(jf);
instruction(add);
instruction(mult);
instruction(mod);
instruction(and);
instruction(or);
instruction(not);
instruction(rmem);
instruction(wmem);
instruction(call);
instruction(ret);
instruction(out);
instruction(in);
instruction(noop);

// TODO: move this out of this file
// TODO: change it to use a "machine struct"

void (*instructions[DISTINCT_INSTRUCTIONS])(uint16_t *registers, uint16_t *memory, uint16_t *stack, size_t *stack_pos, size_t *pc) = {
    i_halt, // 0
    i_set,  // 1
    i_push, // 2
    i_pop,  // 3
    i_eq,   // 4
    i_gt,   // 5
    i_jmp,  // 6
    i_jt,   // 7
    i_jf,   // 8
    i_add,  // 9
    i_mult, // 10
    i_mod,  // 11
    i_and,  // 12
    i_or,   // 13
    i_not,  // 14
    i_rmem, // 15
    i_wmem, // 16
    i_call, // 17
    i_ret,  // 18
    i_out,  // 19
    i_in,   // 20
    i_noop, // 21
};

int main() {
    uint16_t memory[INT_SIZE]          = {0};
    uint16_t registers[REGISTER_COUNT] = {0};
    uint16_t stack[STACK_SIZE]         = {0};
    uint16_t input_buffer[BUFFER_SIZE] = {0};
    size_t stack_pos  = 0; // current stack size
    size_t buffer_pos = 0; // current input buffer size
    size_t pc         = 0; // program counter

    load_file(memory, filename);

    while (true) {
        instructions[memory[pc]](
            registers, memory, stack, &stack_pos, &pc
        );
    }
}

void load_file(uint16_t *memory, const char *filename) {
    uint64_t file_size;
    FILE * file;
    file = fopen(filename, "rb");
    if (!file) {
        printf("failed to open file: %s\n", filename);
        exit(1);
    }
    fseek(file, 0, SEEK_END);
    file_size = ftell(file);
    rewind(file);
    fread(memory, file_size, 1, file);
    fclose(file);
}

uint16_t eval_reg(uint16_t num) {
    assert(MAX_INT < num);
    assert(num <= (MAX_INT + REGISTER_COUNT));
    return num - INT_SIZE;
}

uint16_t eval_num(uint16_t *registers, uint16_t num) {
    assert(num <= (MAX_INT + REGISTER_COUNT));
    // numbers 0..32767 mean a literal value
    if (num <= MAX_INT) {
        return num;
    }
    return registers[eval_reg(num)];
}

instruction(halt) {
    *pc += 1;
    exit(0);
}
instruction(set) {
    *pc += 3;
    registers[eval_reg(memory[*pc - 2])] = eval_num(registers, memory[*pc - 1]);
}
instruction(push) {
    // TODO bounds checking
    *pc += 2;
    *stack_pos += 1;
    stack[*stack_pos] = eval_num(registers, memory[*pc - 1]);
}
instruction(pop) {
    // TODO bounds checking
    *pc += 2;
    registers[eval_reg(memory[*pc - 1])] = stack[*stack_pos];
    *stack_pos -= 1;
}
instruction(eq) {
    uint16_t reg_num, x, y;
    *pc += 4;
    reg_num = eval_reg(memory[*pc - 3]);
    x = eval_num(registers, memory[*pc - 2]);
    y = eval_num(registers, memory[*pc - 1]);
    registers[reg_num] = x == y;
}
instruction(gt) {
    uint16_t reg_num, x, y;
    *pc += 4;
    // TODO macro or function for this eval_num copypasta
    reg_num = eval_reg(memory[*pc - 3]);
    x = eval_num(registers, memory[*pc - 2]);
    y = eval_num(registers, memory[*pc - 1]);
    registers[reg_num] = x > y;
}
instruction(jmp) {
    *pc += 2;
    *pc = (size_t) eval_num(registers, memory[*pc - 1]);
}
instruction(jt) {
    *pc += 3;
    if (eval_num(registers, memory[*pc -2]) != 0) {
        *pc = (size_t) eval_num(registers, memory[*pc - 1]);
    }
}
instruction(jf) {
    *pc += 3;
    if (eval_num(registers, memory[*pc -2]) == 0) {
        *pc = (size_t) eval_num(registers, memory[*pc - 1]);
    }
}
instruction(add) {
    uint16_t reg_num, x, y;
    *pc += 4;
    // TODO macro or function for this eval_num copypasta
    reg_num = eval_reg(memory[*pc - 3]);
    x = eval_num(registers, memory[*pc - 2]);
    y = eval_num(registers, memory[*pc - 1]);

    registers[(size_t) reg_num] = (x + y) % INT_SIZE;
}
instruction(mult) {
    uint16_t reg_num, x, y;
    *pc += 4;
    // TODO macro or function for this eval_num copypasta
    reg_num = eval_reg(memory[*pc - 3]);
    x = eval_num(registers, memory[*pc - 2]);
    y = eval_num(registers, memory[*pc - 1]);

    registers[(size_t) reg_num] = (x * y) % INT_SIZE;
}
instruction(mod) {
    uint16_t reg_num, x, y;
    *pc += 4;
    // TODO macro or function for this eval_num copypasta
    reg_num = eval_reg(memory[*pc - 3]);
    x = eval_num(registers, memory[*pc - 2]);
    y = eval_num(registers, memory[*pc - 1]);

    registers[(size_t) reg_num] = (x % y) % INT_SIZE;
}
instruction(and) {
    // bitwise and
    uint16_t reg_num, x, y;
    *pc += 4;
    // TODO macro or function for this eval_num copypasta
    reg_num = eval_reg(memory[*pc - 3]);
    x = eval_num(registers, memory[*pc - 2]);
    y = eval_num(registers, memory[*pc - 1]);
    registers[reg_num] = (x & y) % INT_SIZE;
}
instruction(or) {
    // bitwise or
    uint16_t reg_num, x, y;
    *pc += 4;
    // TODO macro or function for this eval_num copypasta
    reg_num = eval_reg(memory[*pc - 3]);
    x = eval_num(registers, memory[*pc - 2]);
    y = eval_num(registers, memory[*pc - 1]);
    registers[reg_num] = (x | y) % INT_SIZE;
}
instruction(not) {
    // bitwise not
    uint16_t reg_num;
    *pc += 3;
    reg_num = eval_reg(memory[*pc - 2]);
    registers[reg_num] = ((uint16_t) (~eval_num(registers, memory[*pc - 1])) % INT_SIZE);
}
instruction(rmem) {
    // load memory into register
    uint16_t reg_num;
    *pc += 3;
    reg_num = eval_reg(memory[*pc - 2]);
    registers[reg_num] = memory[eval_num(registers, memory[*pc - 1])];
}
instruction(wmem) {
    // write memory from register
    uint16_t location;
    uint16_t value;
    *pc += 3;
    location = eval_num(registers, memory[*pc - 2]);
    value = eval_num(registers, memory[*pc - 1]);
    memory[location] = value;
}
instruction(call) {
    // TODO bounds checking
    *pc += 2;
    *stack_pos += 1;
    stack[*stack_pos] = *pc;
    *pc = eval_num(registers, memory[*pc - 1]);
}
instruction(ret) {
    *pc = stack[*stack_pos];
    *stack_pos -= 1;
}
instruction(out) {
    *pc += 2;
    printf("%c", (char) memory[*pc - 1]);
}
instruction(in) {
    printf("in unimplemented!");
}
instruction(noop) {
    *pc += 1;
}
