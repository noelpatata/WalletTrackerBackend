# Python Code Coverage

This project uses **pytest-cov** (powered by coverage.py) to measure line coverage, and **SonarQube** to gate PR merges based on the coverage quality gate.

## Tools

| Tool | Role |
|------|------|
| [pytest-cov](https://github.com/pytest-dev/pytest-cov) | pytest plugin that runs coverage.py during tests |
| [coverage.py](https://coverage.readthedocs.io/) | Python line-coverage measurement engine |
| [SonarQube](https://www.sonarsource.com/products/sonarqube/) | Quality gate enforcement and coverage visualization |

## Pipeline Flow

Tests run inside a Docker container via GitHub Actions. The coverage pipeline follows four stages:

```
pytest --cov=.   ──►  coverage.xml  ──►  SonarQube Scanner  ──►  Quality Gate
```

### 1. Run tests with coverage (inside container)

In `.github/workflows/ci.yml`:

```yaml
- run: docker compose exec -T app uv run pytest --cov=. --cov-report=xml --cov-report=term -v
```

- `--cov=.` — measure coverage for all files in `/app/` (the working directory inside the container).
- `--cov-report=xml` — write Cobertura XML to `coverage.xml`.
- `--cov-report=term` — print a summary table to stdout.

Test files are excluded from coverage by the `omit` setting in `app/pyproject.toml`:

```toml
[tool.coverage.run]
relative_files = true
omit = ["tests/*"]
```

The `relative_files = true` flag makes coverage.py output paths relative to the working directory, which is required for correct parsing by SonarQube.

### 2. Copy and fix paths

```yaml
- run: docker compose cp app:/app/coverage.xml ./coverage.xml
  && sed -i 's|<source>/app</source>|<source>app</source>|g;
             s|<source>\.</source>|<source>app</source>|g' coverage.xml
```

The coverage report is generated inside the container with a `<source>` element pointing to `/app/` (the in-container working directory). This path doesn't exist on the GitHub runner, so the `sed` command rewrites it to `app` (relative to the repository root). This makes SonarQube resolve `app.py` → `app/app.py`, matching the `sonar.sources=app` setting.

### 3. Upload as artifact

```yaml
- if: always()
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: coverage.xml
```

The fixed `coverage.xml` is uploaded as a workflow artifact so the downstream `security-checks` job can consume it.

### 4. SonarQube analysis

The `security-checks` job downloads the artifact and runs the SonarQube scanner:

```yaml
- uses: actions/download-artifact@v4
  with:
    name: coverage-report

- name: SonarQube Analysis
  uses: SonarSource/sonarqube-scan-action@v5
```

The scanner reads `sonar-project.properties`, which tells it where to find coverage data:

```properties
sonar.python.coverage.reportPaths=coverage.xml
sonar.sources=app
sonar.tests=tests
sonar.test.exclusions=tests/**
```

### 5. Quality gate check

After the scanner uploads the report, a Compute Engine (CE) task processes it on the SonarQube server. The CI waits for this task to finish before checking the gate:

```bash
# Wait for CE task to complete
TASK_ID=$(curl ... /api/ce/component?componentKey=$PROJECT_KEY | jq -r '.current[0].id // .queue[0].id')
# Poll /api/ce/task?id=$TASK_ID until status = SUCCESS
# Then check /api/qualitygates/project_status
```

This avoids reading a stale quality gate from a previous analysis.

## Directory Layout

```
.
├── .github/workflows/ci.yml     # CI pipeline
├── app/
│   ├── pyproject.toml            # coverage.py config + pytest config
│   ├── Dockerfile                # WORKDIR /app
│   └── ...                       # application source (app.py, endpoints/, ...)
├── tests/                        # test suite (mounted into container at /app/tests)
├── docker-compose.yml            # volumes: - ./tests:/app/tests
└── sonar-project.properties      # SonarQube analysis parameters
```

Tests live outside `app/` to keep the production image lean. They are mounted into the container at runtime via a Docker Compose volume:

```yaml
services:
  app:
    volumes:
      - ./tests:/app/tests
```

## Running Coverage Locally

```sh
docker compose exec app uv run pytest --cov=. --cov-report=term -v
```

Output example:

```
Name                                   Stmts   Miss  Cover
----------------------------------------------------------
app.py                                    51     24    53%
endpoints/AuthenticationEndpoints.py      98      0   100%
...
----------------------------------------------------------
TOTAL                                     412    102    75%
```

To generate an HTML report for browsing:

```sh
docker compose exec app uv run pytest --cov=. --cov-report=html -v
# open htmlcov/index.html
```

## Configuration Reference

### `app/pyproject.toml` — coverage.py

```toml
[tool.coverage.run]
relative_files = true    # report paths relative to working dir
omit = ["tests/*"]       # exclude test code from metrics
```

### `sonar-project.properties` — SonarQube

```properties
sonar.sources=app                          # source root (resolves app.py → app/app.py)
sonar.python.coverage.reportPaths=coverage.xml  # path to Cobertura XML
sonar.tests=tests                          # test directory
sonar.test.exclusions=tests/**             # exclude tests from source analysis
```
