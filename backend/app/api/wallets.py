from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import WhaleWallet, WhaleWalletCreate, WhaleWalletImportRequest, WhaleWalletImportSummary, WhaleWalletUpdate, WalletSummary

router = APIRouter(prefix="/wallets", tags=["wallets"])


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


def _get_wallet_or_404(wallet_id: UUID, db: Session) -> dict[str, Any]:
    row = db.execute(text("SELECT * FROM whale_wallets WHERE id = :wallet_id"), {"wallet_id": wallet_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wallet not found")
    return _row_to_dict(row)


@router.get("", response_model=list[WhaleWallet])
def list_wallets(
    enabled: bool | None = Query(default=None),
    chain: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    if enabled is not None:
        filters.append("enabled = :enabled")
        params["enabled"] = enabled
    if chain is not None:
        filters.append("chain = :chain")
        params["chain"] = chain
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    rows = db.execute(
        text(
            f"""
            SELECT *
            FROM whale_wallets
            {where_clause}
            ORDER BY watch_priority ASC, updated_at DESC
            LIMIT :limit
            """
        ),
        params,
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


@router.post("", response_model=WhaleWallet, status_code=status.HTTP_201_CREATED)
def create_wallet(payload: WhaleWalletCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    values = payload.model_dump()
    values["normalized_address"] = payload.normalized_address
    try:
        row = db.execute(
            text(
                """
                INSERT INTO whale_wallets (
                    wallet_address, normalized_address, chain, label, wallet_type, notes, enabled,
                    alert_threshold_usd, watch_priority, confidence_weighting, copy_trade_enabled,
                    do_not_copy, tags, sectors_of_interest
                ) VALUES (
                    :wallet_address, :normalized_address, :chain, :label, :wallet_type, :notes, :enabled,
                    :alert_threshold_usd, :watch_priority, :confidence_weighting, :copy_trade_enabled,
                    :do_not_copy, :tags, :sectors_of_interest
                )
                RETURNING *
                """
            ),
            values,
        ).fetchone()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="wallet already exists for this chain or violates wallet policy",
        ) from exc
    return _row_to_dict(row)


@router.post("/import", response_model=WhaleWalletImportSummary)
def import_wallets(payload: WhaleWalletImportRequest, db: Session = Depends(get_db)) -> WhaleWalletImportSummary:
    imported = 0
    skipped = 0
    failed = 0
    wallet_ids: list[UUID] = []
    for wallet in payload.wallets:
        values = wallet.model_dump()
        values["normalized_address"] = wallet.normalized_address
        values["chain"] = values["chain"].lower()
        try:
            row = db.execute(
                text(
                    """
                    INSERT INTO whale_wallets (
                        wallet_address, normalized_address, chain, label, wallet_type, notes, enabled,
                        alert_threshold_usd, watch_priority, confidence_weighting, copy_trade_enabled,
                        do_not_copy, tags, sectors_of_interest
                    ) VALUES (
                        :wallet_address, :normalized_address, :chain, :label, :wallet_type, :notes, :enabled,
                        :alert_threshold_usd, :watch_priority, :confidence_weighting, :copy_trade_enabled,
                        :do_not_copy, :tags, :sectors_of_interest
                    )
                    ON CONFLICT (chain, normalized_address) DO NOTHING
                    RETURNING id
                    """
                ),
                values,
            ).fetchone()
            if row is None:
                skipped += 1
            else:
                imported += 1
                wallet_ids.append(row._mapping["id"])
        except IntegrityError:
            db.rollback()
            failed += 1
    db.commit()
    return WhaleWalletImportSummary(imported=imported, skipped_duplicates=skipped, failed=failed, wallet_ids=wallet_ids)


@router.get("/summary", response_model=WalletSummary)
def wallet_summary(db: Session = Depends(get_db)) -> dict[str, int]:
    row = db.execute(
        text(
            """
            SELECT
              (SELECT count(*) FROM whale_wallets) AS total_wallets,
              (SELECT count(*) FROM whale_wallets WHERE enabled = TRUE) AS enabled_wallets,
              (SELECT count(*) FROM whale_wallets WHERE do_not_copy = TRUE) AS do_not_copy_wallets,
              (SELECT count(*) FROM wallet_movements) AS movement_count,
              (SELECT count(*) FROM wallet_movements WHERE manual_review_required = TRUE) AS manual_review_movements
            """
        )
    ).fetchone()
    return _row_to_dict(row)


@router.get("/{wallet_id}", response_model=WhaleWallet)
def get_wallet(wallet_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    return _get_wallet_or_404(wallet_id, db)


@router.patch("/{wallet_id}", response_model=WhaleWallet)
def update_wallet(wallet_id: UUID, payload: WhaleWalletUpdate, db: Session = Depends(get_db)) -> dict[str, Any]:
    current = _get_wallet_or_404(wallet_id, db)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return current

    effective_do_not_copy = updates.get("do_not_copy", current["do_not_copy"])
    effective_copy = updates.get("copy_trade_enabled", current["copy_trade_enabled"])
    if effective_do_not_copy and effective_copy:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="do_not_copy wallets cannot be copy_trade_enabled",
        )
    if effective_do_not_copy:
        updates["copy_trade_enabled"] = False
        if updates.get("wallet_type") is None:
            updates["wallet_type"] = "Do Not Copy"

    allowed = {
        "label", "wallet_type", "notes", "enabled", "alert_threshold_usd", "watch_priority",
        "confidence_weighting", "copy_trade_enabled", "do_not_copy", "tags", "sectors_of_interest",
    }
    set_clauses = [f"{field} = :{field}" for field in updates if field in allowed]
    if not set_clauses:
        return current
    params = {**updates, "wallet_id": wallet_id}
    try:
        row = db.execute(
            text(
                f"""
                UPDATE whale_wallets
                SET {', '.join(set_clauses)}, updated_at = now()
                WHERE id = :wallet_id
                RETURNING *
                """
            ),
            params,
        ).fetchone()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="wallet update violates wallet policy") from exc
    return _row_to_dict(row)


@router.patch("/{wallet_id}/enabled", response_model=WhaleWallet)
def set_wallet_enabled(wallet_id: UUID, enabled: bool, db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            UPDATE whale_wallets
            SET enabled = :enabled, updated_at = now()
            WHERE id = :wallet_id
            RETURNING *
            """
        ),
        {"wallet_id": wallet_id, "enabled": enabled},
    ).fetchone()
    if row is None:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wallet not found")
    db.commit()
    return _row_to_dict(row)
