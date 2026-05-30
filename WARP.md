# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is the personal portfolio website of Nick Ceglia (Nicholas Ceglia, PhD), an ML Research Scientist / Principal Computational Biologist. It is hosted on GitHub Pages at nceglia.github.io.

The site is a **multi-page static HTML site** with a minimal, black-on-white aesthetic and light Monokai-inspired color accents. Each page is a self-contained HTML file that links one shared stylesheet — there is no build step or templating required to preview or edit the content.

## Architecture

### Pages
Each page is standalone HTML and lives at a clean URL via folder + `index.html`:

- **`index.html`** — Home / hero (name, title, tagline, social links)
- **`research/index.html`** — Core Research Areas (`/research/`)
- **`projects/index.html`** — Featured Projects (`/projects/`)
- **`publications/index.html`** — Selected Publications (`/publications/`)
- **`experience/index.html`** — Experience timeline (`/experience/`)

Every page links the shared stylesheet with `<link rel="stylesheet" href="/css/site.css">` and contains its own copy of the `<nav>` and `<footer>` markup.

### Shared stylesheet
- **`css/site.css`** — ALL site styling lives here (design tokens, nav, hero, cards, timeline, footer, responsive rules). Edit this one file to change the look of every page.

### Navigation
- A sticky top nav appears on every page. Because pages are plain HTML (no Jekyll includes), the nav markup is **duplicated in each page** — if you add/rename a nav link, update it in all pages.
- The current page marks its nav link with `class="... active"`, and the `<body>` carries an `accent-*` class that colors the page's section underline.

### Jekyll / Minima remnants (dormant)
`_config.yml`, `_layouts/`, `_includes/`, `_sass/`, `css/main.scss`, `feed.xml`, and the `Gemfile` remain from the original Minima-themed setup but are **no longer used by any page**. GitHub Pages still runs Jekyll on push, which harmlessly copies the standalone HTML and `css/site.css` verbatim. These files can be left alone or cleaned up later.

## Color System

Defined as CSS custom properties at the top of `css/site.css`:

- Background: `#ffffff` (white) · soft `#fafafa`
- Text: `#111111` (body) · `#000000` (headings) · `#6b7280` (muted)
- Borders: `#ececec` / `#dcdcdc`

Monokai accents — used lightly (underlines, badges, dots, hovers). Each has a bright value (decorative) and an "ink" value (readable on white):

| Accent | Bright    | Ink (text) | Page        |
|--------|-----------|------------|-------------|
| green  | `#a6e22e` | `#5f8700`  | Research    |
| blue   | `#66d9ef` | `#1683a8`  | Projects    |
| orange | `#fd971f` | `#cf6f0a`  | Publications|
| purple | `#ae81ff` | `#7c45e0`  | Experience  |

The hero name carries a four-color signature bar showing the whole palette. Keep color usage restrained — black-on-white is the base; accents stay subtle.

## Development

Because every page is standalone HTML, **no Jekyll build is needed** to preview — any static file server works:

```bash
# Serve the repo root on http://localhost:8123
python3 -m http.server 8123
```

(A `.claude/launch.json` defines this same static server for the editor's preview panel.)

To reproduce the exact GitHub Pages build (optional, requires a working Ruby/Bundler toolchain):

```bash
bundle install
bundle exec jekyll serve   # http://localhost:4000
```

## Deployment

Deployed via GitHub Pages automatically on push to the `master` branch, served from the repository root. Pages use root-absolute links (`/research/`, `/css/site.css`), which is correct for the user site at `nceglia.github.io` (no baseurl).

## Common Tasks

### Updating content
- **Home / hero**: edit `index.html`
- **Research areas**: edit `research/index.html`
- **Projects**: edit `projects/index.html`
- **Publications**: edit `publications/index.html`
- **Experience**: edit `experience/index.html`
- **Look & feel (any page)**: edit `css/site.css`

### Adding a new page
1. Create `newpage/index.html`, copy the nav/footer from an existing page, and link `/css/site.css`.
2. Give `<body>` an `accent-green|blue|orange|purple` class for its section underline color.
3. Add a `<a class="newpage" href="/newpage/">…</a>` link to the nav in **every** page, and mark it `active` on the new page.

### Troubleshooting
- Changes not showing: hard-refresh the browser (static files cache aggressively).
- Broken styling: confirm the page's `<link>` points to `/css/site.css` and the server root is the repo root.
