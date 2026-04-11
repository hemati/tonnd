"""Token management endpoints — JWT auth only (dashboard)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.models.db_models import User
from src.schemas.api_schemas import TokenCreateRequest, TokenCreateResponse, TokenResponse
from src.services.token_service import create_token, list_user_tokens, revoke_token
from src.services.user_service import current_active_user

router = APIRouter()


@router.get("/tokens", response_model=list[TokenResponse])
async def list_tokens(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    tokens = await list_user_tokens(session, user.id)
    return [
        TokenResponse(
            id=t.id,
            name=t.name,
            token_prefix=t.token_prefix,
            scopes=t.scopes,
            expires_at=t.expires_at,
            last_used_at=t.last_used_at,
            created_at=t.created_at,
            is_active=t.is_active,
        )
        for t in tokens
    ]


@router.post("/tokens", response_model=TokenCreateResponse, status_code=201)
async def create_new_token(
    body: TokenCreateRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        token_record, raw_token = await create_token(
            session,
            user_id=user.id,
            name=body.name,
            scopes=body.scopes,
            expires_at=body.expires_at,
        )
        await session.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return TokenCreateResponse(
        token=raw_token,
        id=token_record.id,
        name=token_record.name,
        scopes=token_record.scopes,
        expires_at=token_record.expires_at,
        created_at=token_record.created_at,
    )


@router.delete("/tokens/{token_id}", status_code=204)
async def delete_token(
    token_id: UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    revoked = await revoke_token(session, token_id, user.id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Token not found or already revoked")
    await session.commit()
