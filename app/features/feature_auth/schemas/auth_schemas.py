# Pydantic models for the decoded JWT payload minted by mint_tokens.py.
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """The claims we trust once a JWT's signature and expiry are verified."""
    sub: str
    email: str
    department: str
    level: int
