# Adversarial review: “The Element Has a Name”

Target: <https://stephens.page/blog/the-element-has-a-name/>  
Reviewed: 2026-08-05, approximately 16:35 UTC  
Scope: the human article, its live specimens, and the linked `agents.md` companion

## Verdict

Do not promote the current page as an authoritative reference until the release blockers below are resolved.

The premise is excellent: ambiguous component names create expensive implementation errors, especially when an agent turns a vague noun into a large diff. The live-specimen format is memorable, the source disclosure is unusually good, and the article has clearly been built rather than merely described.

But the piece demands terminological precision while repeatedly failing its own standard. Its first comparison contradicts itself; “canonical” is used far beyond the authority of the cited glossary; several specimens do not implement the components whose names they teach; the native-capability probe measures syntax exposure rather than production readiness; and the learning-science section misnames the central construct it attributes to Bjork and Bjork. The machine-oriented companion then converts some of those overstatements into unconditional instructions for coding agents.

This is not a copyediting problem. It is a credibility problem at the exact layer the article claims to make reliable.

## Release blockers

### 1. The opening figure fails its own disambiguation test

The prose above Figure 1 says:

- two of the five controls run commands and three hold a value; and
- only one of the five is a single native HTML element.

The table immediately below says something else:

- only the dropdown menu runs commands;
- the dropdown list, listbox, combo box, and autocomplete all hold values; and
- both the dropdown list and listbox are single native `<select>` elements (`<select>` and `<select multiple>`).

The table is internally much closer to correct than the paragraph. The paragraph should say one runs commands, four hold a value, and two are single native elements. This is the article's flagship example. If it cannot count the categories in its own five-row table, the reader has no reason to trust the later inventory.

There is a second problem inside the same figure: the “autocomplete” is only a text input plus a `role="status"` string containing matches separated by dots. The suggestions cannot be focused, navigated, or selected. It demonstrates string filtering, not an autocomplete component. Calling it “live” lowers the behavioral bar until almost any styled fragment qualifies as the named component.

### 2. “Canonical” is an assertion the evidence does not support

NN/g published a useful glossary. It did not become a web standard or acquire authority over Apple, Material, platform accessibility APIs, HTML, ARIA, or every design system. The article nevertheless says NN/g “solved the vocabulary problem,” calls its terms canonical, and then applies the same canonical label to 103 specimens assembled from NN/g, Component Gallery, product-specific conventions, marketing-gallery categories, and the author's own bins.

The article later concedes that there is no agreed taxonomy and that 95 design systems still disagree. That concession does not coexist cleanly with “solved” or “canonical.” At most, these are:

- NN/g-preferred terms within the scope of its glossary;
- common names observed across design systems; and
- house terms chosen by the author where the sources disagree.

The labels also collapse distinctions the prose says matter:

- “Date picker” is labeled “also: calendar picker,” while its own note says NN/g separates Date Picker and Calendar Picker.
- “Form” is labeled “also: fieldset group,” although a `<form>` and a `<fieldset>` have different semantics and purposes.
- “Drawer” includes “drawer menu” as a synonym, while the collisions section says NN/g lists Drawer Menu separately from Side Sheet.
- “Data grid” is implemented as a sortable HTML table. A data grid is an interactive composite with managed focus, not merely any table with sortable headers. The [WAI-ARIA grid pattern](https://www.w3.org/WAI/ARIA/apg/patterns/grid/) explicitly distinguishes a grid from a table on this basis.
- “Tree view” is nested `<details>` elements without tree roles or tree keyboard behavior. It is a disclosure hierarchy, not a tree widget.

The article's most defensible conclusion is not “the element has a canonical name.” It is “the team needs a shared, scoped name and a behavioral contract.” That is a better thesis and is already latent in the final section about project-level glossaries.

### 3. The native-versus-library argument confuses feature exposure with a finished component

Figure 7 accurately reports that all 18 expressions return true in the installed Chrome 142. That result was reproducible. The inference drawn from it is not.

Most probes answer only whether a property, selector, method, or input type is recognized. `CSS.supports(...)` does not demonstrate usable rendering, complete interaction, accessibility, compatibility with the project's browser matrix, or freedom from implementation defects. Reflection of `input.type = "date"` does not prove that the picker meets the product's formatting, localization, validation, or consistency requirements. Recognition of `::scroll-button()` does not test a carousel. Presence of `anchor-name` does not test a tooltip.

The article quietly proves this distinction itself:

- its tooltip is positioned with `getBoundingClientRect()`, not CSS anchor positioning;
- its carousel uses custom JavaScript buttons, not `::scroll-button()`; and
- its menus use the popover top layer but do not implement menu semantics or menu keyboard behavior.

The companion's directive—do not add a component library for a dialog, menu, tooltip anchor, accordion, slider, date input, or color input—is therefore unsafe. Native primitives can remove plumbing, but primitives are not complete product components. Keyboard behavior is not an “edge case”; for composite widgets it is part of the component definition.

Replace the binary “native or library” conclusion with a decision matrix:

1. Does the target browser matrix expose the primitive?
2. Does the primitive supply the semantics and interaction pattern required here?
3. What behavior, styling, validation, localization, and test code remains?
4. Is the remaining code smaller and safer than the project's existing component abstraction?

### 4. Several teaching specimens are inaccessible or behaviorally mislabeled

The page says element names act as specifications. If so, a named specimen must include the behavior users reasonably infer from that name. Several do not.

- **Tabs:** Both tabs are in the page tab order and the script handles clicks only. Left/Right Arrow does nothing. The [WAI-ARIA tabs pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) expects a single tab stop with arrow-key movement (and appropriate activation behavior).
- **Action menus:** The trigger and popup have no `aria-haspopup="menu"`, `role="menu"`, or `role="menuitem"`; opening does not move focus to the first item; arrow keys do not navigate; selecting an item neither runs a command nor closes the menu. The Popover API supplies top-layer display, light dismiss, an invoker relationship, and sequential focus-order help. It does not turn arbitrary buttons into the [menu-button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/).
- **Rating:** A container has `role="radiogroup"`, but its children are ordinary buttons with no radio role or checked state. All five are tab stops. Assistive technology is told there is a radiogroup containing no radios.
- **Autocomplete:** Suggestions are unselectable status text, with no listbox, option, active descendant, or completion behavior.
- **Data grid and tree view:** These are a sortable table and nested disclosures, respectively, not the composite widgets their labels promise.
- **Floating action button:** The visible “button” is a `<span>` with no action, focusability, accessible name, or button semantics.
- **Contextual menu:** Its target is a non-focusable `<div>`, so a keyboard user cannot reach it to invoke the context menu.
- **Toast action:** The toast disappears after five seconds, but focus remains on a trigger in the middle of a very long document and the Undo button lives near the end of the DOM. A keyboard user has no practical route to the action before it vanishes.

These are not demands for production complexity on a teaching page. They are the lesson. The article argues that the noun determines the implementation; its specimens must therefore honor the noun's behavioral contract.

### 5. The accessibility section claims invariants while the page violates basic ones

An automated axe run against the current live page in Chrome 142 found six WCAG A/AA rule categories with violations:

- one unlabeled file input;
- two transfer-list `<select>` elements without accessible names;
- five light-theme contrast failures (four remained in the settled dark theme);
- twelve links in text blocks distinguishable only by color in the light theme;
- two scrollable regions without keyboard access; and
- eight undersized targets (the five rating buttons and three carousel dots).

Automated checks do not detect the composite-widget problems above. Those came from keyboard and DOM inspection.

The companion's “accessibility invariants” list is consequently dangerous as a checklist: it is short enough to imply completeness, omits the failures present on the page, and the specimens do not satisfy it in spirit. Either rename it “selected accessibility notes” or make accessibility a real acceptance gate with automated and keyboard tests.

### 6. The filtering and recall interactions make false claims about their own behavior

The switchboard does not hide nonmatches; it sets them to `opacity: 0.18` while leaving all controls focusable and interactive. Its count nevertheless says items are “shown.” More seriously, the input specimens are nested inside a parent `.spec` named Form. Searching for “rating” leaves the Rating specimen undimmed but dims its Form ancestor, so the supposedly shown result remains visually faded. The counter reports “1 of 103 shown” while the one result is still at 18% ancestor opacity.

The recall drill caption says its 24 specimens are drawn from all five families. The hard-coded pool contains navigation, input, status, and display specimens—none from the page-level family.

The caption also says pointer events are disabled so the specimen cannot be poked. Pointer suppression is not interaction suppression: cloned inputs, selects, links, summaries, and buttons remain keyboard-focusable. `cloneNode(true)` does not preserve the original JavaScript listeners, so some staged controls look interactive, enter the tab order, and then stop working.

These are small implementation bugs individually. In a piece about exact specifications and verifiable teaching, they are evidence that the claims were written before the behavior was audited.

### 7. The learning-science section misstates its source

Bjork and Bjork's New Theory of Disuse distinguishes **retrieval strength** from **storage strength**, not “fluency strength” from storage strength. The [Bjork Learning and Forgetting Lab's own summary](https://bjorklab.psych.ucla.edu/research/) uses retrieval strength and storage strength. “Retrieval fluency” is a related idea, but “fluency strength” is not the named construct the article attributes to the 1992 theory.

The article also says multiple choice “adds almost nothing to storage.” The cited Roediger and Karpicke study compared restudying with immediate free-recall tests, not multiple-choice recognition with free recall. Its result was time-dependent: restudying did better after five minutes, while prior testing produced better retention after two days and one week. The [paper's abstract](https://doi.org/10.1111/j.1467-9280.2006.01693.x) supports retrieval practice over restudy for delayed retention; it does not support the article's categorical dismissal of multiple-choice learning.

Use the correct term, describe the actual experimental comparison, and present the recall drill as a plausible application rather than a result established by those citations.

### 8. The human and agent versions have already drifted

At review time the live human page reported 103 named elements, including a newly added table of contents. The linked `agents.md` still said 102 and listed 21 navigation elements rather than the live 22. The human page's rendered article text was roughly 5,377 words including visible specimen content and labels, while the metadata advertised approximately 3,500.

The exact numbers are not important. The drift is. A machine-oriented source of truth should not be maintained as a second handwritten inventory beside a rapidly changing HTML document. Generate both views from one structured element dataset, or remove claims of completeness and exact counts from the companion.

## Structural criticism

The article is trying to be three things at once:

1. an argument for precise component language;
2. a 103-item visual atlas; and
3. a browser-capability and dependency essay.

The first is sharp. The second is useful as a reference. The third needs a much more careful definition of “native.” Combined, they create a page whose breadth fights its teaching goal. A reader is unlikely to retain 103 names, and the six-question quiz barely samples the inventory. The page itself admits that same-session performance does not establish durable learning.

Split the work:

- Keep the essay focused on the five-way “dropdown” ambiguity, the highest-cost collisions, and the project-glossary recommendation.
- Move the complete specimen atlas to a reference page with per-item provenance, behavior contracts, and accessibility notes.
- Make the native-capability probe a separate lab that clearly distinguishes API detection from production readiness.

That structure would make the central argument shorter, stronger, and less vulnerable to a single broken specimen discrediting the whole taxonomy.

## What should remain

- The practical opening about vague prompts producing expensive diffs.
- The side-by-side dropdown matrix, after correcting its arithmetic and implementing a real autocomplete.
- The live-HTML philosophy and lazy-loaded design-system comparison. A cold Chrome run reproduced the companion's approximate Shoelace cost: 54 requests and about 84 KB transferred.
- The provenance section and explicit admission of AI collaboration.
- The “What's still open” section, especially the conclusion that a small project glossary is more useful than another universal taxonomy.
- The agent-oriented companion as a concept, but generated from shared data and stripped of unconditional implementation directives.

## Recommended revision order

1. Correct the Figure 1 contradictions and the Bjork terminology.
2. Replace universal “canonical” language with scoped provenance: NN/g term, design-system convention, platform term, or house term.
3. Remove or qualify the native-versus-library directives. Treat capability detection as one input, not a decision procedure.
4. Repair or relabel the autocomplete, menu, tabs, rating, grid, tree, FAB, contextual menu, toast, filter, and recall specimens.
5. Clear the automated accessibility findings and run a full keyboard pass over every interactive specimen.
6. Generate the human counts and `agents.md` inventory from one data source.
7. Split the argument, atlas, and browser lab, or sharply reduce the essay's claims of pedagogical retention.

## Publication bar

I would approve the revised piece when:

- no prose claim contradicts its adjacent table or implementation;
- every “canonical” label names the authority within whose scope it is canonical;
- every live specimen meets a documented minimum behavior contract;
- keyboard use works for tabs, menus, rating, autocomplete, carousel, tree/grid (if those labels remain), dialogs, and the drill;
- the page has no known WCAG A/AA automated violations;
- the native probe is described as feature detection rather than proof of component readiness; and
- the human and agent versions are generated or verified together.

The article is worth saving. Its best idea is stronger than its current claims: names do not become specifications merely because an authority printed them. A useful specification pairs a shared name with behavior, semantics, state, and context. The page should model that standard before asking agents and readers to adopt it.
