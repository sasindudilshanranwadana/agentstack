# inference — local models (recommended)

Run models locally with Ollama (`:11434`) and chat with them via Open WebUI
(`:3101`). Lets the stack use local models alongside hosted providers.

## Upstream credit

- **Ollama** — <https://github.com/ollama/ollama>
- **Open WebUI** — <https://github.com/open-webui/open-webui>

agentstack provides only the deployment config; all credit goes to their
authors. Licenses: see `THIRD_PARTY_NOTICES.md`.

## GPU

CPU works out of the box. For NVIDIA GPU on Linux, install the NVIDIA Container
Toolkit and add a GPU reservation to the `ollama` service. GPU is best-effort on
Docker Desktop.

## Run

```bash
docker network create agentstack 2>/dev/null || true
docker compose up -d
docker exec ollama ollama pull llama3   # pull a model
```
