        .globl  main
        .section .rodata
.LC0:
        .string "Hello, World!"
        .text
main:
        pushq   %rbp
        movq    %rsp, %rbp
        leaq    .LC0(%rip), %rdi
        call    puts@PLT
        movl    $0, %eax
        popq    %rbp
        ret
