# AGENTS.md

Guidance for Codex and other coding agents working across the local AgroMega development workspace.

## Workspace Layout

This `am-dev` directory is an integration workspace containing separately owned projects and deployment configuration:

- `am-core/` — main AgroMega Django backend and API; OAuth/OIDC provider; main navigation and root SEO surfaces.
- `forum_instance/` — separate Django application built on `django-spirit`; owns forum/community data, templates, static assets, and forum-specific behavior.
- `nginx/` — local reverse-proxy configuration.
- `docker-compose.yml` — local multi-service environment.
- `forum_instance` is not a new service to create. Extend the existing sibling project when forum/community work is requested.
- The retired `am-front` project/service must not be reintroduced.

Read and follow the nearest project-level `AGENTS.md` before changing files inside a child project. More specific instructions override this file.

## Integration Invariants

- The main application and forum remain separate Django applications with separate databases and dependency sets.
- AgroMega is the OAuth/OIDC identity provider; `forum_instance` uses the existing OIDC integration and local synchronized Spirit user records.
- All public forum/community/publication pages stay below the main host's `/forum/` path.
- Nginx redirects `/forum` to `/forum/`, proxies `/forum/` to `forum_instance`, and owns `/forum/static/` and `/forum/media/` routing.
- Preserve `/forum` in externally generated URLs, redirects, login/logout `next` values, OIDC callbacks, form actions, pagination, AJAX, canonical URLs, sitemap URLs, static assets, and media assets.
- Do not introduce public top-level `/community/` or `/publications/` routes in `am-core` for forum-owned content.
- Keep cross-service relationships explicit. Do not create Django foreign keys between the main and forum databases.

## Community And Publication Direction

The planned product name is **Спільнота AgroMega**. It will combine redesigned discussion experiences with moderated article-like publications.

- Compose around Spirit rather than modifying installed Spirit source or adding fields to Spirit-owned models.
- Put publication-specific models, lifecycle, permissions, routes, templates, and SEO behavior in an AgroMega-owned Django app inside the existing `forum_instance` project.
- Continue using Spirit where appropriate for topics, replies/comments, users, likes, notifications, flags, and existing moderation behavior.
- Give each publication one canonical page under `/forum/publications/.../`; prevent an indexable duplicate generic topic page.
- Keep draft, review, rejected, private, removed, and archived content out of anonymous discovery, search, feeds, and sitemaps.
- Treat the existing Spirit/Mistune dependency risk as a required architecture and security decision before production publication launch.

The durable implementation plan is:

- `am-core/docs/work/plans/2026-07-11-community-publications-and-forum-redesign.md`

Start with the plan's Phase 0 investigation. Record required decisions before implementation and update the plan/result artifacts as work progresses.

## Working Rules

- Use the root workspace when work crosses `am-core`, `forum_instance`, Nginx, or Compose.
- Keep dependency changes isolated to the project that owns them.
- Main app dependencies use uv via `am-core/pyproject.toml` and `am-core/uv.lock`.
- Forum dependencies are managed separately in `forum_instance/requirements.in`, `requirements.txt`, and `constraints.txt` until that project deliberately adopts another workflow.
- Keep main static sources in `am-core/frontend/src/`; keep forum static sources and overrides in `forum_instance`.
- Prefer Docker Compose verification from this workspace because both applications depend on the integrated environment.
- Preserve unrelated user changes and generated local environment files.
- Do not add secrets, tokens, OAuth client secrets, cookies, or production credentials to tracked files.

Useful commands from `am-core/` include:

```bash
just ps
just test
just forum-test
just flake
just migrate
just static-build
just collectstatic
```

For direct integrated commands, use the root Compose file:

```bash
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml exec forum_instance python manage.py test
docker compose -f docker-compose.yml exec core python manage.py test
```

## Planning And Documentation

- Follow `am-core/docs/README.md` for durable documentation and planning.
- Meaningful cross-app changes require a dated plan under `am-core/docs/work/plans/` unless an equivalent plan already exists.
- Write execution evidence, verification, rollout notes, and remaining risks under `am-core/docs/work/results/`.
- Update business and engineering documentation when implementation establishes new community rules, lifecycle states, moderation policy, security decisions, or proxy invariants.
