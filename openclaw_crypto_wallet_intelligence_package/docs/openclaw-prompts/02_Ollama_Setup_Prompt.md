# 02 - Ollama Setup Prompt

Install and configure Ollama on the local Ubuntu 24.04 computer.

Only install one local model:

```bash
ollama pull qwen3:4b
```

Tasks:
1. Check whether Ollama is installed.
2. Install Ollama if needed.
3. Pull qwen3:4b only.
4. Confirm the Ollama API is reachable locally.
5. Confirm qwen3:4b responds to a simple test prompt.
6. Add OLLAMA_BASE_URL and OLLAMA_MODEL to `.env.example` if missing.
7. Build a small backend model routing test.
8. Log model task usage to `model_task_logs` once the database exists.

Rules:
- Do not install llama3.2, gemma, qwen3:8b or other local models.
- Do not expose Ollama directly to the internet.
- Use qwen3:4b only for low-risk tasks.
