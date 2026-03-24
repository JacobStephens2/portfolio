# stephens.page

Static personal website and portfolio hub for [Jacob Stephens](https://stephens.page).

The site is built with plain HTML, CSS, and a small amount of JavaScript. It serves as a lightweight landing page for professional links, background information, and selected projects.

## Live site

https://stephens.page

## Pages

- `index.html` - main landing page with external links
- `about.html` - background, experience, and technical profile
- `portfolio.html` - selected projects with screenshots and outbound links

## Project structure

- `screenshots/` - portfolio preview images
- `private/` - internal notes, specs, and support scripts

## Local preview

From the repository root:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Editing

This project is intentionally simple. Most updates can be made by editing the HTML files directly:

- update layout and content in `index.html`, `about.html`, and `portfolio.html`
- add or replace portfolio images in `screenshots/`
- keep analytics configuration aligned with `private/specification.md`
