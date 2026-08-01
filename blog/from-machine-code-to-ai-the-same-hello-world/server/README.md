# Hello ladder runner

FastAPI service that executes **allowlisted** Hello World programs for the blog post.

- Listens on `127.0.0.1:3521`
- Public path: `/blog/from-machine-code-to-ai-the-same-hello-world/api/`
- Never accepts source code from the client - only a language key

## Endpoints

- `GET /health`
- `GET /languages` - ids, titles, source text
- `POST /run/{language}` - run allowlisted program

## Deploy

```bash
python3 -m venv /home/jacob/venvs/hello-ladder
/home/jacob/venvs/hello-ladder/bin/pip install -r requirements.txt
sudo cp deploy/hello-ladder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hello-ladder.service
# Add ProxyPass lines from deploy/apache-proxy.conf to stephens.page-le-ssl.conf
sudo systemctl reload apache2
```
