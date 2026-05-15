from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.wallet_policy import MOVEMENT_TYPES, WALLET_TYPES, normalize_wallet_address


class WhaleWalletCreate(BaseModel):
    wallet_address: str = Field(min_length=3, max_length=256)
    chain: str = Field(min_length=2, max_length=64)
    label: str | None = Field(default=None, max_length=160)
    wallet_type: str = "Unknown"
    notes: str | None = Field(default=None, max_length=2000)
    enabled: bool = True
    alert_threshold_usd: Decimal = Field(default=Decimal("100000"), ge=0)
    watch_priority: int = Field(default=3, ge=1, le=5)
    confidence_weighting: Decimal = Field(default=Decimal("1.00"), ge=0, le=5)
    copy_trade_enabled: bool = False
    do_not_copy: bool = False
    tags: list[str] = Field(default_factory=list)
    sectors_of_interest: list[str] = Field(default_factory=list)

    @field_validator("wallet_type")
    @classmethod
    def wallet_type_allowed(cls, value: str) -> str:
        if value not in WALLET_TYPES:
            raise ValueError(f"unsupported wallet_type: {value}")
        return value

    @model_validator(mode="after")
    def do_not_copy_disables_copy(self):
        if self.do_not_copy and self.copy_trade_enabled:
            raise ValueError("do_not_copy wallets cannot be copy_trade_enabled")
        return self

    @property
    def normalized_address(self) -> str:
        return normalize_wallet_address(self.wallet_address)


class WhaleWalletUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=160)
    wallet_type: str | None = None
    notes: str | None = Field(default=None, max_length=2000)
    enabled: bool | None = None
    alert_threshold_usd: Decimal | None = Field(default=None, ge=0)
    watch_priority: int | None = Field(default=None, ge=1, le=5)
    confidence_weighting: Decimal | None = Field(default=None, ge=0, le=5)
    copy_trade_enabled: bool | None = None
    do_not_copy: bool | None = None
    tags: list[str] | None = None
    sectors_of_interest: list[str] | None = None

    @field_validator("wallet_type")
    @classmethod
    def wallet_type_allowed(cls, value: str | None) -> str | None:
        if value is not None and value not in WALLET_TYPES:
            raise ValueError(f"unsupported wallet_type: {value}")
        return value

    @model_validator(mode="after")
    def do_not_copy_disables_copy(self):
        if self.do_not_copy is True and self.copy_trade_enabled is True:
            raise ValueError("do_not_copy wallets cannot be copy_trade_enabled")
        return self


class WhaleWalletImportRequest(BaseModel):
    wallets: list[WhaleWalletCreate] = Field(min_length=1, max_length=500)


class WhaleWalletImportSummary(BaseModel):
    imported: int
    skipped_duplicates: int
    failed: int
    wallet_ids: list[UUID]
    paper_trading_only: bool = True


class WhaleWallet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    wallet_address: str
    normalized_address: str
    chain: str
    label: str | None = None
    wallet_type: str
    notes: str | None = None
    enabled: bool
    alert_threshold_usd: Decimal
    watch_priority: int
    confidence_weighting: Decimal
    copy_trade_enabled: bool
    do_not_copy: bool
    last_seen_at: datetime | None = None
    tags: list[str]
    sectors_of_interest: list[str]
    created_at: datetime
    updated_at: datetime


class WalletMovementCreate(BaseModel):
    wallet_id: UUID
    chain: str = Field(min_length=2, max_length=64)
    transaction_hash: str = Field(min_length=3, max_length=256)
    movement_type: str
    token_symbol: str = Field(min_length=1, max_length=32)
    token_contract: str | None = Field(default=None, max_length=256)
    token_amount: Decimal | None = None
    estimated_usd_value: Decimal | None = None
    from_address: str | None = Field(default=None, max_length=256)
    to_address: str | None = Field(default=None, max_length=256)
    protocol: str | None = Field(default=None, max_length=160)
    block_number: int | None = Field(default=None, ge=0)
    transaction_time: datetime
    price_at_trade_time: Decimal | None = None
    gas_fee: Decimal | None = None
    alert_threshold_crossed: bool = False
    processed_by_agent: bool = False
    data_quality_score: int = Field(default=0, ge=0, le=100)
    manual_review_required: bool = True
    raw_api_payload: dict = Field(default_factory=dict)
    data_quality_reasons: list[str] = Field(default_factory=list)

    @field_validator("movement_type")
    @classmethod
    def movement_type_allowed(cls, value: str) -> str:
        if value not in MOVEMENT_TYPES:
            raise ValueError(f"unsupported movement_type: {value}")
        return value


class WalletMovement(WalletMovementCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class AgentAlert(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    wallet_id: UUID | None = None
    wallet_movement_id: UUID | None = None
    alert_type: str
    severity: str
    title: str
    message: str
    data_quality_score: int
    manual_review_required: bool
    decision_snapshot: dict
    status: str = "open"
    analyst_notes: str | None = None
    candidate_decision: str = "manual_review"
    created_at: datetime
    acknowledged_at: datetime | None = None


class AgentAlertUpdate(BaseModel):
    status: str | None = None
    analyst_notes: str | None = Field(default=None, max_length=4000)
    candidate_decision: str | None = None

    @field_validator("status")
    @classmethod
    def status_allowed(cls, value: str | None) -> str | None:
        if value is not None and value not in {"open", "acknowledged", "dismissed", "escalated"}:
            raise ValueError(f"unsupported alert status: {value}")
        return value

    @field_validator("candidate_decision")
    @classmethod
    def decision_allowed(cls, value: str | None) -> str | None:
        if value is not None and value not in {"watch", "manual_review", "ignore", "paper_copy_candidate"}:
            raise ValueError(f"unsupported candidate decision: {value}")
        return value


class PipelineRunLog(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_type: str
    provider: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    checked_wallets: int
    checked_movements: int
    fetched_movements: int
    created_movements: int
    enriched_movements: int
    created_outcomes: int
    skipped_duplicates: int
    skipped_existing: int
    provider_errors: int
    skipped_reason: str | None = None
    metadata: dict
    paper_trading_only: bool


class PollingRunSummary(BaseModel):
    provider: str
    checked_wallets: int
    eligible_wallets: int
    fetched_movements: int = 0
    created_movements: int
    skipped_duplicates: int = 0
    skipped_reason: str | None = None
    provider_errors: int = 0
    paper_trading_only: bool = True


class WalletSummary(BaseModel):
    total_wallets: int
    enabled_wallets: int
    do_not_copy_wallets: int
    movement_count: int
    manual_review_movements: int


class MovementEnrichmentRunSummary(BaseModel):
    provider: str
    checked_movements: int
    enriched_movements: int
    skipped_unmapped: int
    provider_errors: int
    paper_trading_only: bool = True


class SignalOutcome(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    wallet_movement_id: UUID
    wallet_id: UUID
    chain: str
    token_symbol: str
    horizon: str
    provider: str
    baseline_price: Decimal | None = None
    outcome_price: Decimal | None = None
    price_change_pct: Decimal | None = None
    direction: str
    signal_result: str
    measured_at: datetime
    due_at: datetime
    data_quality_score: int
    paper_trading_only: bool
    raw_price_payload: dict
    created_at: datetime
    updated_at: datetime


class SignalOutcomeRunSummary(BaseModel):
    provider: str
    checked_movements: int
    created_outcomes: int
    skipped_existing: int
    checked_due_outcomes: int = 0
    skipped_not_due: int = 0
    provider_errors: int = 0
    paper_trading_only: bool = True


class SignalOutcomeSummary(BaseModel):
    total_outcomes: int
    favorable_outcomes: int
    unfavorable_outcomes: int
    neutral_outcomes: int
    needs_review_outcomes: int


class TokenMappingCreate(BaseModel):
    chain: str = Field(min_length=2, max_length=64)
    token_symbol: str = Field(min_length=1, max_length=32)
    token_contract: str | None = Field(default=None, max_length=256)
    provider: str = "coingecko_public"
    provider_token_id: str = Field(min_length=1, max_length=160)
    source: str = Field(default="manual", max_length=80)
    confidence_score: int = Field(default=80, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=1000)
    enabled: bool = True


class TokenMapping(TokenMappingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class WalletPerformance(BaseModel):
    wallet_id: UUID
    label: str | None = None
    normalized_address: str
    chain: str
    wallet_type: str
    watch_priority: int
    total_outcomes: int
    favorable_outcomes: int
    unfavorable_outcomes: int
    neutral_outcomes: int
    needs_review_outcomes: int
    win_rate_pct: Decimal
    avg_return_pct: Decimal
    avg_data_quality_score: Decimal
    confidence_score: Decimal
    last_outcome_at: datetime | None = None
    paper_trading_only: bool = True
