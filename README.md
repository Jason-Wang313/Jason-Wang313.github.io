# Jason Z Wang Academic Website

Personal academic website for Jason Z Wang, Computer Science student at the University of Cambridge.

Live at: [jason-wang313.github.io](https://jason-wang313.github.io)

This `codex-version` branch uses a separate homepage layout, CSS system, and canvas animation from the baseline `main` site so it can be compared cleanly against other agent versions.

## Branch safety

This Codex implementation is intended to live on the `codex-version` branch only. Do not merge or overwrite a separate `claude-version` branch without an explicit review step.

## Deployment

This is a static GitHub Pages site. It has no build step and can be served from the repository root.

Recommended deployment while keeping `main` untouched:

1. Push this branch: `git push -u origin codex-version`.
2. In **Settings > Pages**, set source to "Deploy from a branch" with branch `codex-version` and folder `/ (root)`.
3. The site deploys automatically on every push to `codex-version`.

If you later decide to use `main`, first compare `codex-version` against any `claude-version` branch and merge deliberately.

## Structure

```
index.html        — Main single-page site
cv.html           — Standalone academic CV
css/style.css     — All styles
assets/hero-world-models-warm.png — Original generated hero illustration
js/main.js        — Rotating text, navbar, scroll, fade-ins
assets/favicon.svg — Favicon placeholder
```

No build tools or dependencies required.

The deployed CV is `cv.html`, copied from the local source CV. The site must not link to the original local-only CV path.
