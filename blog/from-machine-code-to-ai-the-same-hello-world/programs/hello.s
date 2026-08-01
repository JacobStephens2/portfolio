# Linux x86_64 AT: Hello World via libc puts.
# Built with: gcc -o hello hello.s
# (Server is amd64 Linux - not Apple Silicon ARM64.)

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
