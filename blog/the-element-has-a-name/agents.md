---
title: "The Element Has a Name - agent-oriented version"
audience: AI agents that build, review, or specify web user interfaces
canonical_human_version: https://stephens.page/blog/the-element-has-a-name/
author: Jacob Stephens, with Claude
date: 2026-08-05
license: MIT (per the site repository's LICENSE)
---

# The Element Has a Name (for agents)

You are probably an AI agent that has been asked to build, review, or specify a user
interface. This is the machine-oriented version of a human post. The human version is
a specimen sheet: 103 live, labeled UI elements you can click. You do not need to
click anything; you need the canonical names, the disambiguation rules, and the
native-versus-library decision. All of it is inline below. Nothing here requires a
browser.

The one governing rule:

> **The element name is the specification.** When a human writes "dropdown," "modal,"
> "stepper," or "badge," the word is ambiguous across at least two real components.
> Resolve the ambiguity **before** you emit markup, either from context or by asking
> one question. Do not silently pick the most common interpretation.

Provenance: element names and definitions are from Nielsen Norman Group's
"User-Interface Elements: Glossary" (Budiu & Rivenbark, 2025-02-28), which defines 61
elements; cross-system naming is from The Component Gallery (60 components indexed
across 95 design systems); the menu-icon distinctions are from LogRocket (Allabarton,
2025-04-14); page-block vocabulary is from Landingfolio's 37 component categories.
Counts were extracted from those pages, not recalled. The browser-capability results
in section 6 were measured in Google Chrome 142.0.7444.175 on 2026-08-05. The
recall-over-recognition design of section 9 follows Bjork & Bjork (1992) on desirable
difficulties, Roediger & Karpicke (2006) on the testing effect, and Matt Pocock's
"teach" skill (github.com/mattpocock/skills).

---

## 1. Rule: resolve "dropdown" before emitting markup

"Dropdown" maps to five distinct components. Pick with this table.

| If the requirement is | Emit | Native? |
|---|---|---|
| Run one of several **commands** (Rename, Delete) | button + `popover` menu | button + popover |
| Pick **one value** from a closed, known set | `<select>` | yes, one element |
| Pick **one or many** values, options always visible | `<select multiple size=N>` | yes |
| Pick from a list **or type a value not on it** | `<input list="x">` + `<datalist id="x">` | yes |
| Suggest from an **open-ended** set as the user types | text input + JS filter/fetch | no |

| Control | Holds a value? | Off-list input? | Options always visible? | Native HTML |
|---|---|---|---|---|
| Dropdown menu | no - runs commands | n/a | no | button + popover |
| Dropdown list | yes | no | no | `<select>` |
| Listbox | yes (often many) | no | yes | `<select multiple>` |
| Combo box | yes | yes | no | `input` + `<datalist>` |
| Autocomplete | yes | yes | no | JavaScript |

**Directive:** if a ticket says "dropdown" and does not say whether it holds a value or
runs a command, that is the one question to ask. Everything else you can infer.

## 2. Rule: modality is a mode, not a component

`<dialog>` is the component. The mode is chosen by the method you call:

- `dialog.showModal()` - enters the **top layer**, renders `::backdrop`, makes the rest
  of the document inert, Escape closes it. This is "a modal."
- `dialog.show()` - same element, no backdrop, page stays interactive. Non-modal.

The **bottom sheet**, **drawer / side sheet**, **lightbox**, and **confirmation dialog**
are all the same `<dialog>` element with different CSS and different content patterns.
Do not build any of them from `<div>` + manual focus trapping; you will reimplement
inert, focus return, and Escape handling worse than the browser does.

**Directive:** never introduce a component named `Modal`. Name it `Dialog` and take
modality as a prop.

## 3. Canonical names by family

The five-family split is a working convention, not a standard. UXPin's guide uses four
categories (input, output, navigational, container); NN/g imposes no families at all and
lists 61 entries alphabetically. The **element names** below are canonical; the bins are
the author's.

### 3.1 Navigation (22 in the human post)

| Canonical name | Also called | Note |
|---|---|---|
| Navigation bar | navbar, app bar, header nav | |
| Sidebar | side navigation, nav rail | |
| Tab bar | tabs | NN/g: "Tab Bar (Tabs)" |
| Bottom navigation | tab bar (mobile) | |
| Breadcrumbs | breadcrumb trail | hierarchical position, not history |
| Pagination | pager | |
| Anchor link | in-page link, jump link | NN/g lists all three |
| Hamburger menu | - | **three horizontal lines**; site navigation |
| Kebab menu | overflow menu | **three dots, vertical**; item actions |
| Meatball menu | - | **three dots, horizontal**; row actions |
| Bento menu | grid menu, app switcher | **grid of squares**; app switching |
| Dropdown menu | pulldown menu, linear menu | |
| Megamenu | rectangular menu, square menu | |
| Submenu | nested menu, flyout menu | |
| Contextual menu | right-click menu, context menu | |
| Pie menu | radial menu | |
| Search field | search input, search box | |
| Drawer | side sheet, flyout, drawer menu | NN/g: "Side Sheet (Drawer, Flyout)" |
| Stepper | wizard, progress steps | **collides** - see section 5 |
| Back-to-top button | scroll-to-top | |
| Toolbar | action bar, control bar | |
| Table of contents | in-page navigation, on this page, jump list | built from anchor links; pair with a current-section indicator |

### 3.2 Input (26)

| Canonical name | Also called | Native element |
|---|---|---|
| Button | push button, CTA | `<button>` |
| Split button | dropdown button | `<button>` + popover |
| Segmented control | segmented button, button group | none |
| Floating action button | FAB, floating button | `<button>` |
| Text field | textbox, input field | `<input type=text>` |
| Textarea | multi-line text field | `<textarea>` |
| Password field | masked input | `<input type=password>` |
| Checkbox | tick box | `<input type=checkbox>` |
| Radio group | radio buttons, option buttons | `<input type=radio>` |
| Toggle switch | switch, state-switch control | `<input type=checkbox role=switch>` |
| Rating | star rating | none |
| Filter chip | filter tag, choice chip | none |
| Slider | range control, continuous control | `<input type=range>` |
| Input stepper | number input, spin button | `<input type=number>` |
| Knob | virtual knob, dial | none |
| Date picker | calendar picker, date input | `<input type=date>` |
| Wheel picker | spinner picker, drum picker | platform-dependent |
| File upload | file input, dropzone | `<input type=file>` |
| Color picker | colour input, swatch picker | `<input type=color>` |
| Transfer list | dual listbox, shuttle, pick list | none |
| Multiselect | tag input, token field | none |
| Form | fieldset group | `<form>` |
| Dropdown list, Listbox, Combo box, Autocomplete | see section 1 | |

**Directive:** checkbox vs toggle switch is decided by *when the change applies*. A
switch applies immediately with no submit step; a checkbox collects a value the form
submits later. If your UI has a Save button, use checkboxes.

### 3.3 Feedback and status (19)

| Canonical name | Also called | Note |
|---|---|---|
| Alert | inline message, callout | in the document flow |
| Toast | snackbar | transient, self-dismissing, non-blocking |
| Modal dialog | modal | `<dialog>.showModal()` |
| Non-modal dialog | modeless dialog | `<dialog>.show()` |
| Confirmation dialog | confirm | name the action in the button, never "OK" |
| Bottom sheet | action sheet | `<dialog>` anchored to bottom edge |
| Lightbox | image overlay | non-fullscreen media overlay |
| Progress bar | determinate progress | `<progress value max>` |
| Progress indicator | indeterminate progress | duration unknown |
| Spinner | loading spinner, activity indicator, wait animation | |
| Skeleton screen | content placeholder, shimmer | |
| Backdrop | scrim, overlay | `::backdrop` for dialogs |
| Badge | notification dot, counter | **collides** - see section 5 |
| Tooltip | popup tip | **text only, never interactive content** |
| Popover | popup | may contain links and focusable content |
| Hover card | preview card | hover intent, rich content |
| Empty state | blank slate, zero state | |
| Error state | validation message, field error | `aria-invalid` + `aria-describedby` |
| Status indicator | health dot, presence dot | pair with text, never color alone |

**Directive:** if the overlay needs a link or a button inside it, it is a popover, not a
tooltip. Putting interactive content in a `role="tooltip"` element makes it unreachable
by keyboard and screen reader.

### 3.4 Display and containers (22)

Card, Panel, Paper (surface, elevated container), Divider (separator, rule), Accordion
(disclosure group, expander), Table, Data grid (sortable table, datatable), List, Tree
view, Timeline, Carousel (slider, slideshow), Image list (gallery, image grid), Chart,
Sparkline (inline chart, micro chart), Stats block (stat tile, KPI row, metric card),
Avatar, Icon, Tag (chip, pill, label), Typography scale (type ramp), Blockquote (pull
quote), Layout primitives (box, stack, grid, container), Scrollbar.

**Directive:** an **accordion** is native. `<details name="group">` gives exclusive
open/close with zero JavaScript. Do not import an accordion component.

**Directive:** **Tag** (non-interactive) and **filter chip** (pressable) are different
components. If it has `aria-pressed`, it is a chip; if it is decorative metadata, it is
a tag.

### 3.5 Page-level blocks (14)

Marketing pages compose from blocks, not atomic controls. Landingfolio indexes 37
categories; by example count the largest are Feature (995), Hero (456), Footer (393),
Header (390), Call To Action (297), Testimonial (296), Content (245), Logo Cloud (179),
Pricing (88).

Standard top-to-bottom order used in the human post: Notification bar / Promotion bar,
Header, Hero, Logo cloud, Feature grid, How it works, Testimonial, Stats band, Pricing
table, FAQ, CTA band, Newsletter signup, Footer.

**Directive:** when asked for "a landing page," emit these block names as section
comments or component names. It makes the output reviewable in one pass and matches the
vocabulary the requester is already using.

## 4. NN/g's 61 canonical entries, verbatim

Use this list when you need the authoritative name. Parentheses are NN/g's own alternate
names.

2D-Matrix Input Control; Accordion; Anchor Link (In-Page Link, Jump Link); Back-to-Top
Button; Badge; Bottom Sheet; Breadcrumbs; Button; Calendar Picker; Card; Carousel;
Checkbox; Combo Box; Container; Contextual Menu; Control; Date Picker; Dialog; Drawer
Menu; Dropdown List; Dropdown Menu (Pulldown Menu, Linear Menu); Expandable Menu;
Floating Button (Floating Action Button or FAB); Icon; Input Control; Input Stepper;
Knob (Virtual Knob); Lightbox; Link (Hyperlink); Listbox; Megamenu (Rectangular Menu,
Square Menu); Menu; Menu Bar; Navigation Bar; Navigation Menu; Overlay; Picker; Pie Menu
(Radial Menu); Popup (Popover); Popup Tip; Progress Bar; Progress Indicator; Radio
Button; Range Control (Continuous Control); Ribbon; Scrollbar; Segmented Button
(Segmented Control); Side Sheet (Drawer, Flyout); Skeleton Screen; Slider; Snackbar
(Toast); Spinner (Wait Animation, Loading Spinner, Activity Indicator); Split Button;
State-Switch Control; Submenu; Tab Bar (Tabs); Textbox (Text Field, Input Field); Toggle
(Toggle Switch, Switch); Tooltip; Wheel Picker; Wheel-Style Date Picker.

## 5. Collisions - the words that cost review time

| Word | The collision | What to say instead |
|---|---|---|
| **Stepper** | Component Gallery's "Stepper" is the multi-step wizard. NN/g's "Input Stepper" is the numeric increment control. Two unrelated components. | "wizard" or "number input" |
| **Badge** | Bootstrap's badge is a small inline label (= Material's chip, Polaris's tag). Material's and NN/g's badge is the count bubble on an icon. | "count badge" or "tag" |
| **Modal** | Not a component; a property of a dialog. | "modal dialog" or "dialog, modal: true" |
| **Snackbar / toast** | Material says snackbar; everyone else says toast. NN/g: "Snackbar (Toast)." | either, but pick one per codebase |
| **Drawer / side sheet / flyout** | Three names, one element. NN/g: "Side Sheet (Drawer, Flyout)." | "drawer" |
| **Segmented control** | Apple's name; Material 3 says segmented button. | "segmented control" |
| **Popover** | Both a component name (NN/g "Popup (Popover)") **and** an HTML attribute that is a top-layer mechanism. | say "the `popover` attribute" when you mean the mechanism |
| **Card** | The most overloaded container. NN/g: "container resembling playing card size holding related brief information." | if it fills the page it is a panel or surface |
| **Dropdown** | Five components. See section 1. | never use the bare word |

## 6. Native-versus-library: measured, not assumed

Run these exact expressions to decide whether you need a dependency. Every one returns a
boolean and needs no library. **All 18 returned `true` in Google Chrome
142.0.7444.175 on 2026-08-05.** Firefox and Safari score lower on the last five rows;
re-measure rather than trusting this table for a non-Chrome target.

| Capability | Detection expression | Chrome 142 |
|---|---|---|
| Modal dialog | `typeof HTMLDialogElement.prototype.showModal === 'function'` | yes |
| Popover / top layer | `Object.prototype.hasOwnProperty.call(HTMLElement.prototype,'popover')` | yes |
| Exclusive accordion | `'name' in document.createElement('details')` | yes |
| Combo box list | `'options' in document.createElement('datalist')` | yes |
| Search landmark | `!(document.createElement('search') instanceof HTMLUnknownElement)` | yes |
| Progress bar | `'max' in document.createElement('progress')` | yes |
| Slider | `i=document.createElement('input'); i.type='range'; i.type==='range'` | yes |
| Date picker | same pattern with `type='date'` | yes |
| Color picker | same pattern with `type='color'` | yes |
| Inert background | `'inert' in HTMLElement.prototype` | yes |
| Anchor positioning | `CSS.supports('anchor-name: --a')` | yes |
| Customizable select | `CSS.supports('appearance: base-select')` | yes |
| Parent selector | `CSS.supports('selector(:has(a))')` | yes |
| Auto-sizing input | `CSS.supports('field-sizing: content')` | yes |
| Balanced headings | `CSS.supports('text-wrap: balance')` | yes |
| View transitions | `'startViewTransition' in document` | yes |
| Scroll-driven animation | `CSS.supports('animation-timeline: scroll()')` | yes |
| CSS carousel buttons | `CSS.supports('selector(::scroll-button(*))')` | yes |

**Directive:** do **not** add a component library to obtain a dialog, a menu, a tooltip
anchor, an accordion, a slider, a date input, or a color input. Those are native. A
library earns its place on theming, on keyboard behavior in edge cases, and on
cross-team consistency - not on capability.

Measured cost of the alternative, for calibration: loading Shoelace 2.20.1's `sl-select`,
`sl-option`, `sl-switch`, and `sl-rating` from jsDelivr took **54 requests and ~84 KB
transferred** to render three controls.

## 7. Accessibility invariants

These are not style preferences; violating them produces a broken control.

1. Tooltips (`role="tooltip"`) contain **text only**. Interactive content goes in a
   popover.
2. Status is never communicated by color alone. Pair the dot with a word.
3. A sortable column header carries `aria-sort` on the `<th>`, not on the button.
4. Tabs need `role="tablist"` / `role="tab"` / `role="tabpanel"` with `aria-selected`
   and `aria-controls`, and non-selected panels get `hidden`.
5. An invalid field carries `aria-invalid="true"` **and** `aria-describedby` pointing at
   the message element.
6. Icon-only buttons (hamburger, kebab, meatball, bento, FAB) require `aria-label`.
7. Honor `prefers-reduced-motion: reduce` for every spinner, shimmer, and transition.
8. If the page has a **sticky** header or toolbar, every jump-link target needs
   `scroll-margin-top` at least as large as that bar, or the heading lands underneath it
   and the reader sees the wrong place. Measure the bar at runtime and set the value as a
   custom property rather than hard-coding a rem guess - the bar's height changes when its
   contents wrap. Do not use `requestAnimationFrame` to throttle the accompanying
   current-section indicator: rAF is throttled to zero in background tabs, which stalls it
   silently. Use a timer throttle.

## 8. Operational checklist

Before emitting UI markup:

- [ ] Every component in the request is named unambiguously. No bare "dropdown," "modal,"
      "stepper," or "badge" survives into the implementation.
- [ ] For each control, you chose native HTML if section 6 says the browser has it.
- [ ] Dialogs are `<dialog>`; modality is `showModal()` vs `show()`, not a separate
      component.
- [ ] Accordions use `<details name>`; you did not import one.
- [ ] Menus, tooltips, and hover cards use the `popover` attribute, with JS positioning
      or CSS anchor positioning.
- [ ] Tag vs filter chip decided by whether it is pressable.
- [ ] Checkbox vs switch decided by whether the change applies immediately.
- [ ] Every accessibility invariant in section 7 is satisfied.
- [ ] Page-level work is described in block names from section 3.5.
- [ ] Any component library you added is justified by theming or consistency, not by
      capability.

## 9. Self-test

**Answer these by producing the term, not by recognizing it.** The human version of this
post ships two graded exercises on purpose: a multiple-choice quiz (recognition) and a
drill that stages an unlabeled specimen and requires the reader to type its name
(recall). The split follows Robert and Elizabeth Bjork's distinction between *fluency
strength* and *storage strength*: recognizing a name you just read scores high on fluency
and adds little to storage, and Roediger & Karpicke (2006) measured that retrieval
practice beats restudying for retention even though it feels worse. The operational
translation for you: **the skill that matters is emitting the right term unprompted**,
because at generation time nobody hands you four options either.

Answer before reading the answers.

1. A field must accept one of three known deploy targets **or** a new value the user
   types. Which control?
2. What is the difference between `<dialog>.show()` and `<dialog>.showModal()`?
3. Three dots arranged horizontally - which menu icon?
4. A ticket says "add a stepper." What do you ask?
5. The setting applies the moment it is flipped, with no Save button. Checkbox or switch?
6. You need an overlay containing a heading, a paragraph, and a link. Tooltip or popover?
7. How do you build an accordion where opening one panel closes the others, with no
   JavaScript?
8. Is "modal" a component?

**Answers.**
1. A **combo box**: `<input list="targets">` plus `<datalist id="targets">`. A dropdown
   list would reject the typed value.
2. `show()` is non-modal - no backdrop, page stays interactive. `showModal()` puts the
   dialog in the top layer, renders `::backdrop`, makes the rest inert, and enables
   Escape-to-close. Same element either way.
3. The **meatball** menu. Vertical dots are the kebab; three lines are the hamburger; a
   grid is the bento.
4. Whether they mean the **multi-step wizard** (Component Gallery's "Stepper") or the
   **numeric increment control** (NN/g's "Input Stepper"). The two share no markup.
5. A **toggle switch**. Checkboxes collect a value for later submission.
6. A **popover**. Tooltips are text-only; focusable content inside `role="tooltip"` is
   unreachable.
7. `<details name="group">` on each panel, with the same `name` value. The browser
   enforces exclusivity.
8. **No.** It is a mode of a dialog. Name the component `Dialog` and take modality as a
   prop.

## 10. What is still open

The vocabulary does not settle arguments by existing. NN/g published 61 canonical names
in February 2025, and the 95 design systems indexed by The Component Gallery still
disagree with each other and with NN/g - "stepper" continues to mean two different
things. The author has not yet adopted a house glossary across his own repositories; the
stated next step is a short names file per project so agent and human read from the same
list. If you are generating code for a repository that has such a file, **it outranks
this document.**
