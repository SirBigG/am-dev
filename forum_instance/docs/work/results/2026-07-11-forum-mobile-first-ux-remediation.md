# Result: Mobile-First Forum UX Remediation

- Date: 2026-07-11
- Plan: `../plans/2026-07-11-forum-mobile-first-ux-remediation.md`
- Implementation state: completed and verified for the approved launch scope
- Environment: local integrated Docker Compose stack through Nginx at `http://localhost:8000/forum/`

## Approved Decisions Implemented

- The forum now owns an independent design-token and component layer. It visually aligns with the current main site without importing runtime ownership from `am-core`.
- One **Створити** menu offers two distinct content paths: publication and discussion.
- Community tabs are sticky; phones also receive a bottom app-style navigation bar.
- Tags are optional so an empty release taxonomy cannot block publication. Publication type is explicit in the form.
- Publication cards and forms have no cover or fallback-cover surface. Body images use the editor upload widget.
- Publication-backed topics are excluded from home discussion discovery, active discussions, category lists, and public forum search. Direct topic URLs redirect to the canonical publication URL.
- Authors can edit their own published publications directly during the low-activity launch phase.

## Implemented Slices

### Routing and safety

- Fixed already-prefixed auth return paths so `/forum/...` never becomes `/forum/forum/...`.
- Added exact-prefix regression coverage.
- Applied Spirit public/private/category visibility rules to home discussions and canonical publication detail.
- Excluded publication topic IDs before search pagination.
- Preserved query strings on canonical redirects and retained Spirit-compatible comment anchors on the canonical publication page.

### Responsive shell and accessibility foundations

- Added one shared `main` landmark, skip link, visible focus style, current-page state, Ukrainian accessible icon names, reduced-motion handling, and minimum critical control sizes.
- Added a compact search disclosure for phone/tablet layouts.
- Standardized content width, reading width, spacing, color, radius, shadow, form, card, chip, status, and control tokens.
- Restricted the editor bundle to publication authoring routes.

### Discovery and reading

- Rebuilt the community home with an H1, product explanation, separate publication/discussion sections, clear creation paths, and useful empty states.
- Rebuilt publication listing, filtering, result count, type metadata, cards, and no-result state without cover placeholders.
- Rebuilt publication article hierarchy, author/update information, disclosure, readable body, comments, reply composer, reporting/permalink actions, and author edit action.
- Rebuilt active/category discussion lists and localized follow/create controls while retaining Spirit behavior.

### Authoring and secondary surfaces

- Exposed publication kind, made taxonomy optional, and added truthful unsaved/saving status plus unload protection.
- Added an accessible publish dialog with Escape/return focus behavior and form error alerting.
- Reworked author dashboard and review queue presentation.
- Added community search, notification, profile, 403, and 404 presentation with consistent headings and landmarks.

## Verification Evidence

### Automated application checks

Commands executed in the integrated forum container:

```text
npm run build
docker compose -f docker-compose.yml exec forum_instance python manage.py collectstatic --noinput
docker compose -f docker-compose.yml exec forum_instance python manage.py check
docker compose -f docker-compose.yml exec forum_instance python manage.py test
git diff --check
```

Final results:

- frontend editor build: passed;
- Django system check: passed with zero issues;
- complete Django suite after continuation fixes: 46/46 passed;
- pre-checker complete suite: 42/42 passed;
- checker-repair targeted suite: 45/45 passed;
- whitespace check: passed;
- static collection: passed.

New regression coverage includes:

- exactly one external `/forum` prefix during SSO return;
- anonymous private-topic exclusion on community home;
- publication-topic exclusion from active/category discovery;
- publication search exclusion before pagination;
- canonical publication comment anchors and reply rendering;
- optional empty taxonomy and explicit publication kind;
- one `main` and one H1 on core public routes.

### Responsive browser matrix

The rendered integrated site was inspected through Nginx at these explicit viewports:

| Width × height | Overflow | Header | Mobile bottom nav | Main/H1 | Critical targets |
|---|---:|---:|---|---:|---:|
| 320 × 800 | none | 64 px | visible | 1 / 1 | none below 44 px |
| 360 × 800 | none | 64 px | visible | 1 / 1 | none below 44 px |
| 390 × 844 | none | 64 px | visible | 1 / 1 | none below 44 px |
| 430 × 900 | none | 64 px | visible | 1 / 1 | none below 44 px |
| 768 × 1024 | none | 64 px | hidden | 1 / 1 | none below 44 px |
| 1024 × 900 | none | 68 px | hidden | 1 / 1 | none below 44 px |
| 1280 × 900 | none | 68 px | hidden | 1 / 1 | none below 44 px |
| 1440 × 1000 | none | 68 px | hidden | 1 / 1 | none below 44 px |

Routes inspected at mobile and representative larger widths:

- community home;
- publication list, detail, create, and author dashboard;
- active discussion list and discussion detail/reply;
- search results;
- notifications;
- user profile.

The automated DOM audit on those routes found:

- no unnamed visible link/button/submit controls;
- exactly one `main` and one H1 per inspected route;
- no document width greater than the viewport;
- no critical button/icon/navigation target below 44 × 44 px.

Final mobile and desktop screenshots were visually inspected in the browser session after static collection. They are not committed because environment content contains local test users and test publications.

### Recognized automated accessibility scan

Pa11y 9.0.1 was executed as a temporary verification tool without adding a project dependency. The final mobile run used a 390 × 844 viewport with both the axe 4.10 and HTML_CodeSniffer WCAG 2 AA runners. The same core routes were also checked by the desktop WCAG2AA run.

Final scanned routes:

```text
/forum/
/forum/publications/
/forum/publications/argargargargag/
/forum/topic/active/
/forum/search/?q=Topic
```

Final result for every route: exit code `0`, JSON result `[]`. There were zero critical, serious, or WCAG2AA error findings. The first scan found legacy link contrast and prohibited ARIA attributes; those findings were corrected before the clean final scan.

### Manual accessibility checks

- DOM and accessible-tree inspection confirmed the skip link, landmark hierarchy, heading hierarchy, named search/create/navigation controls, `aria-current`, dialog labelling, authoring field labels, and comment/reply structure.
- Mobile navigation remains usable without hover; desktop hover is additive.
- Focus rules use a three-pixel high-contrast focus ring and controls remain native keyboard-focusable.
- Reduced-motion media handling is present.
- The computed visible tab order begins with the skip link, then brand, mobile search, notification/account, section navigation, and page actions. Closed disclosure content is removed from the visible tab order.
- The authoring publish dialog moves focus to its labelled close button, closes with Escape, and returns focus to the open-publish button; this journey was exercised in the rendered browser.

### Nginx, OIDC, and canonical smoke evidence

- All browser checks used the Nginx `/forum/` route, not direct container URLs.
- SSO tests cover unprefixed, already-prefixed, external, same-origin-outside-forum, authenticated, and anonymous returns.
- Publication topic requests resolve through the owned guard before Spirit; canonical redirects and comment anchors have regression coverage.
- Static CSS and editor bundles were collected and served successfully through `/forum/static/`.

## Performance Budget And Evidence

The plan's launch budgets are adopted:

- LCP ≤ 2.5 seconds;
- CLS ≤ 0.1;
- INP ≤ 200 ms.

Performance-oriented changes in this delivery include route-only editor loading, no publication cover/fallback assets, reserved editor/image behavior, reduced decorative UI, and no new runtime framework dependency. Production-like Core Web Vitals were not claimed from localhost because that would be misleading; measure these budgets in staging or production telemetry before release.

## Checker Repair Cycle

The first checker review returned `FAIL` for private-topic leakage, missing canonical comments, post-pagination search filtering, and absent evidence. The focused repair cycle addressed all four:

- home uses Spirit `visible().global_()` semantics and has a private-topic regression test;
- canonical publication detail uses Spirit comment pagination, exact `cN` anchors, replies, reporting/permalinks, and the standard reply form;
- public search excludes publication topic IDs before pagination;
- this artifact records test, responsive, accessibility, proxy, and performance evidence and limitations.

## Checker And Continuation Result

The original final checker returned `FAIL` after the single permitted repair cycle.

Resolved critical findings:

- private/restricted topics no longer leak on the anonymous home feed;
- the canonical publication page now provides Spirit-compatible comments, anchors, reply, reporting, and permalink behavior.

Its two remaining completion blockers were subsequently resolved in the active-goal continuation:

1. Public search now mutates only the `YTPage.object_list`, preserving the page number, page range, next/previous behavior, and paginator metadata. A real multi-page filtered-result regression test verifies the wrapper and navigation metadata.
2. Pa11y 9.0.1 with both axe and HTML_CodeSniffer now reports zero errors on the core mobile matrix; desktop WCAG2AA scans are also clean. Tab order and the authoring dialog Escape/return-focus journey are recorded above.

The independent completion checker returned `PASS` after these continuation fixes. It confirmed that search pagination metadata is preserved, the accessibility evidence satisfies the plan gate, earlier private-topic and canonical-comment repairs remain correct, and no new critical correctness, routing, security, or accessibility blocker exists.

## Known Non-Blocking Follow-ups

- Add publication pagination, sort, and type filtering when the catalog grows beyond the initial launch volume.
- Constrain rendered body images to owned media if remote-image hotlink/privacy policy becomes strict; current rendering sanitizes markup but can display safe external HTTP(S) images.
- Complete a screen-reader-specific pass in target browsers before production release.
- Capture production-like Core Web Vitals in staging or telemetry.
- Continue Ukrainian localization of low-traffic Spirit administrative and legacy surfaces.
- `frontend/node_modules/` remains a local untracked build directory and must not be committed.
