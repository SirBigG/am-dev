# Forum Documentation

This directory is the durable knowledge base for **Спільнота AgroMega** and the `forum_instance` repository. Forum-owned product rules, engineering decisions, plans, investigations, and implementation evidence belong here rather than in the main application's documentation.

## Structure

- `business/` — community language, actors, publication lifecycle, moderation policy, editorial rules, and operations.
- `engineering/` — architecture, integrations, security, rendering, dependencies, investigations, and technical decisions.
- `engineering/decisions/` — choices that future contributors should not need to rediscover.
- `work/plans/` — dated plans prepared before meaningful implementation.
- `work/results/` — audits, execution summaries, verification evidence, rollout notes, and remaining risks.

## Workflow

Before meaningful work:

1. Read `../AGENTS.md`.
2. Read relevant product notes under `business/`.
3. Check `engineering/decisions/` for constraints and accepted choices.
4. Read the active plan under `work/plans/`.
5. Create or update a dated plan when work changes behavior, architecture, data, security, permissions, routing, or a multi-step workflow.
6. Record execution and verification under `work/results/`.

Small mechanical fixes do not need a full plan. Durable decisions and newly established product rules must be documented in the same change that establishes them.

Prefer dated files:

- `work/plans/YYYY-MM-DD-topic.md`
- `work/results/YYYY-MM-DD-topic.md`
- `engineering/decisions/YYYY-MM-DD-topic.md`
- `engineering/security/YYYY-MM-DD-topic.md`
- `business/domains/YYYY-MM-DD-topic.md`

Never store credentials, OAuth secrets, cookies, production tokens, or personal data in documentation artifacts.

