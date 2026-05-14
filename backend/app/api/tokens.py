from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import TokenMapping, TokenMappingCreate

router = APIRouter(prefix="/token-mappings", tags=["token-mappings"])


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


@router.get("", response_model=list[TokenMapping])
def list_token_mappings(
    chain: str | None = Query(default=None),
    token_symbol: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    if chain:
        filters.append("chain = :chain")
        params["chain"] = chain.lower()
    if token_symbol:
        filters.append("token_symbol = :token_symbol")
        params["token_symbol"] = token_symbol.upper()
    if provider:
        filters.append("provider = :provider")
        params["provider"] = provider
    if enabled is not None:
        filters.append("enabled = :enabled")
        params["enabled"] = enabled
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    rows = db.execute(
        text(
            f"""
            SELECT *
            FROM token_mappings
            {where_clause}
            ORDER BY enabled DESC, provider ASC, chain ASC, token_symbol ASC, updated_at DESC
            LIMIT :limit
            """
        ),
        params,
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


@router.post("", response_model=TokenMapping, status_code=status.HTTP_201_CREATED)
def create_token_mapping(payload: TokenMappingCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    values = payload.model_dump()
    values["chain"] = values["chain"].lower()
    values["token_symbol"] = values["token_symbol"].upper()
    try:
        row = db.execute(
            text(
                """
                INSERT INTO token_mappings (
                    chain, token_symbol, token_contract, provider, provider_token_id, source,
                    confidence_score, notes, enabled
                ) VALUES (
                    :chain, :token_symbol, :token_contract, :provider, :provider_token_id, :source,
                    :confidence_score, :notes, :enabled
                )
                ON CONFLICT (chain, token_symbol, COALESCE(token_contract, ''), provider)
                DO UPDATE SET
                    provider_token_id = EXCLUDED.provider_token_id,
                    source = EXCLUDED.source,
                    confidence_score = EXCLUDED.confidence_score,
                    notes = EXCLUDED.notes,
                    enabled = EXCLUDED.enabled,
                    updated_at = now()
                RETURNING *
                """
            ),
            values,
        ).fetchone()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="token mapping violates identity policy") from exc
    return _row_to_dict(row)
