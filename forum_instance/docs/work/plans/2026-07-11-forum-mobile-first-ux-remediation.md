# Plan: Mobile-First Forum UX Remediation

- Date: 2026-07-11
- Status: Completed
- Owner: AgroMega product and engineering
- Parent plan: `2026-07-11-community-publications-and-forum-redesign.md`
- Audit target: current local integrated build at `/forum/`

## Outcome

Turn the first version of **Спільнота AgroMega** into a coherent, trustworthy, mobile-first experience for reading, discovery, discussion, publication authoring, and moderation. The interface must remain efficient on phones, scale deliberately to tablets, and use desktop space without becoming sparse or fragmented.

This is a UX remediation and implementation plan, not authorization to replace Spirit, move forum routes out of `/forum/`, or redesign the publication domain model.

## Audit Method And Coverage

The rendered integrated application was reviewed at representative viewports:

- mobile: 390 × 844;
- tablet: 768 × 1024;
- desktop: 1440 × 1000.

Reviewed journeys:

- community home;
- publication list and filtering;
- publication detail;
- authenticated publication-create entry;
- active discussion list;
- discussion detail and reply composer;
- shared header, search, account controls, section navigation, tags, actions, and content widths.

The implementation phase must expand the matrix to 320, 360, 390, 430, 768, 1024, 1280, and 1440 px and include authenticated, anonymous, empty, loading, error, long-content, and moderation states.

## Executive Findings

### P0 — Functional and routing defects

1. **Publication creation can generate a doubled prefix.** Opening the authenticated publication-create route redirected to `/forum/forum/publications/new/` and produced a 404. Audit every login/create redirect and `next` construction; route generation must preserve exactly one `/forum` prefix.
2. **Responsive behavior is largely visual CSS, not a verified journey.** Pages avoid broad horizontal overflow at the tested widths, but core creation, account, notification, navigation, and reply flows have not been proven end to end across breakpoints.
3. **Publication-backed topics remain visible in the generic active-topic list.** This creates product confusion and risks duplicate navigation/indexing. Apply the parent plan's canonical publication routing policy before polishing those cards.

### P1 — Mobile usability and accessibility

1. **The mobile header is too tall and search dominates.** At 390 px it occupies about 154 px before the section tabs. Brand, sign-in/account, search, and primary navigation compete for the first screen.
2. **Navigation is duplicated.** The shared section tabs and the home feed tabs repeat “Публікації” and “Обговорення,” costing vertical space and weakening location awareness.
3. **Active state is incomplete.** Shared section navigation does not expose a reliable current-page state (`aria-current="page"` and a persistent visual state).
4. **Touch targets are frequently below 44 × 44 px.** Search, notification, account, chips, cards' text links, breadcrumbs, discussion actions, and submit controls commonly measure 15–43 px high.
5. **Icon-only actions have poor accessible names.** The search button and legacy Spirit toolbar/actions expose glyphs such as ``, ``, or formatting icons instead of clear Ukrainian labels.
6. **Legacy discussion pages lack consistent landmarks.** Active-topic and topic-detail pages did not expose a `main` landmark, while publication pages did.
7. **Mixed language remains visible.** Examples include “Notify Me” and the “General” category in an otherwise Ukrainian experience.
8. **Horizontal chip rows hide content.** Popular-topic filters scroll horizontally without a strong affordance, selected-filter summary, or “more filters” model.
9. **Mobile content actions are scattered.** Starting a publication appears late in the home sidebar, while starting a discussion is absent from the home primary actions.

### P1 — Information architecture and product clarity

1. **The home page has no H1 or positioning statement.** It begins with tertiary feed tabs, so first-time visitors do not learn what the community is for.
2. **Publication and discussion content look too similar.** Both are mostly title-and-metadata rows; content type, intent, author credibility, freshness, and expected interaction are not sufficiently scannable.
3. **The two creation modes are disconnected.** “Почати публікацію,” “Поділитися досвідом,” “Створити публікацію,” and “Створити тему” use inconsistent language and placement.
4. **Discussion discovery remains Spirit-centric.** “Усі категорії,” unread concepts, terse counters, and category labels are exposed without onboarding or a clear content hierarchy.
5. **Empty and low-quality seed content weakens trust.** Test titles such as “erer” and “argargargargag” make layout evaluation misleading and would make a public first impression look unfinished.

### P2 — Visual system and responsive composition

1. **Two visual systems coexist.** New publication/community pages use large rounded cards and modern spacing, while Spirit lists and topic pages retain dense legacy typography and controls.
2. **Desktop containers are inconsistent.** Home uses 1080 px while publication and legacy article surfaces use 1120 px; padding and vertical rhythm shift between routes.
3. **Tablet is treated mostly as collapsed desktop.** At 768 px the header still consumes 96 px, the sidebar simply moves below content, and no tablet-specific navigation or two-pane opportunities are defined.
4. **Home publication stories have no strong visual hook.** Covers, type labels, avatars, reading time, reply/activity signals, and editorial badges are absent.
5. **Publication detail lacks a complete article frame.** Reading width is reasonable, but author block, update semantics, share actions, comment transition, related content, and trust/disclosure elements need a deliberate hierarchy.
6. **Typography and spacing are defined ad hoc.** Repeated one-off sizes, colors, radii, and breakpoints make future Spirit overrides fragile.

## Product Model For The Interface

Use three stable levels:

1. **Global AgroMega shell:** brand, return to main site, global/account actions.
2. **Community navigation:** Огляд, Публікації, Обговорення; authenticated secondary items belong in the account menu or contextual dashboards, not the primary tab row.
3. **Contextual navigation:** publication filters, discussion categories, author dashboard states, or moderation filters.

Use one content-creation entry point labeled **Створити**. On activation, offer two clearly described choices:

- **Публікацію** — a structured article or practical guide;
- **Обговорення** — a question, short topic, or conversation.

Direct contextual CTAs may remain (“Написати публікацію”, “Почати обговорення”) when their destination is unambiguous.

## Responsive UX Specification

### Mobile: 320–599 px

- Compact 56–64 px top bar with brand, search trigger, and account/menu trigger.
- Search opens an inline full-width row or accessible dialog; it must not permanently consume a second header row.
- Community navigation uses three equal or horizontally scrollable tabs with visible selected state; do not duplicate it inside the home feed.
- One-column content with 16 px gutters and no fixed-width children.
- Primary actions are full-width or at least 44 px high; card titles may use a larger linked surface.
- Filters use a single-row summary plus an accessible filter sheet/disclosure when tags exceed the available width.
- Sidebar content becomes intentionally ordered sections, not a desktop sidebar appended blindly.
- Discussion metadata collapses to the signals users need: category/type, last activity, replies, and unread state.
- Reply composer uses a simple default textarea and an expandable formatting toolbar with named controls.
- Sticky actions are allowed only where they do not cover content, browser UI, keyboard, or form errors.

### Tablet: 600–1023 px

- Keep a compact single-row shell; search may be inline when space permits.
- Use a 12-column grid with 24 px gutters.
- Listing cards may use two columns when content quality supports it; discussions stay a readable single list.
- Contextual filters can use a compact left rail or top bar, but never both.
- Authoring canvas targets 680–760 px with persistent save status and non-obscuring toolbar.
- Side content may become a 4-column rail only when the primary reading column remains at least 8 columns.

### Desktop: 1024 px and above

- Standardize the shell and content grid at one documented maximum width (recommend 1120–1200 px).
- Use a primary content column plus a 280–320 px contextual rail where the rail adds real value.
- Article body stays near 68–75 characters per line even when the outer frame is wider.
- Make hover additive only; every action must remain visible/focusable without hover.
- Use desktop space for richer metadata, relevant recommendations, and moderation context—not oversized empty margins.

## Component And Page Work

### 1. Foundation and shared shell

- Define semantic tokens for color, typography, spacing, radius, shadow, motion, control heights, focus rings, content widths, and breakpoints.
- Create a small AgroMega-owned component layer around Spirit templates: page container, stack/cluster utilities, buttons, icon buttons, tabs, chips, cards, metadata rows, avatars, alerts, empty states, pagination, and form fields.
- Standardize `:focus-visible`, hover, active, disabled, selected, loading, and validation states.
- Add a skip link, `main` landmark, unique H1, Ukrainian accessible names, and `aria-current` across every public surface.
- Replace raw Font Awesome glyph announcements with hidden decorative icons plus explicit labels.
- Respect `prefers-reduced-motion` and maintain WCAG 2.2 AA contrast.

### 2. Header and navigation

- Reduce mobile header height and move full-site links into an accessible menu below 900 px.
- Make search a labeled control with clear, submit, no-results, and recent-query behavior.
- Consolidate community navigation; move “Мої матеріали,” unread, notifications, settings, and private topics into logically named authenticated destinations.
- Give notification/account controls 44 px targets and clear badges/labels.
- Preserve OIDC return paths with exactly one `/forum` prefix and test anonymous/authenticated transitions.

### 3. Community home

- Add an H1, short Ukrainian value proposition, and two primary creation choices.
- Replace duplicate feed tabs with clearly titled sections: featured/recent publications and active discussions.
- Give publication cards type, cover/placeholder, author identity, date/read time, excerpt, and tags.
- Give discussion rows category, author, reply count, latest activity, unread/pinned/locked state, and a generous linked surface.
- Add useful empty states and curated starter prompts for a low-activity community.
- Move popular tags and onboarding into purposeful mobile sections; do not render a desktop rail verbatim at the bottom.

### 4. Publication listing

- Keep one H1 and explanatory lead; make the CTA terminology consistent.
- Combine query, tag, type, and sort into one filter model with removable active-filter chips and result count.
- Use one column on mobile, two on tablet, and two or three on desktop depending on cover quality.
- Specify robust cards for missing images, long Ukrainian titles, long author names, multiple tags, and zero results.
- Preserve filters through pagination and expose filter state in the URL.

### 5. Publication detail

- Build a complete article header: type, title, summary, author/avatar, published/updated dates, reading time, disclosure, and author/editor actions.
- Use responsive covers with reserved aspect ratio; avoid forced tall crops on mobile unless editorially selected.
- Keep body width readable and style headings, lists, tables, quotes, figures, captions, links, and long unbroken content.
- Add a clear transition from article to comments, comment count, reply CTA, related publications, and reporting path.
- Define sticky share/navigation only after keyboard, screen-reader, and small-screen testing.

### 6. Publication editor and author dashboard

- Fix the doubled-prefix routing defect before visual work.
- Make save status truthful: saving, saved timestamp, failed/retry, offline/unsaved warning.
- Split essential content fields from publish metadata with progressive disclosure.
- Keep title/body first; move type, summary, cover, alt text, tags, and review submission into a clear publish/review step.
- Ensure keyboard access and visible labels for every toolbar command; avoid icon-only commands.
- Preserve drafts server-side, warn before navigation with unsaved work, and restore safely.
- On mobile, keep toolbar compact and non-overlapping with the virtual keyboard.
- Dashboard cards must explain status, required next action, editorial note visibility, and permitted actions.

### 7. Discussion list and categories

- Add a page H1 and short explanation or selected-category heading.
- Replace the legacy compressed rows with accessible topic-row components.
- Separate title, category, author, replies, last contributor/activity, and state badges.
- Hide or redirect publication-backed topics according to the canonical policy.
- Make category filters usable as a disclosure on mobile and a compact rail/menu on larger screens.
- Localize all visible labels and define correct Ukrainian pluralization for replies and dates.

### 8. Discussion detail and reply

- Apply the shared article/list shell and `main` landmark.
- Visually separate the original post from replies while keeping one reading rhythm.
- Simplify action priority: reply and like primary; quote, share, report, edit, and moderation secondary.
- Replace “Notify Me” with a Ukrainian follow/unfollow control and explicit state.
- Expand tap targets and give every icon action an accessible name.
- Make pagination meaningful and avoid showing “Сторінка 1 з 1” as prominent UI.
- Use an accessible, resilient composer with clear errors, preview behavior, upload state, and submission feedback.

### 9. Search, profiles, notifications, moderation, and system states

- Use one community-search results model with clear distinction between publications and discussions.
- Redesign profile public view and account menu without duplicating main-site settings ambiguously.
- Define notification grouping, unread state, mark-read behavior, and empty/loading/error states.
- Apply the component layer to flags, admin, editor queue, permissions errors, 403/404/500, and authentication handoff screens.
- Never expose unpublished publication content in snippets, counts, notifications, or error pages.

## Implementation Sequence

### Slice 0 — Regression safety and inventory

- Add route/prefix tests for every CTA, login `next`, create/edit/submit flow, canonical topic redirect, pagination, and search/filter URL.
- Inventory every overridden Spirit template and map it to the new component/page ownership.
- Capture baseline screenshots and automated accessibility results for the route × viewport × auth matrix.
- Replace public-facing seed/test content with representative fixtures for design QA.

**Exit:** no known doubled-prefix or public canonical-route defect; baseline artifacts exist.

### Slice 1 — Tokens, accessibility primitives, and shell

- Implement tokens, containers, controls, focus states, landmarks, skip link, icon labels, header, search, account menu, and community navigation.
- Keep behavior unchanged except for the routing/accessibility fixes.

**Exit:** shared shell passes keyboard and 320–1440 px smoke testing; primary targets meet 44 px guidance.

### Slice 2 — Home and discovery

- Rebuild home information hierarchy and creation choice.
- Implement publication cards, discussion rows, filters, empty states, and responsive compositions.

**Exit:** a new visitor can explain the difference between a publication and discussion and start either journey within two actions.

### Slice 3 — Reading experiences

- Redesign publication detail, discussion detail, comments, metadata, actions, pagination, and related content.
- Resolve publication-backed topic presentation/canonical behavior.

**Exit:** reading and reply journeys work with keyboard, touch, long content, and 200% zoom.

### Slice 4 — Authoring and dashboards

- Rework publication editor, discussion composer, drafts, validation, status feedback, author dashboard, and editor queue.

**Exit:** users can create, recover, submit, correct, and track content on a 360 px phone without hidden fields or ambiguous status.

### Slice 5 — Secondary surfaces and hardening

- Complete search, profile, notifications, flags, moderation/admin, auth, and system states.
- Run cross-browser, performance, accessibility, localization, and integrated proxy verification.

**Exit:** no high-severity UX/accessibility defects remain in the agreed matrix.

## Acceptance Criteria

### Navigation and comprehension

- Every public page has one H1, one `main`, a descriptive title, and clear current location.
- Users can reach home, publications, discussions, search, create, and account destinations without relying on horizontal scrolling or hidden hover behavior.
- A first-time user can distinguish publication versus discussion from labels and card treatment alone.

### Responsive quality

- No unintended horizontal page overflow at 320–1440 px or 200% zoom.
- Primary controls and all icon-only controls are at least 44 × 44 CSS px; compact inline text links have adequate spacing and an equivalent larger card/action target where needed.
- Virtual keyboard, sticky elements, and toolbars do not cover focused fields, validation, or submit controls.
- Layouts remain balanced with missing images, long titles, long names, 10+ tags, and empty results.

### Accessibility

- Full journeys work by keyboard with visible focus and logical order.
- Controls have Ukrainian accessible names; decorative glyphs are hidden from assistive technology.
- Forms provide persistent labels, instructions, associated errors, error summary, and focus management.
- Color contrast meets WCAG 2.2 AA and meaning never depends only on color.
- Automated checks report zero critical/serious violations; manual checks cover landmarks, headings, menus/dialogs, announcements, zoom, and reduced motion.

### Product and technical integrity

- All externally generated forum URLs contain exactly one `/forum` prefix.
- Publication drafts/review states never leak through UI, search, notifications, feeds, or metadata.
- Publication-backed topic URLs follow the canonical policy without broken comment or notification links.
- Existing Spirit capabilities remain available or have an explicitly approved replacement.

### Performance

- Establish mobile budgets before implementation; recommended targets on representative content are LCP ≤ 2.5 s, CLS ≤ 0.1, and INP ≤ 200 ms in production-like measurement.
- Covers reserve space, use responsive sources, lazy-load below the fold, and avoid shipping desktop-sized assets to phones.
- The editor bundle loads only on authoring routes unless a measured reason requires otherwise.

## Verification Matrix

For each high-value route test anonymous, author, unrelated authenticated user, editor/moderator, and administrator where applicable.

High-value routes:

- home;
- publication list, filtered list, no results, detail, draft preview, create/edit, dashboard, review queue;
- discussion list/category, topic detail, create, reply/edit;
- search results;
- profile, notifications, login/logout handoff;
- 403, 404, validation error, upload failure, and offline/failed-save state.

Verification layers:

1. Django route, authorization, and prefix regression tests.
2. Template/component tests for landmarks, H1, labels, current state, and unpublished-content exclusion.
3. Browser journey tests at mobile and desktop breakpoints.
4. Screenshot regression at mobile, tablet, and desktop.
5. Automated accessibility scan plus manual keyboard and screen-reader-oriented inspection.
6. Production-like Nginx/Compose smoke test for routes, assets, media, OIDC return paths, and canonical URLs.

## Delivery Guardrails

- Work inside `forum_instance` for forum-owned templates, static assets, behavior, and tests; update `am-core` only for main-site navigation/identity touchpoints and durable docs.
- Do not modify installed Spirit source. Override or wrap templates and behavior in AgroMega-owned code.
- Do not introduce top-level `/community/` or `/publications/` public routes.
- Do not mix a visual rewrite with unresolved publication lifecycle/security decisions.
- Keep changes reviewable by vertical slice and preserve unrelated working-tree changes.
- Record implementation evidence and remaining risks in `docs/work/results/` after each slice.

## Approved Product Decisions

1. The forum owns an independent design system. Its initial colors, typography, lines, cards, and Bootstrap-compatible patterns may be copied from the main site, but future forum design can diverge without coupling repositories.
2. Use one **“Створити”** entry point offering two distinct choices: a structured publication or a discussion.
3. Use sticky community section tabs below a compact non-sticky header and add app-style community navigation at the bottom on phones.
4. The forum owns category and tag taxonomy. Production taxonomy will be populated from scratch by the owner at release, so an empty taxonomy must not block authoring.
5. Publications have no cover field or fallback cover. Images appear only when authors add them to the body through the editor image widget.
6. Publication-backed Spirit topics are excluded from ordinary discussion discovery and their direct topic URLs redirect to the canonical publication page.
7. During the low-activity launch phase, authors may edit their own published publications directly. Moderation and re-review policy will be reconsidered when activity grows.
