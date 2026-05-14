from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    app_name: str = "crypto-wallet-intelligence"
    app_version: str = "v0.1.0-dev"
    app_env: str = "development"
    cors_allowed_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    database_url: str = "postgresql+psycopg://cwi_app:change_me_do_not_commit_real_password@localhost:5432/crypto_wallet_intelligence"

    ollama_enabled: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"

    paid_model_escalation_enabled: bool = True
    primary_paid_provider: str = "openai"
    primary_development_model: str = "configure_cost_effective_openai_model"
    fallback_paid_provider: str = "anthropic"
    fallback_development_model: str = "configure_cost_effective_anthropic_model"
    production_reasoning_model: str = "configure_latest_suitable_model_when_system_is_in_use"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    etherscan_api_key: str = ""
    etherscan_base_url: str = "https://api.etherscan.io/api"
    etherscan_max_transactions_per_wallet: int = 10
    etherscan_timeout_seconds: float = 15.0

    broad_market_search_enabled: bool = False
    paper_trading_enabled: bool = True
    live_trading_enabled: bool = False
    require_manual_approval_for_live_trades: bool = True
    emergency_stop_enabled: bool = False


settings = Settings()
