#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#define INT_SIZE              (1 << 15)      // 15-bit address space
#define MAX_INT               (INT_SIZE - 1) // largest possible int
#define REGISTER_COUNT        8              // number of registers
#define STACK_SIZE            1024            // how large the stack can grow
#define BUFFER_SIZE           256            // size of the input buffer
#define DISTINCT_INSTRUCTIONS 22             // how many instructions there are

const bool TRACE = false; // print debugging trace

char *filename = "../challenge.bin";  // TODO read from argv

struct Machine {
    uint16_t registers[REGISTER_COUNT];
    uint16_t memory[INT_SIZE];
    uint16_t stack[STACK_SIZE];
    uint16_t input_buffer[BUFFER_SIZE];
    size_t buffer_pos;
    size_t stack_pos;
    size_t pc;
};

void load_file(uint16_t *memory, const char *filename);
uint16_t eval_reg(uint16_t num);
uint16_t eval_num(uint16_t *registers, uint16_t num);
uint16_t read_arg(struct Machine *m);

// instruction forward declarations
void i_halt (struct Machine *m);
void i_set (struct Machine *m);
void i_push (struct Machine *m);
void i_pop (struct Machine *m);
void i_eq (struct Machine *m);
void i_gt (struct Machine *m);
void i_jmp (struct Machine *m);
void i_jt (struct Machine *m);
void i_jf (struct Machine *m);
void i_add (struct Machine *m);
void i_mult (struct Machine *m);
void i_mod (struct Machine *m);
void i_and (struct Machine *m);
void i_or (struct Machine *m);
void i_not (struct Machine *m);
void i_rmem (struct Machine *m);
void i_wmem (struct Machine *m);
void i_call (struct Machine *m);
void i_ret (struct Machine *m);
void i_out (struct Machine *m);
void i_in (struct Machine *m);
void i_noop (struct Machine *m);

// TODO: move this out of this file
// TODO: change it to use a "machine struct"

void (*instructions[DISTINCT_INSTRUCTIONS])(struct Machine *m) = {
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
    struct Machine machine = {{0},{0},{0},{0},0,0,0};
    load_file(machine.memory, filename);
    while (true) {
        if (TRACE) {
            printf("\nREGISTERS:");
            for (int i=0; i<8; i++) {
                printf(" %d", machine.registers[i]);
            }
            printf("\nPC: %zu\n", machine.pc);
        }
        instructions[machine.memory[machine.pc++]](&machine);
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
    assert(num > MAX_INT);
    assert(num <= (MAX_INT + REGISTER_COUNT));
    return num - INT_SIZE;
}

uint16_t eval_num(uint16_t *registers, uint16_t num) {
    // TODO document this moar better
    assert(num <= (MAX_INT + REGISTER_COUNT));
    // numbers 0..32767 mean a literal value
    if (num <= MAX_INT) {
        return num;
    }
    return registers[eval_reg(num)];
}

uint16_t read_arg(struct Machine *m) {
    // read an argument and advance PC past it
    uint16_t arg = m->memory[m->pc++];
    return arg;
}


void i_halt (struct Machine *m __attribute__((__unused__))) {
    exit(0);
}
void i_set (struct Machine *m) {
    size_t reg   = eval_reg(read_arg(m));
    size_t value = eval_num(m->registers, read_arg(m));
    m->registers[reg] = value;
}
void i_push (struct Machine *m) {
    m->stack[++m->stack_pos] = eval_num(m->registers, read_arg(m));
}
void i_pop (struct Machine *m) {
    m->registers[eval_reg(read_arg(m))] = m->stack[m->stack_pos--];
}
void i_eq (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = x == y;
}
void i_gt (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = x > y;
}
void i_jmp (struct Machine *m) {
    m->pc = eval_num(m->registers, read_arg(m));
}
void i_jt (struct Machine *m) {
    uint16_t condition = eval_num(m->registers, read_arg(m));
    uint16_t target    = eval_num(m->registers, read_arg(m));
    if (condition != 0)
        m->pc = target;
}
void i_jf (struct Machine *m) {
    uint16_t condition = eval_num(m->registers, read_arg(m));
    uint16_t target    = eval_num(m->registers, read_arg(m));
    if (condition == 0)
        m->pc = target;
}
void i_add (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = (x + y) % INT_SIZE;
}
void i_mult (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = (x * y) % INT_SIZE;
}
void i_mod (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = (x % y) % INT_SIZE;
}
void i_and (struct Machine *m) {
    // bitwise and
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = (x & y) % INT_SIZE;
}
void i_or (struct Machine *m) {
    // bitwise or
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = (x | y) % INT_SIZE;
}
void i_not (struct Machine *m) {
    // bitwise not
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t val = eval_num(m->registers, read_arg(m));
    // cast because int promotion
    m->registers[reg_num] = (uint16_t) ~val % INT_SIZE;
}
void i_rmem (struct Machine *m) {
    // load memory into register
    size_t reg_num = eval_reg(read_arg(m));
    size_t mem_loc = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = m->memory[mem_loc];
}
void i_wmem (struct Machine *m) {
    // write memory
    size_t mem_loc = eval_num(m->registers, read_arg(m));
    size_t value   = eval_num(m->registers, read_arg(m));
    m->memory[mem_loc] = value;
}
void i_call (struct Machine *m) {
    size_t dest = eval_num(m->registers, read_arg(m));
    m->stack[++m->stack_pos] = m->pc;
    m->pc = dest;
}

void i_ret (struct Machine *m) {
    m->pc = m->stack[m->stack_pos--];
}
void i_out (struct Machine *m) {
    printf("%c", (char) eval_num(m->registers, read_arg(m)));
}
void i_in (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    char c;
    scanf("%c", &c);
    m->registers[reg_num] = c;
}
void i_noop (struct Machine *m __attribute__((__unused__))) {
}
