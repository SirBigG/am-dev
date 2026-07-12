# AGENTS.md

Guidance for Codex and other coding agents working in the AgroMega forum repository.

## Project Context

This repository is the existing `forum_instance` Django application for **Спільнота AgroMega**. It is built on `django-spirit` and normally runs from the parent `am-dev` integration workspace.

Local integration:

- Compose file: `../docker-compose.yml`
- Forum service: `forum_instance`
- Main AgroMega/OIDC service: `core`
- Database service: `db`
- Nginx exposes the integrated site on local port `8000`
- Public community routes are served only below `/community/`; `/forum/` is a legacy redirect.

Do not create a replacement forum service, move forum-owned content into `am-core`, or reintroduce the retired `am-front` project.

## Architecture Invariants

- `forum_instance` and `am-core` remain separate Django applications with separate databases and dependencies.
- AgroMega is the OAuth/OIDC identity provider; the forum uses the existing OIDC integration and synchronized local Spirit users.
- Preserve `/community` in generated URLs, redirects, login/logout `next` values, OIDC callbacks, canonical and sitemap URLs, forms, pagination, AJAX, static assets, and media assets.
- Keep public community and publication routes below `/community/`; do not add public top-level `/publications/` routes.
- Do not create Django foreign keys across the forum and main databases.
- Compose around Spirit through local apps, templates, services, and overrides. Do not edit installed Spirit source or add fields to Spirit-owned models.
- Publication-specific models, lifecycle, permissions, routes, templates, rendering, and SEO belong to the AgroMega-owned `community` app.
- Each publication has one canonical page below `/community/publications/`; its backing Spirit topic must not create an indexable duplicate.
- Draft, review, rejected, private, removed, and archived content must not leak into anonymous discovery, search, feeds, notifications, metadata, or sitemaps.

## Repository Ownership

- Django project configuration: `agromega_forum/`
- AgroMega publication/community domain: `community/`
- OIDC and forum integration: `forum_sso/`
- Spirit and community template overrides: `templates/`
- Frontend source and build configuration: `frontend/`
- Forum-owned static files: their owning Django app under `static/`
- Durable forum knowledge, decisions, plans, and results: `docs/`

Keep main-site navigation, main-site domain behavior, and main-site static assets in sibling `../am-core`. When a change crosses repositories, work from the parent workspace and keep each artifact with its owning project.

## Dependency And Frontend Workflow

Python dependencies remain independently managed through:

- `requirements.in`
- `requirements.txt`
- `constraints.txt`

Frontend dependencies use `frontend/package.json` and `frontend/package-lock.json`. Keep editable frontend sources in `frontend/src/` and committed build outputs only at the existing application-owned static paths required by deployment.

Do not commit `frontend/node_modules/`, secrets, tokens, OAuth client secrets, cookies, uploaded test media, or local environment files.

The legacy Spirit/Mistune rendering stack is a known architecture and security risk. Before expanding long-form publication rendering, follow the recorded decision process under `docs/engineering/decisions/` and add security regression coverage.

## Documentation Layout

This repository treats `docs/` as the durable forum knowledge base for people and agents.

Before meaningful implementation work, read:

- `docs/README.md` for the documentation workflow;
- relevant notes under `docs/business/` for product language and community rules;
- `docs/engineering/decisions/` for architecture and security decisions;
- `docs/work/plans/` for the active implementation plan;
- `docs/work/results/` for prior evidence, verification, and remaining risks.

Use:

- `docs/business/` for community product rules, moderation policy, lifecycle language, and content operations;
- `docs/engineering/` for technical investigations, architecture, security, dependencies, and decisions;
- `docs/work/plans/` for dated implementation plans;
- `docs/work/results/` for dated audits, execution evidence, verification, rollout notes, and follow-ups.

Planning is required before implementation when work affects product behavior, domain rules, architecture, dependencies, data, security, permissions, routing, or multi-step workflows. Small mechanical fixes such as typos or formatting-only changes do not require a full plan.

Update the durable knowledge base when implementation establishes new community rules, lifecycle states, moderation policy, renderer/security choices, canonical behavior, proxy invariants, or operational recovery procedures.

## Current Product Direction

The product name is **Спільнота AgroMega** with two distinct experiences:

- **Публікації** — durable authored guides, expert material, editorial content, and personal experience with explicit publication workflow;
- **Обговорення** — Spirit-backed topics and replies using the normal discussion workflow.

The current UX implementation plan is:

- `docs/work/plans/2026-07-11-forum-mobile-first-ux-remediation.md`

Start implementation with its Slice 0 regression safety and inventory. Record evidence under `docs/work/results/` as each slice is completed.

## Verification

Prefer the integrated Docker Compose environment from the parent workspace because routing, OIDC, static/media paths, and proxy-prefix behavior depend on multiple services.

Useful commands from the parent `am-dev` directory:

```bash
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml exec forum_instance python manage.py test
docker compose -f docker-compose.yml exec forum_instance python manage.py check
```

When available from `am-core`, the integration shortcut is:

```bash
just forum-test
```

Verification should be proportional to risk and include:

- Django unit and authorization tests;
- exact-one-`/community` prefix regression tests and `/forum/` compatibility redirects;
- anonymous and authenticated browser journeys through Nginx;
- mobile, tablet, and desktop responsive checks;
- keyboard, focus, labels, landmarks, contrast, and zoom checks;
- publication visibility, canonical, rendering, upload, and security tests where relevant.

## Working Rules

- Preserve unrelated user changes and generated local environment files.
- Read the active plan before changing community behavior or presentation.
- Keep changes reviewable by vertical slice; avoid combining broad visual rewrites with unresolved lifecycle or security decisions.
- Reuse Spirit behavior where appropriate while keeping AgroMega product rules in owned code.
- Use Ukrainian for public product language and accessible labels unless a domain term is intentionally untranslated.
- Keep accessibility and mobile behavior part of acceptance criteria, not post-implementation cleanup.
