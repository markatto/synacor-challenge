#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#define INT_SIZE              (1U << 15U)     // 15-bit address space
#define MAX_INT               (INT_SIZE - 1) // largest possible int
#define REGISTER_COUNT        8              // number of registers
#define STACK_SIZE            1024            // how large the stack can grow
#define BUFFER_SIZE           256            // size of the input buffer
#define DISTINCT_INSTRUCTIONS 22             // how many instructions there are

const bool TRACE = false; // print debugging trace


struct Machine {
    uint16_t registers[REGISTER_COUNT];
    uint16_t memory[INT_SIZE];
    uint16_t stack[STACK_SIZE];
    size_t stack_pos;
    size_t pc;
};

static void load_file(uint16_t *memory, const char *filename);
static uint16_t eval_reg(uint16_t num);
static uint16_t eval_num(const uint16_t *registers, uint16_t num);
static uint16_t read_arg(struct Machine *m);

// instruction forward declarations
static void i_halt (struct Machine *m);
static void i_set (struct Machine *m);
static void i_push (struct Machine *m);
static void i_pop (struct Machine *m);
static void i_eq (struct Machine *m);
static void i_gt (struct Machine *m);
static void i_jmp (struct Machine *m);
static void i_jt (struct Machine *m);
static void i_jf (struct Machine *m);
static void i_add (struct Machine *m);
static void i_mult (struct Machine *m);
static void i_mod (struct Machine *m);
static void i_and (struct Machine *m);
static void i_or (struct Machine *m);
static void i_not (struct Machine *m);
static void i_rmem (struct Machine *m);
static void i_wmem (struct Machine *m);
static void i_call (struct Machine *m);
static void i_ret (struct Machine *m);
static void i_out (struct Machine *m);
static void i_in (struct Machine *m);
static void i_noop (struct Machine *m);

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

int main(int argc, char *argv[]) {
    const char *filename = (argc > 1) ? argv[1] : "../challenge.bin";
    struct Machine machine = {0};
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

static void load_file(uint16_t *memory, const char *filename) {
    FILE *file = fopen(filename, "rb");
    if (!file) {
        printf("i/o error on %s\n", filename);
        exit(1);
    }

    if (fseek(file, 0, SEEK_END) != 0) goto close_and_die;

    long file_size = ftell(file);
    if (file_size == -1) goto close_and_die;

    if (fseek(file, 0, SEEK_SET) != 0) goto close_and_die;

    size_t bytes_read = fread(memory, 1, (size_t)file_size, file);
    if (bytes_read != (size_t)file_size) goto close_and_die;

    (void)fclose(file);
    return;

close_and_die:
    printf("i/o error on %s\n", filename);
    (void)fclose(file);
    exit(1);
}

static uint16_t eval_reg(uint16_t num) {
    assert(num > MAX_INT);
    assert(num <= (MAX_INT + REGISTER_COUNT));
    return num - INT_SIZE;
}

static uint16_t eval_num(const uint16_t *registers, uint16_t num) {
    // TODO document this moar better
    assert(num <= (MAX_INT + REGISTER_COUNT));
    // numbers 0..32767 mean a literal value
    if (num <= MAX_INT) {
        return num;
    }
    return registers[eval_reg(num)];
}

static uint16_t read_arg(struct Machine *m) {
    // read an argument and advance PC past it
    uint16_t arg = m->memory[m->pc++];
    return arg;
}


static void i_halt (struct Machine *m __attribute__((__unused__))) {
    exit(0);
}
static void i_set (struct Machine *m) {
    size_t reg   = eval_reg(read_arg(m));
    size_t value = eval_num(m->registers, read_arg(m));
    m->registers[reg] = value;
}
static void i_push (struct Machine *m) {
    m->stack[++m->stack_pos] = eval_num(m->registers, read_arg(m));
}
static void i_pop (struct Machine *m) {
    m->registers[eval_reg(read_arg(m))] = m->stack[m->stack_pos--];
}
static void i_eq (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = x == y;
}
static void i_gt (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = x > y;
}
static void i_jmp (struct Machine *m) {
    m->pc = eval_num(m->registers, read_arg(m));
}
static void i_jt (struct Machine *m) {
    uint16_t condition = eval_num(m->registers, read_arg(m));
    uint16_t target    = eval_num(m->registers, read_arg(m));
    if (condition != 0)
        m->pc = target;
}
static void i_jf (struct Machine *m) {
    uint16_t condition = eval_num(m->registers, read_arg(m));
    uint16_t target    = eval_num(m->registers, read_arg(m));
    if (condition == 0)
        m->pc = target;
}
static void i_add (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = (x + y) % INT_SIZE;
}
static void i_mult (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = (x * y) % INT_SIZE;
}
static void i_mod (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = (x % y) % INT_SIZE;
}
static void i_and (struct Machine *m) {
    // bitwise and
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = (x & y) % INT_SIZE;
}
static void i_or (struct Machine *m) {
    // bitwise or
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t x = eval_num(m->registers, read_arg(m));
    uint16_t y = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = (x | y) % INT_SIZE;
}
static void i_not (struct Machine *m) {
    // bitwise not
    size_t reg_num = eval_reg(read_arg(m));
    uint16_t val = eval_num(m->registers, read_arg(m));
    // cast because int promotion
    m->registers[reg_num] = (uint16_t) ~val % INT_SIZE;
}
static void i_rmem (struct Machine *m) {
    // load memory into register
    size_t reg_num = eval_reg(read_arg(m));
    size_t mem_loc = eval_num(m->registers, read_arg(m));
    m->registers[reg_num] = m->memory[mem_loc];
}
static void i_wmem (struct Machine *m) {
    // write memory
    size_t mem_loc = eval_num(m->registers, read_arg(m));
    size_t value   = eval_num(m->registers, read_arg(m));
    m->memory[mem_loc] = value;
}
static void i_call (struct Machine *m) {
    size_t dest = eval_num(m->registers, read_arg(m));
    m->stack[++m->stack_pos] = m->pc;
    m->pc = dest;
}

static void i_ret (struct Machine *m) {
    m->pc = m->stack[m->stack_pos--];
}
static void i_out (struct Machine *m) {
    printf("%c", (char) eval_num(m->registers, read_arg(m)));
}
static void i_in (struct Machine *m) {
    size_t reg_num = eval_reg(read_arg(m));
    int c = getchar();
    if (c == EOF) c = 0;
    m->registers[reg_num] = (uint16_t)(unsigned char)c;
}
static void i_noop (struct Machine *m __attribute__((__unused__))) {
}
