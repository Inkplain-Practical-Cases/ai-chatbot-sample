# Decodes and verifies a JWT minted by mint_tokens.py. This is the single
# place that trusts a token's claims — callers only ever see either a
# validated TokenPayload or an AuthError, never raw jwt exceptions.
import jwt
from pydantic import ValidationError

from app.core.config import Settings
from app.features.feature_auth.schemas.auth_schemas import TokenPayload


class AuthError(Exception):
    """Raised for any invalid, expired, or malformed token."""


def service_verify_jwt(token: str, settings: Settings) -> TokenPayload:
    """Decodes and verifies `token` against settings.jwt_secret/jwt_algorithm.
    Returns the validated claims as a TokenPayload, or raises AuthError for
    any expired, malformed, or incomplete token."""
    try:
        raw_payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise AuthError("token expired")
    except jwt.InvalidTokenError:
        raise AuthError("invalid token")

    try:
        return TokenPayload(**raw_payload)
    except ValidationError:
        raise AuthError("token payload missing required claims")
