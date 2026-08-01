# Hello ladder runner

## Architecture

```
index.html  →  HTTP (app.py)  →  deep execute (execute.py)  →  allowlisted programs/
```

| Module | Role |
|--------|------|
| **`execute.py`** | **Deep execute API** — all allowlisted build/run/stats logic |
| **`app.py`** | Thin FastAPI adapter (rate limits, JSON, timeouts) |
| **`programs/`** | Fixed Hello World sources (never from the client) |

### Deep execute interface

```python
import execute as core

core.run_samples("python", samples=10)
# → stdout, avgMs, minMs, maxMs, stdevMs, exitCode, ...

core.benchmark(samples=10, languages=["c", "python"])
# → { samples, hardware, rows: [...] }

core.catalog_levels()   # bands + variants for the UI
core.hardware_info()    # host facts for the page
```

Callers never pass source code — only language ids from the allowlist.

## Endpoints

| Method | Path | Maps to |
|--------|------|---------|
| GET | `/health` | tools + hardware + language list |
| GET | `/levels` | `catalog_levels()` |
| GET | `/languages` | `catalog_languages()` |
| POST | `/run/{language}?samples=N` | `run_samples(language, N)` |
| POST | `/benchmark` | `benchmark(samples, languages?)` |

## Deploy

```bash
python3 -m venv /home/jacob/venvs/hello-ladder
/home/jacob/venvs/hello-ladder/bin/pip install -r requirements.txt
sudo cp deploy/hello-ladder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hello-ladder.service
# ProxyPass from deploy/apache-proxy.conf
sudo systemctl reload apache2
```

## Tests

```bash
cd server
python3 test_execute.py -v
```

Tests hit `execute.py` only (no HTTP, stdlib unittest).
