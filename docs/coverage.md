# How Python Coverage Works

## 1. How coverage.py measures coverage

coverage.py uses Python's tracing infrastructure -- `sys.settrace()` (or `sys.monitoring` in 3.12+) -- to hook into the interpreter at the function/line level.

When tracing is enabled:
- Every line executed fires a trace callback. coverage.py records which `file:line` was hit.
- At the end, it parses each source file with Python's `ast` module to determine **which lines are actually executable** (comments, blank lines, docstrings, pure decorators are excluded).
- **Coverage % = (lines hit) / (executable lines) * 100**

`omit = ["tests/*"]` excludes test code from the metric.

**Example:** `app/app.py` has 51 executable statements. If tests exercise 27 of them, coverage = 27/51 = 53%.

---

## 2. How the report is generated

```bash
docker compose exec -T app uv run pytest --cov=. --cov-report=xml --cov-report=term -v
```

Runs **inside the container** (`WORKDIR=/app`). The chain:

1. pytest collects tests from `tests/` (mounted via docker-compose volume)
2. pytest-cov plugin starts the coverage tracer before the first test
3. All tests run -- every line in `app/*.py` that executes increments its hit counter
4. After tests finish, the tracer stops
5. `--cov-report=xml` writes `/app/coverage.xml` (Cobertura XML format)
6. `--cov-report=term` prints the summary table to stdout

### Cobertura XML structure (simplified)

```xml
<coverage line-rate="0.75">
  <sources>
    <source>/app</source>
  </sources>
  <packages>
    <package name="endpoints" line-rate="0.81">
      <classes>
        <class name="AuthenticationEndpoints.py" filename="endpoints/AuthenticationEndpoints.py" line-rate="1.0">
          <lines>
            <line number="10" hits="5"/>
            <line number="11" hits="0"/>   <!-- missed -->
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
```

Every line in every `.py` file gets a `<line>` entry with a hit count. `hits="0"` = uncovered.

---

## 3. The path fix (why sed is needed)

Inside the container, `<source>/app</source>` is correct -- files are at `/app/app.py`, `/app/endpoints/AuthenticationEndpoints.py`, etc.

On the **GitHub runner**, the repo is at `/home/runner/work/WalletTrackerAPI/WalletTrackerAPI/`. The path `/app` doesn't exist there.

```bash
sed -i 's|<source>/app</source>|<source>app</source>|g; s|<source>\.</source>|<source>app</source>|g' coverage.xml
```

Rewrites `<source>/app</source>` to `<source>app</source>` (relative). SonarQube then resolves `endpoints/AuthenticationEndpoints.py` to `<repo_root>/app/endpoints/AuthenticationEndpoints.py`, matching `sonar.sources=app`.

---

## 4. How SonarQube interprets the data

```properties
sonar.python.coverage.reportPaths=coverage.xml
sonar.sources=app
```

SonarQube's scanner:

1. **Parses the Cobertura XML** -- reads each `<class>` filename and its per-line hits
2. **Maps filenames** -- combines `<source>app</source>` + `filename` attribute to `app/app.py`, `app/endpoints/AuthenticationEndpoints.py`
3. **Cross-references** against files found under `sonar.sources=app` in the checked-out repo
4. **Loads coverage data** per file -- each line is green (hit), yellow (partial branch), or red (missed). Drives the UI visualization.
5. **Computes the quality gate** -- if overall line coverage is below the project threshold, the gate fails and the PR is blocked.

**SonarQube does NOT run the tests.** It only imports the pre-generated XML. It is purely a consumer of coverage data, not a producer.

---

## 5. CI pipeline flow

```text
[container] pytest --cov=.          -->  coverage.xml (Cobertura)
                                              |
                                       sed fix paths
                                              |
                                      upload as artifact
                                              |
[security-checks job] download artifact      |
                                              |
                                      SonarQube Scanner
                                              |
                                          Quality Gate
```

### Upload as artifact

```yaml
- if: always()
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: coverage.xml
```

### Download and scan

```yaml
- uses: actions/download-artifact@v4
  with:
    name: coverage-report

- name: SonarQube Analysis
  uses: SonarSource/sonarqube-scan-action@v5
```

### Wait for CE task (quality gate check)

The scan triggers an async Compute Engine (CE) task on the SonarQube server. The CI:

1. Calls `/api/ce/component?componentKey=$KEY` to get the current task ID
2. Polls `/api/ce/task?id=$TASK_ID` until `status = SUCCESS`
3. Calls `/api/qualitygates/project_status?projectKey=$KEY` to read gate status

This avoids reading a stale gate result from a previous analysis.

---

## Key files

| File | Purpose |
|------|---------|
| `app/pyproject.toml` | Coverage config: `relative_files = true`, `omit = ["tests/*"]` |
| `.github/workflows/ci.yml` | Full pipeline definition |
| `sonar-project.properties` | `sonar.python.coverage.reportPaths=coverage.xml`, `sonar.sources=app` |
| `docker-compose.yml` | Mounts `./tests:/app/tests` at runtime |

## Running coverage locally

```bash
docker compose exec app uv run pytest --cov=. --cov-report=term -v
```

HTML report for browsing:

```bash
docker compose exec app uv run pytest --cov=. --cov-report=html -v
# open htmlcov/index.html
```
