# AgroMega Parser Studio

Local desktop control surface for company parser sources. It is a separate sibling project and communicates with `am-core` only through the authenticated parser API.

## Phase 1

- connection profiles with tokens stored in the operating-system keyring;
- all/due source catalog and source runtime state;
- static HTML XPath dry runs and on-demand runs, including bounded next-page pagination;
- result preview and local run log;
- attempts, products, and price-history views;
- no direct database access and no arbitrary shell execution.

Browser-rendered Selenium sources are visible but not runnable in Phase 1.

## Install And Run

```bash
cd parser_studio
uv sync --extra dev
uv run agromega-parser-studio
```

Use the public base URL of the local or remote AgroMega installation, for example `http://localhost:8000/`. The token user needs `companies.use_parser_worker_api`. On-demand runs additionally require `companies.run_parser_source_on_demand`.

Connection profile metadata is stored under the platform application-data directory. Tokens are stored only through the operating-system keyring and are never written to the profile JSON.

## Tests

```bash
uv run pytest
```
