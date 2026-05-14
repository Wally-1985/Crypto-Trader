# 03 - Anthropic Fallback Setup Prompt

Configure Anthropic as the fallback paid model provider for development.

Current desired routing:
1. Ollama qwen3:4b for low-risk local extraction, cleanup, tagging and first-pass summaries.
2. ChatGPT as the primary paid development model.
3. Anthropic as fallback if ChatGPT token limits are reached.
4. When the finished system is used for real research/risk analysis, use the latest suitable paid models for final reasoning.

Tasks:
1. Add Anthropic API key placeholder to `.env.example`.
2. Add fallback provider settings to backend configuration.
3. Add model routing logic with provider priority.
4. Add graceful fallback if ChatGPT returns token/rate limit errors.
5. Log fallback events in `model_task_logs`.
6. Add tests/mocks showing fallback behaviour.
7. Update Installation Guide and README.

Rules:
- Do not hardcode API keys.
- Do not expose keys in frontend code.
- During development, prefer cost-effective model selections where suitable.
- Keep final high-risk research configurable to use the latest suitable models later.
