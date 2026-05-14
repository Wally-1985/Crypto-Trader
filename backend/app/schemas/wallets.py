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


class WalletSummary(BaseModel):
    total_wallets: int
    enabled_wallets: int
    do_not_copy_wallets: int
    movement_count: int
    manual_review_movements: int
