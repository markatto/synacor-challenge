.PHONY: all check clean build debug valgrind

CC = gcc
CFLAGS = -Wall -Wextra -Wpedantic -std=c99 -O3 -ffast-math -funroll-loops -march=native  # yes, I know this is stupid
CFLAGS_DEBUG = -Wall -Wextra -Wpedantic -std=c99 -g -fsanitize=address -fsanitize=undefined

all: check

# 2025 style checking
check: build
	@echo "Running static analysis with clang-tidy..."
	clang-tidy interpreter.c --checks='-*,bugprone-*,cert-*,clang-analyzer-*,hicpp-signed-bitwise,performance-*' --warnings-as-errors=''
	@echo "Running cppcheck..."
	cppcheck --enable=all --suppress=missingIncludeSystem interpreter.c
	@echo "All checks passed!"

# Build with strict warnings
build:
	@echo "Building with strict warnings..."
	$(CC) $(CFLAGS) -o interpreter interpreter.c

# Debug build with sanitizers
debug:
	@echo "Building debug version with sanitizers..."
	$(CC) $(CFLAGS_DEBUG) -o interpreter-debug interpreter.c

# Run valgrind for memory debugging
valgrind: debug
	@echo "Running valgrind with full checking..."
	valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all --track-origins=yes --verbose ./interpreter-debug

clean:
	rm -f interpreter interpreter-debug