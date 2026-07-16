# Native benchmark runner

This FastAPI service executes the post's existing `simpy_factory.py` under
native CPython and loads the existing Rust kernel as a persistent native shared
library. It deliberately returns the canonical event log rather than trusted
summary statistics. Figure 3 derives the statistics and SHA-256 hash in the
browser, exactly as it does for the browser-native engines.

Routes:

- `GET /health`
- `POST /run/simpy` with `{ "seed": 42 }`
- `POST /run/rust` with `{ "seed": 42 }`

Apache exposes those as:

- `GET /blog/the-animation-is-a-replay/api/health`
- `POST /blog/the-animation-is-a-replay/api/run/simpy`
- `POST /blog/the-animation-is-a-replay/api/run/rust`

The request is limited to the fixed 14-day factory model, seeds from 0 through
999,999,999, 30 runs per client per minute, and a two-second execution timeout.

Both engine routes return the same response shape. Adding another producer must
not require a change to the page's event-log consumer.

## Deployment

The pinned environment lives outside the document root:

```bash
python3 -m venv /home/jacob/venvs/animation-replay-bench
/home/jacob/venvs/animation-replay-bench/bin/pip install -r requirements.txt

cargo build --release --target-dir /tmp/animation-replay-rust-native \
  --manifest-path ../rust-kernel/Cargo.toml
sudo install -D -o root -g root -m 0755 \
  /tmp/animation-replay-rust-native/release/libreplay_kernel.so \
  /usr/local/lib/animation-replay/libreplay_kernel.so
```

Install `deploy/animation-replay-bench.service` into `/etc/systemd/system/`,
install the two directives in `deploy/apache-proxy.conf` inside the
`stephens.page` TLS virtual host, run `apache2ctl configtest`, then enable the
service and reload Apache.
