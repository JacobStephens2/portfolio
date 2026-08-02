# Programming Eras Narrative Research

Research notes for the blog post at [stephens.page/blog/from-machine-code-to-ai-the-same-hello-world](https://stephens.page/blog/from-machine-code-to-ai-the-same-hello-world/). Not final blog prose — historical substance, suggested openings, transitions, and citable details for writing the narrative faithfully.

---

## Framing throughline

Every major level of programming is a response to the pain of the level beneath it. Plugboards made stored programs necessary; numeric codes made mnemonics necessary; hand assembly made formula translation necessary; Fortran-era languages made systems languages necessary; unchecked memory made managed runtimes and ownership types necessary; ceremony made scripting necessary; and writing every line by hand made model interfaces necessary. Abstractions accumulate rather than replace — ELF still packages machine words; C still underpins kernels; prompts still compile down (through tool calls and generated code) to the same silicon. “Hello world” is a moving target: a 1945 machine could not print a greeting to a teletype in the modern idiom, so period-honest first programs are sums, squares, primes, and trajectory tables — until Kernighan’s 1970s Bell Labs tutorials freeze the greeting as the canonical first program, and until 2022 when the greeting can be a contract with a model rather than a sequence of instructions.

---

## 1. Absolute machine program (c. 1945)

**Suggested opening line:** Before there was source code, there was a room full of cables, switches, and six mathematicians who had to become the program.

### Origin story

The Electronic Numerical Integrator and Computer (ENIAC) was financed by the U.S. Army, designed by physicist John Mauchly and engineer J. Presper Eckert at the University of Pennsylvania’s Moore School of Electrical Engineering, and first put to work on **December 10, 1945** on a classified math problem from Los Alamos — likely hydrogen-bomb ignition calculations that remain classified ([APS News](https://www.aps.org/apsnews/2022/11/eniac-first-top-secret-program); [Army Ordnance / Weik, “The ENIAC Story”](https://ftp.arl.army.mil/~mike/comphist/eniac-story.html)). Public unveiling came on **February 14–15, 1946** at the Moore School, with a ballistic-trajectory demonstration that ran in about two hours and was claimed to equal a year of work by a hundred trained human computers ([Penn Today](https://penntoday.upenn.edu/news/worlds-first-general-purpose-computer-turns-75); [APS News](https://www.aps.org/apsnews/2022/11/eniac-first-top-secret-program)).

The six original programmers — hired first as human “computers” for Ballistic Research Laboratory trajectory tables — were **Kathleen “Kay” McNulty** (later Mauchly Antonelli), **Jean Jennings** (Bartik), **Betty Snyder** (Frances Elizabeth Holberton), **Marlyn Wescoff** (Meltzer), **Fran Bilas** (Spence), and **Ruth Lichterman** (Teitelbaum) ([IEEE Computer Society — Women of ENIAC](https://www.computer.org/volunteering/awards/pioneer/about-women-of-eniac); [Computer History Museum](https://www.computerhistory.org/revolution/birth-of-the-computer/4/78)). Herman H. Goldstine, an Ordnance Department mathematician assigned to the Ballistics Research Laboratory, was a key Army liaison and later co-author of the stored-program vision ([Army Ordnance history](https://ftp.arl.army.mil/~mike/comphist/eniac-story.html)).

### Pain of the prior level

Before ENIAC, a single ballistic trajectory took roughly **forty hours by hand**; differential analyzers (wheel-and-disc integrators at Moore School) could integrate but were nightmarishly hard to reconfigure — “you program it once… if the wheels slip then you’ve got big problems” ([Penn Today](https://penntoday.upenn.edu/news/worlds-first-general-purpose-computer-turns-75)). War demand for firing tables outstripped human and mechanical capacity.

### What programming looked like

ENIAC was **not** a stored-program machine in 1945. It had no internal program store in the modern sense. Programming meant physically reconfiguring the machine: routing cables on plugboards, setting ~**6,000 switches**, and coordinating **~18,000 vacuum tubes** across **40 nine-foot panels** around three walls of a room ([APS News](https://www.aps.org/apsnews/2022/11/eniac-first-top-secret-program); [Computer History Museum](https://www.computerhistory.org/revolution/birth-of-the-computer/4/78)). The women initially lacked clearance to see the machine and learned it from “tangled diagrams,” then invented practical techniques — subroutines, nesting, breakpoints (Holberton) — that would later be recognized as foundational ([IEEE Computer Society](https://www.computer.org/volunteering/awards/pioneer/about-women-of-eniac)). Contemporary press photos often showed male operators; the programmers’ role was omitted from early accounts ([IEEE Computer Society](https://www.computer.org/volunteering/awards/pioneer/about-women-of-eniac)).

### Period-honest “hello world”

There is no teletype “hello world.” Period-honest first jobs:

- **Problem A — 12/10/45**: classified Los Alamos calculation; log note after test: “Machine tested—OK.” ([APS News](https://www.aps.org/apsnews/2022/11/eniac-first-top-secret-program))
- **Ballistic trajectory tables**: the public demo job — numerical integration of shell paths under air density, temperature, wind ([Penn Today](https://penntoday.upenn.edu/news/worlds-first-general-purpose-computer-turns-75))
- **Carousel guidance for the blog**: a **sum 1..n** style numeric job for period honesty; a modern **ELF packaging note** for ladder continuity (how raw machine words would be represented as a Linux binary today); optional “hello via syscalls” only as a modern mapping, clearly labeled anachronistic

### Pivotal artifact / transition moment

While ENIAC was still being finished, the next architecture was already being designed. In **June 1945**, John von Neumann’s **“First Draft of a Report on the EDVAC”** (Electronic Discrete Variable Automatic Computer) circulated the stored-program concept: instructions and data as words in a common memory, so the machine need not be rewired per problem ([MIT copy of the First Draft](https://fab.cba.mit.edu/classes/862.16/notes/computation/vonNeumann-1945.pdf); [History of Information](https://www.historyofinformation.com/detail.php?id=644); [Computer History Museum — The Stored Program](https://www.computerhistory.org/revolution/birth-of-the-computer/4/87)). Credit is historically contested — Mauchly, Eckert, Goldstine, and others contributed ideas — but the First Draft became the canonical description of the architecture almost every later machine followed.

### Alan Turing and the ACE (first “recognizable code,” per Uncle Bob)

Robert C. Martin’s 2016 talk *The Future of Programming* frames **Alan Turing** as probably the first person to write code a modern programmer would still recognize, and says of the ACE work: “You would recognise the code that Alan Turing wrote on the ACE machine. You would not like it, but you would recognise it.” ([talk](https://www.youtube.com/watch?v=ecIWPzGEbFc); talk notes summarizing the quote: [Loenko](https://dive.medium.com/about-bob-martins-talk-the-future-of-programming-2016-f9408ee2e8ae)).

Archival anchor: Turing’s **ACE report** — *Proposed Electronic Calculator* — written late **1945** at the National Physical Laboratory and presented **1946** (often cited as the 1946 ACE report). It is a reasonably complete stored-program design with circuit diagrams, **subroutine** call/return (named sequences such as BURY/UNBURY), floating-point ideas, **Abbreviated Computer Instructions**, and sample program sequences ([Wikipedia — ACE](https://en.wikipedia.org/wiki/Automatic_Computing_Engine); [MIT Press collection](https://mitpress.mit.edu/9780262031141/a-m-turings-ace-report-of-1946-and-other-papers/); Rutherford Journal overview of ACE programming work: [Carpenter & Doran lineage / Copeland](https://www.rutherfordjournal.org/article040101.html)). While hardware lagged, Turing’s group wrote a library of mathematical programs for the unbuilt machine. A cut-down **Pilot ACE** ran its first program on **10 May 1950** (often the “Suc Digs” successive-digits test).

Priority among ENIAC, EDVAC, Baby, EDSAC, and ACE is historically contested; for this post the load-bearing claim is narrower: by mid-1940s the *form* of the artifact is already instruction/data words and subroutines, not only plugboards.

### Vivid citable details

1. **Physical scale**: 30 tons, ~80 feet of panels, 18,000 tubes — Betty Snyder Holberton later: “it was just a monstrous thing” ([APS News](https://www.aps.org/apsnews/2022/11/eniac-first-top-secret-program)).
2. **Human computers first**: the six were paid ~$1,620/year as mathematical computers before becoming the machine’s programmers; nearly a hundred women had been hired at Moore School for BRL work ([APS News](https://www.aps.org/apsnews/2022/11/eniac-first-top-secret-program)).
3. **Debugging as hardware**: Holberton invented **breakpoints**; Jean Bartik later led conversion of ENIAC toward stored-program operation ([IEEE Computer Society](https://www.computer.org/volunteering/awards/pioneer/about-women-of-eniac)).

**Suggested transition:** Rewiring a thirty-ton machine for every new problem could not scale. The next move was to stop changing the wires and start changing the **numbers** in memory.

---

## 2. Machine code (c. late 1940s)

**Suggested opening line:** The breakthrough was not a faster tube — it was the idea that the program itself could be data.

### Origin story

The first machine to execute a program stored in electronic memory was the **Manchester Small-Scale Experimental Machine (SSEM)**, nicknamed **“Baby,”** at the University of Manchester on **21 June 1948**. Designed by **F.C. (Freddie) Williams** and **Tom Kilburn** (with Geoff Tootill) to prove the Williams-Kilburn CRT store, it ran Kilburn’s first successful program that day — and as Manchester’s own history puts it, “nothing was ever the same again” ([University of Manchester / computer50](https://curation.cs.manchester.ac.uk/computer50/www.computer50.org/mark1/new.baby.html); [ETHW milestone](https://ethw.org/Milestones:Manchester_University_%22Baby%22_Computer_and_its_Derivatives,_1948-1951)). Baby led to the Manchester Mark 1 and the commercial **Ferranti Mark 1**.

In the U.S., commercial machine-code culture crystallized around machines like the **IBM 650** Magnetic Drum Data Processing Machine — announced **14 July 1953**, first delivery **December 1954** (John Hancock Mutual Life), the first mass-produced computer and IBM’s first significant computer profit center ([IBM Archives — 650](https://www.ibm.com/history/650)). Programs and data lived as numeric words on a spinning magnetic drum (~12,500 rpm); operators entered and bulk-loaded work via **punched cards**.

### Pain of the prior level

ENIAC-style plugboard programming meant hours or days of physical setup per problem, high risk of cable errors, and zero portability of a “program” between machines or even between runs after the board was cleared. Stored-program architecture fixed the wiring and made the variable thing a sequence of **instruction words**.

### What programming looked like

- **Front-panel / CRT store entry**: Baby had a tiny store (initially **32 words** of 32 bits on a Williams tube); programs were entered as binary patterns — toggled and verified bit by bit ([Manchester computer50](https://curation.cs.manchester.ac.uk/computer50/www.computer50.org/mark1/new.baby.html)).
- **Paper tape**: EDSAC (next section) read five-track paper tape of numeric/symbol codes.
- **Punched cards**: The dominant bulk medium. IBM’s **80-column, 12-row** card (descended from Hollerith census equipment; CTR → IBM 1924) became the universal teaching and production format; by 1937 IBM’s Endicott presses produced **5–10 million cards per day**; the cultural injunction was “Do not fold, spindle or mutilate” ([Wikipedia — Punched card](https://en.wikipedia.org/wiki/Punched_card), used here as index to well-documented industrial facts). Cards held both program and data as decimal/character encodings of machine instructions.
- **Hand assembly**: Programmers wrote absolute or relative addresses on coding sheets, converted mnemonics by hand into octal/hex/decimal opcodes, and punched the result — every branch target recalculated when instructions shifted.

### Period-honest “hello world”

Baby’s first program was **not** a greeting. Kilburn’s program found the **highest proper factor** of a number (a carefully chosen exercise for a machine with almost no memory) ([Manchester computer50](https://curation.cs.manchester.ac.uk/computer50/www.computer50.org/mark1/new.baby.html)). Period-honest carousel peers: **hand-entered hex** of a small arithmetic loop; an **80-column teaching sheet** (sim, not a live reader) showing a punched representation of the same job.

### Pivotal artifact

The **Williams-Kilburn tube** as working random-access store, plus Baby’s 21 June 1948 run — the moment “stored program” left the EDVAC draft and became a blinking CRT full of bits ([Computer History Museum — The Stored Program](https://www.computerhistory.org/revolution/birth-of-the-computer/4/87)).

### Vivid citable details

1. **32 words**: the entire universe of the first stored program fit in a memory smaller than a modern tweet’s UTF-8 encoding ([Manchester computer50](https://curation.cs.manchester.ac.uk/computer50/www.computer50.org/mark1/new.baby.html)).
2. **Drum latency programming**: on the IBM 650, clever programmers ordered instructions around the drum’s rotation so the next instruction was under the head when needed — optimization as physical geometry ([IBM 650](https://www.ibm.com/history/650)).
3. **Cards as source of truth**: dropping a deck, or shuffling one card, was a production outage; the 80-column line length still haunts terminal defaults decades later ([Punched card history](https://en.wikipedia.org/wiki/Punched_card)).

**Suggested transition:** Remembering that opcode `5` means “subtract” and that the branch target is address `047` is work a machine could do. The next abstraction was to let the machine translate **names** into those numbers.

---

## 3. Assembly (c. 1949)

**Suggested opening line:** Cambridge did not invent the stored program — but it invented programming as a craft you could teach from a book.

### Origin story

**EDSAC** (Electronic Delay Storage Automatic Calculator), designed under **Maurice Wilkes** at the University of Cambridge Mathematical Laboratory, ran its first program on **6 May 1949** — printing a table of **squares** — and is widely regarded as the first practical stored-program computer to offer a regular computing service ([Cambridge CL — Edsac](https://www.cl.cam.ac.uk/~mr10/Edsac.html); [Cambridge chronology](https://www.cl.cam.ac.uk/relics/chron.html); [History of Information](https://www.historyofinformation.com/detail.php?id=679)). Input was **five-track paper tape**; a set of **“initial orders”** (a primitive loader/assembler resident in memory) translated symbolic instruction codes on the tape into binary machine words ([Cambridge Edsac poster / initial orders](https://www.cl.cam.ac.uk/~mr10/Edsac/edsacposter.pdf)).

In **1951**, Wilkes, **David Wheeler**, and **Stanley Gill** published ***The Preparation of Programs for an Electronic Digital Computer*** (Addison-Wesley) — widely cited as the first true programming textbook, including subroutine libraries and the calling convention that made reuse practical ([History of Information](https://www.historyofinformation.com/detail.php?id=66); [CACM — In Praise of Wilkes, Wheeler, and Gill](https://cacm.acm.org/opinion/in-praise-of-wilkes-wheeler-and-gill/); [Internet Archive edition](https://archive.org/details/programsforelect00wilk)).

**Parallel threads:**
- **Kathleen Booth** (Birkbeck College, London), working with Andrew Booth on ARC/ARC2 (late 1940s), wrote what is often cited as the first assembly-language style programming documentation — contracting machine operations to mnemonics for their relay/electronic machines ([Hackaday on Kathleen Booth](https://hackaday.com/2018/08/21/kathleen-booth-assembling-early-computers-while-inventing-assembly/); [Wikipedia — Kathleen Booth](https://en.wikipedia.org/wiki/Kathleen_Booth)).
- **Nathaniel Rochester** at IBM designed the **IBM 701**’s assembly-level tools and was among the first to build systematic symbolic assembly for a production scientific machine ([Computer History Museum TDIH](https://www.computerhistory.org/tdih/january/14/); [Computer Pioneers — Rochester](https://history.computer.org/pioneers/rochester.html)).

### Pain of the prior level

Pure numeric coding was slow and brittle: one wrong digit in an address, and the program silently destroyed itself. Inserting an instruction forced renumbering of every absolute jump. There was no modular reuse — every project reinvented division, square root, input formatting.

### Period-honest “hello world”

EDSAC’s first users printed **tables of squares** and **prime numbers**, not greetings ([Cambridge CL](https://www.cl.cam.ac.uk/~mr10/Edsac.html)). Glass in the modern Cambridge Computer Lab still engraves five-track tape of the **initial orders** and a program for squares and differences of 1..100 ([Cambridge CL](https://www.cl.cam.ac.uk/~mr10/Edsac.html)).

### Pivotal artifact

1. **Initial orders** — the loader that made symbolic tape a workable input path.
2. **The Wheeler jump** — David Wheeler’s subroutine calling technique: plant the return address in memory so control can return after a closed subroutine, enabling libraries ([Wikipedia — Wheeler Jump](https://en.wikipedia.org/wiki/Wheeler_Jump); [Clemson — subroutine history](https://people.computing.clemson.edu/~mark/subroutines.html)).
3. **Wilkes/Wheeler/Gill 1951** — programming as publishable engineering method.

### Vivid citable details

1. **May 6, 1949, squares** — the first “application software” moment for a service machine ([Cambridge CL](https://www.cl.cam.ac.uk/~mr10/Edsac.html)).
2. **Subroutine library as social technology**: the 1951 book distributed not just ideas but a culture of reusable closed subroutines ([CACM](https://cacm.acm.org/opinion/in-praise-of-wilkes-wheeler-and-gill/)).
3. **Booth’s assembly pamphlets** as a reminder that mnemonic programming emerged in more than one lab at once ([Hackaday](https://hackaday.com/2018/08/21/kathleen-booth-assembling-early-computers-while-inventing-assembly/)).

**Suggested transition:** Assembly made machine code human-editable — but scientists still wanted to write **formulas**, and business wanted to write **English**. The 1950s answered both.

---

## 4. Early high-level (1957–1959): FORTRAN, Lisp, COBOL

**Suggested opening line:** By the mid-1950s the bottleneck was no longer the machine — it was the cost and scarcity of people who could win hand-to-hand combat with it.

### FORTRAN — John Backus, IBM, 1954–1957

John Backus joined IBM in **1950** after wandering into Madison Avenue headquarters and being hired on the spot to program the SSEC; by **1953** he had budget for a small team to make programming less brutal ([IBM — John Backus](https://www.ibm.com/history/john-backus)). He later called machine coding “**hand-to-hand combat with the machine**,” with the machine often winning ([IBM — Fortran](https://www.ibm.com/history/fortran)).

**FORTRAN** (Formula Translation) was developed 1954–1957 for the **IBM 704** (core memory, floating-point hardware). Commercial release **1957**. The team — including Lois Haibt (only woman on the team, fresh from Vassar), Harlan Herrick, Roy Nutt, David Sayre, and others — often worked nights because that was when they could get 704 time; winters brought snowball fights between debugging sessions ([IBM — Fortran](https://www.ibm.com/history/fortran)). Skeptics said automatic coding could never match hand assembly; Backus: “We thought it was a good project, and then everyone told us it couldn’t be done… There was a sense that we really wanted to show them” ([IBM — Fortran](https://www.ibm.com/history/fortran)).

**Impact numbers IBM still cites:** problems that took up to ~**1,000** machine instructions could shrink to ~**47** Fortran statements; the first **optimizing compiler** produced code “nearly as fast as anything that could be crafted by hand,” which was the political and technical prerequisite for adoption ([IBM — Fortran](https://www.ibm.com/history/fortran)). Motivation was economic as much as aesthetic: programmer labor was beginning to exceed hardware cost.

### Lisp — John McCarthy, MIT, 1958–

John McCarthy developed Lisp’s key ideas **summer 1956–summer 1958**, with implementation and AI application from **fall 1958 through 1962** (some early ideas in FORTRAN-based FLPL); he recounted this at the 1978 ACM SIGPLAN HOPL conference ([McCarthy — History of Lisp](http://jmc.stanford.edu/articles/lisp.html); [PDF](http://jmc.stanford.edu/articles/lisp/lisp.pdf)). Lisp introduced **S-expressions**, **list processing**, **recursion as style**, and **garbage collection** — memory safety as a language service — born from AI research needs (symbolic expressions, not number crunching). Period-honest first programs: symbolic differentiation, list manipulation, not `printf`.

### COBOL — Grace Hopper’s line, CODASYL, 1959

Grace Brewster Murray Hopper (Yale Ph.D. 1934; Navy; Harvard Mark I under Howard Aiken) had long argued that “It’s much easier for most people to write an English statement than it is to use symbols,” and built **FLOW-MATIC** at Remington Rand as an English-like data processing language ([Yale — Hopper biography](https://president.yale.edu/biography-grace-murray-hopper); [Wikipedia — Grace Hopper](https://en.wikipedia.org/wiki/Grace_Hopper)). **CODASYL** (Conference/Committee on Data Systems Languages) convened in **1959** and produced **COBOL** (Common Business-Oriented Language), heavily influenced by FLOW-MATIC’s English-like syntax for business records and reports ([Wikipedia — CODASYL](https://en.wikipedia.org/wiki/CODASYL); [Wikipedia — COBOL](https://en.wikipedia.org/wiki/COBOL)). Betty Holberton (ex-ENIAC) later worked on language standards including FORTRAN/COBOL-related efforts ([IEEE Computer Society](https://www.computer.org/volunteering/awards/pioneer/about-women-of-eniac)).

### Pain of the prior level

Assembly tied every line to one machine’s opcode map. Scientific users rewritten the same Runge-Kutta in new assemblers per machine. Business users needed non-mathematicians to express payroll and inventory logic. Debugging meant reading dumps of numeric words.

### Period-honest “hello world”

No canonical greeting yet. Early FORTRAN programs printed **numeric tables and formula results** via formatted `WRITE`/`PRINT` of numbers. Lisp printed S-expressions. COBOL printed **reports** (aligned columns of money and names). For the carousel: a short FORTRAN arithmetic program printing a sum or polynomial evaluation is more honest than anachronistic `PRINT *, 'HELLO WORLD'`.

### Pivotal artifacts

- **1957 FORTRAN for the 704** and the *Programmers Primer for FORTRAN Automatic Coding System* ([IBM — Backus](https://www.ibm.com/history/john-backus))
- **McCarthy’s Lisp 1.5 / HOPL history** ([jmc.stanford.edu](http://jmc.stanford.edu/articles/lisp.html))
- **CODASYL 1959 / COBOL-60** as the business-language settlement ([CODASYL](https://en.wikipedia.org/wiki/CODASYL))

### Vivid citable details

1. Backus’s “hand-to-hand combat” and the 1000→47 instruction claim ([IBM Fortran](https://www.ibm.com/history/fortran)).
2. Night shifts on the 704 and snowball fights — research as occupation of scarce machine time ([IBM Fortran](https://www.ibm.com/history/fortran)).
3. Hopper’s wall clock that ran **counterclockwise** — her prop against “we’ve always done it this way” ([Yale Hopper bio](https://president.yale.edu/biography-grace-murray-hopper)).

**Suggested transition:** High-level languages won the lab and the payroll office — but operating systems and tools still needed a language close enough to the metal to replace assembly without becoming unmaintainable. Enter the systems era.

---

## 5. Systems (1970–1985): Pascal, C, C++

**Suggested opening line:** Structured programming taught students to think in blocks; C taught operating systems to travel; C++ taught large programs to grow without collapsing.

### Pascal — Niklaus Wirth, ETH Zürich, 1970

After Algol 60, IFIP WG 2.1 fights, and his own **Algol W** at Stanford (from 1966), Wirth returned to Switzerland and designed **Pascal** “after my own preferences” — a small language for **structured programming** and **data structuring**, aimed at teaching and reliable construction ([ETH — 50 years of Pascal / Wirth CACM 2021](https://inf.ethz.ch/department/history/meilensteine-forschung/50years-pascal.html); [ETH spotlight](https://inf.ethz.ch/news-and-events/spotlights/infk-news-channel/2021/04/niklaus-wirth-pascal-conquers-the-world.html)). Context Wirth recalls: early-1960s workflow was still “written on paper, then punched on cards, and one waited a day for the results” ([ETH / CACM](https://inf.ethz.ch/department/history/meilensteine-forschung/50years-pascal.html)). Pascal became a dominant teaching language worldwide; **PascalCase** naming is a living fossil of that pedagogy.

### C — Dennis Ritchie & Ken Thompson, Bell Labs, 1969–1973

Dennis Ritchie’s own history: **C came into being 1969–1973**, most creatively in **1972**, at Bell Labs Murray Hill after Bell pulled out of **Multics** ([Ritchie — The Development of the C Language](https://www.nokia.com/bell-labs/about/dennis-m-ritchie/chist.html)). Ken Thompson had started **Unix** on a discarded **DEC PDP-7** (8K 18-bit words) in assembly; B (Thompson & Ritchie, influenced by BCPL) was an intermediate systems language; C evolved to write Unix itself in a portable higher-level language as the system moved to the **PDP-11** ([Ritchie chist](https://www.nokia.com/bell-labs/about/dennis-m-ritchie/chist.html)). By September 1973 the OS had largely been translated into C ([B language technical report notes](https://www.nokia.com/bell-labs/about/dennis-m-ritchie/bintro.html)).

### “hello, world” — the greeting freezes

The canonical program descends from **Brian Kernighan**:
- **1972** — *A Tutorial Introduction to the Language B*: external character constants spell out `hello, world!` via `putchar` (B limited character constants to four ASCII chars) ([Wikipedia — Hello, world](https://en.wikipedia.org/wiki/Hello,_world); [Bell Labs B materials](https://www.nokia.com/bell-labs/about/dennis-m-ritchie/bintro.html)).
- **1974** — Bell Labs memo *Programming in C: A Tutorial*: `printf("hello, world");` inside `main` ([Wikipedia — Hello, world](https://en.wikipedia.org/wiki/Hello,_world)).
- **1978** — Kernighan & Ritchie, ***The C Programming Language***: globalizes the example forever.

### C++ — Bjarne Stroustrup, Bell Labs, 1979–1985

Stroustrup’s goal: “**Simula’s facilities for program organization together with C’s efficiency and flexibility for systems programming**,” initially as **“C with Classes” (1979–1983)**, evolving to commercial **C++** with the first book defining the language in **October 1985** ([Stroustrup — A History of C++: 1979−1991](https://www.stroustrup.com/hopl2.pdf)). The idea came from his Cambridge Ph.D. simulator work: Simula’s classes mapped application concepts cleanly, but he needed C-level performance for systems software ([Stroustrup HOPL2](https://www.stroustrup.com/hopl2.pdf)).

### Pain of the prior level

FORTRAN/COBOL/Lisp were poor fits for OS kernels, device drivers, and portable systems utilities. Assembly did not scale to Unix’s ambitions. Unstructured FORTRAN-style control flow had become a recognized maintenance hazard — Dijkstra’s structured-programming arguments and Wirth’s teaching language were the cultural counterweight; C was the systems counterweight.

### Period-honest “hello world”

Now the greeting is historically correct: Kernighan’s B and C tutorials. Carousel can show K&R `hello, world` as the moment the ladder’s demo program stabilizes for fifty years.

### Vivid citable details

1. **PDP-7 with 8K words** and no useful vendor software — Unix begins as a personal environment after Multics disappointment ([Ritchie chist](https://www.nokia.com/bell-labs/about/dennis-m-ritchie/chist.html)).
2. **B’s four-character constants** forcing `hell` / `o, w` / `orld` — the awkward birth of the greeting ([Hello, world history](https://en.wikipedia.org/wiki/Hello,_world)).
3. **Stroustrup’s half-year ambition** to combine Simula + C — “modest” in innovation, “preposterous” in schedule and efficiency demands ([Stroustrup HOPL2](https://www.stroustrup.com/hopl2.pdf)).

**Suggested transition:** C made systems portable and fast — and also made buffer overflows and use-after-free portable and fast. The next era moved safety out of convention and into the runtime and the type system.

---

## 6. Managed / safe systems (1995–2015): Java, C#, Go, Rust, Lean

**Suggested opening line:** The shared thesis of this era: stop trusting the programmer’s discipline alone — make the language and runtime refuse whole classes of disaster.

### Java — James Gosling et al., Sun, 1991–1995

**Green Project** began **June 1991** (Gosling, Mike Sheridan, Patrick Naughton) at Sun; language first named **Oak** after the oak outside Gosling’s office; **Star7** handheld demo **2 September 1992**; renamed **Java**; public debut **23 May 1995**; JDK 1.0 **23 January 1996** ([Computer History Museum — Gosling](https://computerhistory.org/profile/james-gosling/); [Wikipedia — Java](https://en.wikipedia.org/wiki/Java_(programming_language)); [Wikipedia — Oak](https://en.wikipedia.org/wiki/Oak_(programming_language))). Pitch: **“write once, run anywhere”** via the **JVM**, bytecode, and **garbage collection** — safety and portability for the network/applet age. C/C++ undefined behavior and platform IFDEFs were the pain being escaped.

### C# — Anders Hejlsberg, Microsoft, ~2000

Hejlsberg (Turbo Pascal, Delphi) joined Microsoft in the mid-1990s around Java tooling; when Microsoft’s Java path narrowed legally/strategically, the team built **C#** and **.NET** for “the ease of use of Visual Basic and the power and expressiveness of C++” on a platform Microsoft could evolve ([GitHub interview summary — Hejlsberg](https://www.youtube.com/watch?v=uMqx8NNT4xY); [Wikipedia — C#](https://en.wikipedia.org/wiki/C_Sharp_(programming_language)); [Wikipedia — Anders Hejlsberg](https://en.wikipedia.org/wiki/Anders_Hejlsberg)). Managed runtime, CTS, GC — Java’s safety model as industry competition.

### Go — Pike, Griesemer, Thompson, Google, 2007–2009

Designed at Google by **Robert Griesemer, Rob Pike, and Ken Thompson**; public announcement **November 2009**. Motivation: C++ build times and complexity at Google scale; want fast compiles, simple language, first-class concurrency (**goroutines**, channels) ([Pike — Go: Ten years and climbing](https://commandcenter.blogspot.com/2017/09/go-ten-years-and-climbing.html); [Go 2009 talk PDF](https://go.dev/talks/2009/go_talk-20091030.pdf); [golang.design history](https://golang.design/history/); [Wikipedia — Go](https://en.wikipedia.org/wiki/Go_(programming_language))). GC returns; deliberate simplicity over C++ expressiveness.

### Rust — Graydon Hoare, Mozilla, 2006–2015

Personal project of **Graydon Hoare** from **2006**; Mozilla sponsorship; first public announcement around **2010**; **Rust 1.0** on **15 May 2015** ([MIT Technology Review](https://www.technologyreview.com/2023/02/14/1067869/rust-worlds-fastest-growing-programming-language/); [Rust origins notes](https://nick.groenen.me/notes/origins-of-rust/); [Rust Foundation — 10 years](https://rustfoundation.org/media/10-years-of-stable-rust-an-infrastructure-story/); [Wikipedia — Rust](https://en.wikipedia.org/wiki/Rust_(programming_language))). Thesis: **memory safety without GC** via **ownership, borrowing, and lifetimes** — the borrow checker as compile-time proof that C’s worst bugs cannot occur. Pain: decades of CVEs from manual memory management in browsers and OS code (Mozilla’s interest was not accidental).

### Lean — Leonardo de Moura, Microsoft Research, 2013–

**Leonardo de Moura** and collaborators launched the **Lean** theorem prover (**Lean 0.1** era ~**2013** at Microsoft Research); evolved through Lean 2/3 to **Lean 4** as both dependently typed language and proof assistant, with a large **mathlib** community formalizing mathematics ([de Moura et al. system description](https://leodemoura.github.io/files/lean_cade25.pdf); [Lean about](https://lean-lang.org/fro/about/); [Wikipedia — Lean](https://en.wikipedia.org/wiki/Lean_(proof_assistant))). Theme extended to the limit: correctness not only of memory but of **proofs and specifications**.

### Shared theme for narrative

| Language | Safety mechanism | Escape from |
|---|---|---|
| Java / C# | GC + bytecode verification + type system | Manual `malloc`/`free`, platform OBJs |
| Go | GC + simple type system + race detector culture | C++ complexity at scale |
| Rust | Ownership / borrow checker | GC latency *and* C memory unsafety |
| Lean | Dependent types + proof terms | “It typechecks” without “it is true” |

### Period-honest “hello world”

Java’s early demo culture was **applets** and `System.out.println("Hello, World");` — finally the greeting in a managed language on the web. Rust’s `println!("Hello, world!");` is the safety era’s nod to K&R with ownership under the hood.

### Vivid citable details

1. **Oak tree outside Gosling’s office** naming a language that would outlive Sun ([CHM Gosling](https://computerhistory.org/profile/james-gosling/)).
2. **Thompson co-creating Go** decades after co-creating Unix/C — same person, opposite complexity budget ([Pike blog](https://commandcenter.blogspot.com/2017/09/go-ten-years-and-climbing.html)).
3. **Rust 1.0 (2015)** as the moment “memory safety without GC” left research and entered production credibility ([Rust Foundation](https://rustfoundation.org/media/10-years-of-stable-rust-an-infrastructure-story/)).

**Suggested transition:** While systems languages fought over how to be safe *and* fast, another culture optimized for a different scarce resource: **programmer time** and **glue between existing tools** — especially on Unix and the web.

---

## 7. Scripting / dynamic (1987–1995): Bash, Perl, Python, PHP, JavaScript

**Note on ordering:** Thematically this section is “ergonomics and glue”; chronologically it **overlaps and largely precedes** the managed-systems boom (Java 1995 is simultaneous with JavaScript; Perl/Python predate both). Treat as a parallel branch, not a strict sequel.

**Suggested opening line:** Not every program needs a type theorist. Sometimes you need duct tape, a readable loop, and a page that answers back.

### Bash — Brian Fox, GNU, 1989

**Brian Fox** began coding **Bash** (Bourne Again SHell) for the **GNU Project** on **10 January 1988**; beta **0.99** released **8 June 1989**, after Richard Stallman grew impatient with prior shell progress. **Chet Ramey** later became long-term maintainer. Bash was among the earliest programs **Linus Torvalds** ported to Linux (with GCC) ([Wikipedia — Bash](https://en.wikipedia.org/wiki/Bash_(Unix_shell)); [Wikipedia — Brian Fox](https://en.wikipedia.org/wiki/Brian_Fox_(programmer))). Pain addressed: proprietary Bourne shell / inconsistent vendor shells vs free software stack.

### Perl — Larry Wall, 1987

**Larry Wall** released Perl to Usenet **`comp.sources.misc` on 18 December 1987** — a general-purpose Unix scripting language to make **report processing** easier, drawing on C, shell, awk, sed, Lisp. Slogan culture: “easy things should be easy and hard things should be possible”; later nicknamed “**duct tape of the Internet**” as CGI made Perl the web’s connective tissue ([EDN](https://www.edn.com/perl-programming-language-released-december-18-1987/); [Opensource.com — Perl turns 30](https://opensource.com/article/17/10/perl-turns-30); [Wikipedia — Perl](https://en.wikipedia.org/wiki/Perl)).

### Python — Guido van Rossum, CWI, 1989–1991

Conceived late 1980s as a successor to **ABC**; implementation started **December 1989** as a Christmas-holiday project at **CWI** (Amsterdam); first public release **0.9.1** on **`alt.sources` in February 1991**; 1.0 in January 1994 ([Wikipedia — History of Python](https://en.wikipedia.org/wiki/History_of_Python); [Codecademy history](https://www.codecademy.com/resources/blog/history-of-python-coding-language)). Design priority: **readability**, batteries-included stdlib, willingness to be “not the fastest” if it is clear. Pain: shell/Perl cleverness vs maintainable code for larger scripts.

### PHP — Rasmus Lerdorf, 1994–1995

**Rasmus Lerdorf** created **PHP** originally as “**Personal Home Page** Tools” — CGI binaries in C to track visits to his online resume — publicly evolving from **1994** into a server-side embedded language for dynamic web pages ([PHP official history](https://www.php.net/manual/en/history.php.php); [Cybercultural — PHP 1995](https://cybercultural.com/p/1995-php-quietly-launches-as-a-cgi-scripts-toolset/)). Pain: static HTML could not personalize or talk to databases without heavy CGI ceremony.

### JavaScript — Brendan Eich, Netscape, May 1995

Eich joined Netscape **April 1995** and prototyped **Mocha** in **about ten days in May 1995** for Navigator 2.0; renamed LiveScript then **JavaScript** (marketing alliance with Sun’s Java hotness, despite being a different language) ([Cybercultural — Birth of JavaScript](https://cybercultural.com/p/1995-the-birth-of-javascript/); [Wikipedia — JavaScript](https://en.wikipedia.org/wiki/JavaScript)). Pain: the early web was documents without behavior; Netscape needed interactivity in the browser *before* the Java plugin path could own the client.

### Theme

Glue languages, rapid iteration, text and the web as the integration bus, ergonomics over peak performance, Unix scripting culture graduating into full application platforms (LAMP, later Node).

### Period-honest “hello world”

- Bash: `echo Hello, world`
- Perl: `print "Hello, world\n";`
- Python: `print("Hello, world")` (or `print "Hello, world"` in 2.x)
- PHP: `<?php echo "Hello, world"; ?>`
- JavaScript: `alert('Hello, world')` or `document.write(...)` in the 1995 idiom

### Vivid citable details

1. **Ten days in May 1995** — language design under ship pressure ([Cybercultural](https://cybercultural.com/p/1995-the-birth-of-javascript/)).
2. **Christmas holiday at CWI** — Python as a gift to a future that would run AI stacks on a readability-first language ([History of Python](https://en.wikipedia.org/wiki/History_of_Python)).
3. **“Duct tape of the Internet”** — Perl’s self-image as infrastructure, not cathedral ([EDN / Perl lore](https://www.edn.com/perl-programming-language-released-december-18-1987/)).

**Suggested transition:** Scripting put programming in everyone’s browser and everyone’s crontab. The next shift did not add another syntax so much as change **who writes the middle of the program** — a model on the other side of an API.

---

## 8. AI Engineering (c. 2022–2025)

**Suggested opening line:** For seventy-five years the contract was: you specify the steps. After November 2022, a surprising amount of the time the contract became: you specify the outcome, and you engineer everything around the model that pursues it.

### Origin story / pivot

**OpenAI launched ChatGPT on 30 November 2022** — a conversational interface to a sibling of InstructGPT, trained to follow instructions in natural language ([OpenAI — Introducing ChatGPT](https://openai.com/index/chatgpt/)). The productized chat UI, not only the underlying GPT-3.5/4-class models, flipped LLMs from research curiosity to default interface. Anthropic’s **Claude** and other labs’ chat/API offerings formed a competitive API market within months.

In **June 2023**, Shawn Wang (**swyx**) published **“The Rise of the AI Engineer”** on Latent Space, naming a role distinct from ML engineer/researcher: software engineers who **wield foundation-model APIs and open models** to ship products — “on the other side of the API line” ([Latent Space — The Rise of the AI Engineer](https://www.latent.space/p/ai-engineer); [AI Engineer about](https://www.ai.engineer/about)). Core claims to cite carefully:

- Tasks that took “5 years and a research team” in 2013 can take “API docs and a spare afternoon” in 2023 ([Latent Space](https://www.latent.space/p/ai-engineer)).
- Supply math: “~5000 LLM researchers” vs “~50m software engineers” → an in-between builder class ([Latent Space](https://www.latent.space/p/ai-engineer)).
- Karpathy quoted: there will be “significantly more AI Engineers than… ML engineers”; success “without ever training anything”; and earlier, “the hottest new programming language is English” ([Latent Space](https://www.latent.space/p/ai-engineer)).

### Pain of the prior level

Classical software required specifying algorithms and edge cases in code. Classical ML required data pipelines, training budgets, and specialized staff. Foundation-model APIs collapsed custom model building for many apps — but introduced new pains: non-determinism, prompt injection, context limits, cost/latency, evaluation difficulty, and the need to **orchestrate** tools, retrieval, and human-written control flow around probabilistic components.

### What “programming” looks like

- **Prompt contracts**: system prompts, schemas, few-shot examples, constraints — specifications in natural language + structured output.
- **Tool use / function calling**: models emit structured calls to developer-defined functions; the app executes them and returns results (OpenAI function calling / tools API as a pivotal product primitive) ([OpenAI function calling docs](https://developers.openai.com/api/docs/guides/function-calling)).
- **RAG** (retrieval-augmented generation): fetch relevant documents into context rather than fine-tuning everything.
- **Agent harnesses**: loops of plan → tool → observe (Auto-GPT/BabyAGI wave; production descendants more disciplined).
- **Orchestration frameworks**: **LangChain**, **LlamaIndex**, etc., as early standard libraries for chains and indexes (swyx notes LangChain’s outsized early ecosystem role) ([Latent Space](https://www.latent.space/p/ai-engineer)).
- **Evals**: the emerging “unit tests” of non-deterministic systems.

Shift in one line: from **“write code that does X”** to **“write a contract with a model that does X, plus the scaffolding that makes that safe and repeatable.”**

### Period-honest “hello world” (carousel peers)

1. **Tight prompt contract** — roles, output schema, refusal boundaries, temperature, tool definitions: engineered hello.
2. **Casual vibe one-liner** — “say hello world like a pirate”: the same capability surface with none of the engineering.

The narrative point: both are real entry points; only one is operable in production.

### Pivotal artifacts / moments

| Date | Artifact |
|---|---|
| 30 Nov 2022 | ChatGPT public launch ([OpenAI](https://openai.com/index/chatgpt/)) |
| 2023 | Chat completions + function calling as app platform |
| Jun 2023 | swyx, “The Rise of the AI Engineer” ([Latent Space](https://www.latent.space/p/ai-engineer)) |
| 2023–2024 | RAG + agent patterns enter mainstream eng practice |
| 2023+ | AI Engineer conference/community institutionalizes the title ([ai.engineer](https://www.ai.engineer/about)) |

### Vivid citable details

1. **Karpathy’s “hottest new programming language is English”** — provocation that only works because models map English to actions and code ([Latent Space](https://www.latent.space/p/ai-engineer)).
2. **“OpenAI wrappers” insult → serious product category** — the essay’s defense of software around models ([Latent Space](https://www.latent.space/p/ai-engineer)).
3. **Same hello, two contracts** — production prompt vs vibe-coded one-liner as the era’s pedagogical pair (blog carousel design).

**Suggested transition (closing the ladder):** From plugboards to prompts, each layer still bottoms out in machine state changes. The programmer’s job keeps migrating toward specifying intent and invariants — and away from manually placing every bit.

---

## Closing reflection (for the narrative coda)

What stays constant across all eight eras is not syntax, media, or even the definition of a “program.” It is the desire to make a machine do our bidding with **less friction and more leverage** — and the recurring discovery that yesterday’s leverage is today’s bottleneck. ENIAC’s programmers fought cables; Backus fought opcodes; Ritchie fought non-portable assembly; Gosling fought undefined behavior; Eich fought a static web; AI engineers fight non-determinism and evals. Abstractions pile up: an AI agent’s tool call may generate Python that runs on a JVM or CPython that sits on a C runtime that emits machine code that an OS loader maps into the same kind of addressable memory the Manchester Baby first proved would work in June 1948. “Hello world” changes costume — trajectory table, squares tape, Fortran `WRITE`, K&R `printf`, `println!`, `echo`, system prompt — but it is always the smallest complete proof that the current layer of the stack is alive and listening.

---

## Quick reference: timeline spine

| Year | Event | Era |
|---:|---|---|
| 1945-06 | von Neumann EDVAC First Draft circulates | 1→2 |
| 1945-12-10 | ENIAC first classified run | 1 |
| 1946-02-14/15 | ENIAC public unveiling | 1 |
| 1948-06-21 | Manchester Baby first stored program | 2 |
| 1949-05-06 | EDSAC first program (squares) | 3 |
| 1951 | Wilkes/Wheeler/Gill textbook | 3 |
| 1953–54 | IBM 650 announced/delivered | 2 |
| 1957 | FORTRAN commercial release (IBM 704) | 4 |
| 1958–59 | Lisp ideas/implementation; CODASYL/COBOL | 4 |
| 1970 | Wirth’s Pascal | 5 |
| 1972 | C’s creative peak; Kernighan B tutorial “hello” | 5 |
| 1974 | Kernighan C tutorial `hello, world` | 5 |
| 1978 | K&R book | 5 |
| 1979–85 | C with Classes → C++ | 5 |
| 1987-12-18 | Perl 1.0 on Usenet | 7 |
| 1989 | Bash; Python implementation starts (Dec) | 7 |
| 1991-02 | Python 0.9.1 public | 7 |
| 1991-06 | Green/Oak project starts | 6 |
| 1994–95 | PHP tools; Java public; JS in 10 days | 6–7 |
| 2000 | C# / .NET era begins | 6 |
| 2009-11 | Go public | 6 |
| 2010/2015 | Rust public / Rust 1.0 | 6 |
| 2013 | Lean theorem prover begins | 6 |
| 2022-11-30 | ChatGPT launch | 8 |
| 2023-06 | “Rise of the AI Engineer” (swyx) | 8 |

---

## Source quality notes for the author

- Prefer **IBM Archives**, **Ritchie’s Bell Labs pages**, **Stroustrup’s HOPL paper**, **McCarthy’s HOPL Lisp history**, **Cambridge CL EDSAC pages**, **Manchester computer50**, **OpenAI’s ChatGPT post**, and **swyx’s Latent Space essay** as spine citations in the finished blog.
- **Wikipedia** was used as an index and for well-corroborated dates (e.g., Java release table, Bash timeline); re-check any single-sourced wiki claim before publishing.
- ENIAC first-program classification: state uncertainty honestly (Los Alamos / likely thermonuclear-related; still described as classified in secondary sources).
- Kathleen Booth “invented assembly language” is a popular framing; safer narrative wording is **early mnemonic coding documentation in the late 1940s, in parallel with EDSAC initial orders and later IBM assemblers**.
- Hello-world origin: credit **Kernighan 1972 B / 1974 C**, popularized by **K&R 1978**; BCPL 1967 claims exist in lore but are thinner.

---

*Research compiled for narrative drafting. Raw fetch extracts live under `research_raw/` in the workspace if deeper quotation is needed.*
