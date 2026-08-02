# Minimal Linux x86_64 "absolute program": no libc, only syscalls.
# What you care about historically is these *instruction words* + the
# character bytes - not ELF headers / dynamic linker glue.
#
# Build: as -o hello_raw.o hello_raw.s && ld -o hello-raw hello_raw.o

.global _start
.text
_start:
    mov $1, %rax              # sys_write
    mov $1, %rdi              # fd = stdout
    lea msg(%rip), %rsi       # buffer
    mov $14, %rdx             # length
    syscall
    mov $60, %rax             # sys_exit
    xor %rdi, %rdi            # status 0
    syscall

.section .rodata
msg:
    .ascii "Hello, World!\n"
