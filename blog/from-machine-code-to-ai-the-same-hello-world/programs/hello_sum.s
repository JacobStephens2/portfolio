# Period-flavored numerical job: sum integers 1..10, print SUM=55
# More like early stored-program work (tables, totals) than a greeting.
#
# Build: as -o hello_sum.o hello_sum.s && ld -o hello-sum hello_sum.o

.global _start
.text
_start:
    xor %rbx, %rbx            # sum = 0
    mov $1, %rcx              # i = 1
.Lloop:
    add %rcx, %rbx            # sum += i
    inc %rcx
    cmp $11, %rcx
    jne .Lloop                # while i < 11

    # rbx == 55; format "SUM=55\n" into buf
    lea buf(%rip), %rdi
    movb $'S', 0(%rdi)
    movb $'U', 1(%rdi)
    movb $'M', 2(%rdi)
    movb $'=', 3(%rdi)
    mov %rbx, %rax
    xor %rdx, %rdx
    mov $10, %rcx
    div %rcx                  # rax = 5, rdx = 5
    add $'0', %al
    add $'0', %dl
    movb %al, 4(%rdi)
    movb %dl, 5(%rdi)
    movb $10, 6(%rdi)         # newline

    mov $1, %rax              # sys_write
    mov $1, %rdi
    lea buf(%rip), %rsi
    mov $7, %rdx
    syscall
    mov $60, %rax             # sys_exit
    xor %rdi, %rdi
    syscall

.bss
    .align 8
buf:
    .space 8
