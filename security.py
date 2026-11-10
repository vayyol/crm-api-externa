import os
import secrets
import time
import jwt

from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()

API_KEY = os.getenv("API_KEY_INTEGRACAO")

INTEGRATION_SECRET = os.getenv("INTEGRATION_SECRET")

def validar_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key")
):
    if not API_KEY or not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key ausente ou não configurada."
        )

    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=401,
            detail="API key inválida."
        )

    return True


def validar_usuario_integracao(
    x_user_token: str | None = Header(
        default=None,
        alias="X-User-Token",
    ),
):
    if not INTEGRATION_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Segredo de integração não configurado.",
        )

    if not x_user_token:
        raise HTTPException(
            status_code=401,
            detail="Token do usuário ausente.",
        )

    try:
        payload = jwt.decode(
            x_user_token,
            INTEGRATION_SECRET,
            algorithms=["HS256"],
            audience="clientes-api",
            issuer="saas-starter-kit",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token de integração expirado.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token de integração inválido.",
        )

    user_id = payload.get("sub")

    if not user_id or not isinstance(user_id, str):
        raise HTTPException(
            status_code=401,
            detail="Identidade do usuário inválida.",
        )

    return user_id
