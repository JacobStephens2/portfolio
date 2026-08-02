.global _start
.text
_start:
    xor %rbx, %rbx
    mov $1, %rcx
.Lloop:
    add %rcx, %rbx
    inc %rcx
    cmp $11, %rcx
    jne .Lloop

    lea buf(%rip), %rdi
    movb $'S', 0(%rdi)
    movb $'U', 1(%rdi)
    movb $'M', 2(%rdi)
    movb $'=', 3(%rdi)
    mov %rbx, %rax
    xor %rdx, %rdx
    mov $10, %rcx
    div %rcx
    add $'0', %al
    add $'0', %dl
    movb %al, 4(%rdi)
    movb %dl, 5(%rdi)
    movb $10, 6(%rdi)

    mov $1, %rax
    mov $1, %rdi
    lea buf(%rip), %rsi
    mov $7, %rdx
    syscall
    mov $60, %rax
    xor %rdi, %rdi
    syscall

.bss
    .align 8
buf:
    .space 8
