# Agent Operating Rules

Work stage by stage. Do not skip ahead.

Always prefer the safest, cheapest suitable model:
1. Ollama qwen3:4b for low-risk extraction, cleanup, classification and first-pass summaries.
2. ChatGPT for normal development, architecture and reasoning.
3. Anthropic as fallback if ChatGPT token limits are reached.
4. Latest suitable models only for final high-risk production/research analysis.

Never allow model output to directly execute shell commands without human review.

Never allow local model output to execute trades or modify security settings.

Every major change must update:
- README if setup changes
- Installation Guide if install steps change
- User Guide if user workflow changes
- ASVS audit/register if security controls change
- OpenClaw reinstall prompts if reinstall process changes
- Backup/restore docs if data/storage changes

Every stage must end with validation and a summary.
