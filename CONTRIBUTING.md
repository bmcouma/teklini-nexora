# Contributing

Thanks for considering a contribution to Teklini Nexora.

## Development workflow

1. Fork the repository and create a feature branch: `git checkout -b feat/short-description`
2. Follow the setup instructions in [SETUP.md](SETUP.md)
3. Make your change
4. Run the full check suite before opening a pull request:

   ```bash
   ruff check src tests
   mypy src/nexora
   pytest
   cd frontend && npm run lint && npm run build
   ```

5. Open a pull request describing what changed and why

## Commit style

Use conventional, descriptive commit messages:

```
feat: add network diagnostic agent
fix: prevent duplicate investigation loops
test: add diagnostic evaluation cases
docs: add architecture documentation
```

Avoid bundling unrelated changes into a single commit.

## Adding a new diagnostic agent

1. Add the tool(s) it needs under `src/nexora/tools/`, following the pattern in an existing tool
   module: a Pydantic input model, a `BaseTool` subclass, and a `run()` method that never raises
   for expected "no data" cases (return an explicit `unavailable` marker instead).
2. Add the agent under `src/nexora/agents/`, subclassing `BaseAgent`. It should read what it
   needs from `InvestigationState` and append its own `Evidence` and `AgentFinding` records.
3. Register the agent in `_SPECIALIST_REGISTRY` in `src/nexora/agents/orchestrator.py`, and add
   it to the relevant category mapping in `src/nexora/agents/planner.py` if it should be engaged
   automatically for certain incident categories.
4. Write unit tests for the new tool(s) under `tests/unit/`, and add or extend an integration test
   under `tests/integration/` exercising the agent as part of a full investigation.

## Adding a new framework to the Application Agent

Add an entry to `_FRAMEWORK_SIGNATURES` in `src/nexora/tools/application_tools.py`. No other
changes should be required, framework-aware analysis is intentionally table-driven.

## Code style

- Python: `ruff` for linting, `mypy` for type checking, type hints throughout, small focused
  functions
- TypeScript/React: `oxlint`, functional components, Tailwind utility classes rather than
  hand-written CSS where possible

## Reporting issues

Please include: what you expected to happen, what actually happened, and, if applicable, the
incident payload or log snippet that reproduces the issue (with any real secrets removed).
