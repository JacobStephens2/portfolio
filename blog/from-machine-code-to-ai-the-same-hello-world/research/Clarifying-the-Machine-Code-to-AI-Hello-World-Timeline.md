## The Arc the Page Describes

The stephens.page piece "From Machine Code to AI: the Same Hello World" is built around a single, deliberately simple test — printing a greeting or a small numeric result — carried across nine "bands" of programming history, each of which hides more implementation detail than the last. The bands progress from raw machine words physically entered into hardware (c. 1945), through hand-encoded machine code and mnemonic assembly (late 1940s), into early high-level languages like FORTRAN, Lisp, and COBOL (1957–1959), then systems languages (Pascal, C, C++), managed/safe languages (Java, C#, Go, Rust), scripting languages (Bash, Perl, Python, PHP, JavaScript), and finally AI-engineering and "vibe coding" era prompting (2022 and 2025). The page's own framing note is important: bands are ordered by abstraction level, not strict release-year chronology — Lisp actually predates C, and Java sits temporally between C and Go, but each is grouped with functionally similar peers rather than placed on a strict timeline.

The throughline is that every layer can "print Hello, World!" but the mechanism each layer conceals — wiring, opcodes, mnemonics, compilers, runtimes, interpreters, or a live LLM call — is the actual subject of the exhibit, with real (allowlisted) program execution on a Linux x86_64 host rather than simulated output.

## Why the Earliest Bands Don't Actually Print "Hello, World!"

This is the crux of what needs clarifying: the literal phrase "Hello, World!" is a mid-20th-century programming-culture artifact, not something the earliest machines were built to express, and the page is explicit about this distinction rather than glossing over it. "Hello, World!" as a cultural phrase and coding convention did not exist during the ENIAC/EDSAC era; it emerged only once symbolic, text-oriented languages made string literals and character output convenient, decades after absolute machine programming began.[^1]

For that reason, the page's earliest carousel band ("absolute machine program," c. 1945) offers two things side by side: a syscall-based Hello World for continuity with the rest of the ladder, and — more historically honest — a period-accurate numerical job that sums 1 through 10 and prints `SUM=55`, which is representative of what programmers of that era actually computed (ballistics tables, census tabulation, payroll, short arithmetic loops). This is a deliberate curatorial choice: rather than pretending 1940s machines were "printing greetings," the page shows what those machines were genuinely used for and only overlays a Hello World onto them as a structural convenience for the exhibit's ladder format.

## The Earliest Computing Methods, Clarified

| Band (per the page) | Approx. era | What it actually was | Real-world example |
|---|---|---|---|
| Absolute machine program | c. 1945 | Instruction and data words entered directly into hardware, often via plugboards/switches, no symbolic notation at all | ENIAC, programmed by physically rewiring plugboards and setting ~3,000 switches per problem; first run Dec 10, 1945, on a classified ballistics/physics calculation[^2][^3][^4] |
| Machine code | c. 1940s | Numeric instruction encodings entered via front-panel switches, hex/octal, or punched paper tape/cards, without wiring the whole machine per program | Early stored-program machines' front-panel opcode entry; punched-card tabulation lineage |
| Assembly | c. 1949 | Mnemonic symbols standing in for numeric opcodes, plus the first assemblers to translate them | EDSAC's "initial orders," a 31-word primitive relocating assembler running by May 1949 — widely regarded as the world's first assembler[^5][^6] |

ENIAC (completed and first run in 1945) is the clearest illustration of the "absolute machine program" band: it was not a stored-program computer at first, and its "programming" consisted of six women physically connecting patch cables and setting function-table switches, a process that could take days per problem. There was no notion of a text string, let alone "Hello, World," being printed — output was numerical results tabulated for physics and ballistics problems.[^2][^3][^4]

EDSAC, which ran its first programs on May 6, 1949, marks the transition the page calls "Assembly": Maurice Wilkes's team built the first stored-program computer to see regular use, and its "initial orders" constituted the first true assembler, letting programmers write in mnemonics rather than raw binary/octal words punched onto paper tape. Its first calculation, run by Beatrice Worsley, computed a table of squares — again, numeric output, not text greetings.[^5][^7][^6]

## So What Was the First Programming Method Actually Capable of Outputting "Hello, World"?

This is the specific point the page invites readers to interrogate, and the honest answer is layered:

- **Technically capable of printing an arbitrary text string:** Any stored-program computer with character/teletype output (EDSAC-class machines onward, late 1940s–1950s) was mechanically capable of printing the literal characters "Hello, World" if a programmer chose to encode that string — nothing about the hardware prevented it. But no one did, because the phrase and the convention did not exist yet.[^1][^5]
- **First language/context where "Hello, World"-style greeting code is actually documented:** The Jargon File and multiple independent histories trace the earliest documented "Hello, world"-type example to Martin Richards' BCPL language around 1967, predating Kernighan's later, better-known versions. Kernighan himself, in a recorded interview, confirmed that Richards had done something similar and diplomatically ceded that Kernighan may have popularized rather than originated the exact convention.[^8][^9][^1]
- **First surviving, precisely dated written code example:** Brian Kernighan's 1972 tutorial "A Tutorial Introduction to the Language B" contains the oldest surviving, well-documented "hello, world" program, using four `putchar` calls (because B's character constants were capped at 4 ASCII characters) to print `hello, world!`. This predates his and Dennis Ritchie's 1974 and 1978 C-language treatments, which are what actually popularized the convention industry-wide.[^10][^11][^1]
- **The version everyone associates with the phrase:** The 1978 book "The C Programming Language" by Kernighan and Ritchie is what cemented "hello, world" as the universal first-program convention for new languages, even though — as the page and multiple sources agree — the concept and even similar wording predate that book by roughly a decade.[^12][^11][^1]

So the layered answer to "what was the first programming method capable of outputting Hello World" is: mechanically, stored-program assembly-language machines of the late 1940s (EDSAC-class) already had the raw capability to print any character string, including that one, but the specific act of programming "Hello, World" as a convention did not occur until BCPL in the late 1960s, was first robustly documented in Kernighan's B tutorial (1972), and only became the standard idiom after the C book (1978). The page's own timeline — assembly c. 1949, early high-level languages 1957–1959 — sits entirely before this convention existed, which is exactly why it substitutes a period-accurate "SUM=55" arithmetic job for the earliest bands rather than misleadingly rendering a 1940s "Hello World" as if it were historically authentic.[^11][^5][^8][^1]

## Why the Distinction Matters for the Page's Argument

The page's larger thesis — credited partly to Robert C. Martin's framing in conversation with Kent Dodds — is that software history is a continuous climb of abstraction layers, each hiding more of the machine underneath, from wiring and switches to natural-language prompts sent to an LLM. Getting the "Hello World" origin story right actually strengthens that thesis: it shows the exhibit's designer was careful to separate two different things that are easy to conflate — the capability to output arbitrary text (present from the earliest stored-program/assembly machines onward) and the cultural convention of using "Hello, World" specifically as a first program (a much later, mid-1960s-to-1970s invention that only became universal after 1978). The carousel's ENIAC-era "sum 1..10" job is therefore not a compromise or filler — it is the more historically accurate artifact for that band, with the greeting-based Hello World bolted on afterward purely so the ladder format has a consistent thread running through all nine bands, including the AI-era ones that end the page.[^5][^11][^1]

---

## References

1. [Hello, world](https://en.wikipedia.org/wiki/Hello,_world) - The example program from the book prints "hello, world" , and was inherited from a 1974 Bell Laborat...

2. [eniac](https://en.wikipedia.org/wiki/ENIAC) - ENIAC (/ˈɛniæk/; Electronic Numerical Integrator and Computer) was the first programmable, electroni...

3. [The ENIAC Computer Runs Its First, Top-Secret Program](https://www.aps.org/apsnews/2022/11/eniac-first-top-secret-program) - December 1945: The ENIAC Computer Runs Its First, Top-Secret Program · Six young women programmed th...

4. [ENIAC Programmers](https://www.columbia.edu/cu/computinghistory/eniac.html) - When it first became operational in 1945, it was programmed entirely by women... "directly" by plugg...

5. [EDSAC](https://en.wikipedia.org/wiki/EDSAC) - Work on EDSAC started during 1947, and it ran its first programs on 6 May 1949, when it calculated a...

6. [1949: EDSAC computer employs delay-line storage](https://www.computerhistory.org/storageengine/edsac-computer-employs-delay-line-storage/) - In May 1949, Maurice Wilkes built EDSAC (Electronic Delay Storage Automatic Calculator), the first f...

7. [The EDSAC and Computing in Cambridge](https://www.whipplemuseum.cam.ac.uk/explore-whipple-collections/calculating-devices/edsac-and-computing-cambridge) - The first stored-program computer to go into regular use was Cambridge University's Electronic Delay...

8. [The Origins of "Hello, World"](https://www.youtube.com/watch?v=vLer3fRwwxE) - Have you ever written the words "Hello, World"? Did you ever wonder who said it first? And why? Bria...

9. [Why do we use Hello World? - the history behind it](https://dev.to/just5moreminutes/why-hello-world-5c0g) - The genius that brought Hello World! to the programming space appears to be the one and only Brian K...

10. [History of “Hello, World!” in Python: First Steps in Learning ...](https://python.plainenglish.io/history-of-hello-world-in-python-first-steps-in-learning-programming-d67a20da04c2) - “Hello, World!” was first coined by Brian Kernighan, In 1974, Kernighan created the B programming la...

11. [The History of 'Hello, World'](https://pages.hackerrank.com/blog/the-history-of-hello-world) - Brian Kernighan, author of one of the most widely read programming books, "C Programming Language", ...

12. [This month, “hello world” said “hello world!” The term was ...](https://www.facebook.com/MITCSAIL/posts/this-month-hello-world-said-hello-world-the-term-was-coined-in-a-seminal-program/1337625175066657/) - The term was coined in a seminal programming book published in 1978: “C Programming Language,” writt...

