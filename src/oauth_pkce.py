"""
OAuth 2.1 with S256 PKCE Server & Tiered Quota Manager (Free 3 decks/mo vs. Pro $24/mo).
Supports Dynamic Client Registration, Authorization Code issuance, and S256 code_verifier validation.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass, replace
from typing import Any, Dict, List


@dataclass(frozen=True)
class RegisteredClient:
    client_id: str
    client_name: str
    redirect_uris: tuple[str, ...]
    created_at: float


@dataclass(frozen=True)
class AuthCodeRecord:
    code: str
    client_id: str
    redirect_uri: str
    code_challenge: str
    code_challenge_method: str
    scope: str
    expires_at: float
    used: bool = False


@dataclass(frozen=True)
class QuotaAccount:
    api_key: str
    tier: str
    decks_used: int
    decks_limit: int


def compute_s256_challenge(code_verifier: str) -> str:
    """Computes RFC 7636 S256 code_challenge = BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))."""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class OAuthAndQuotaStore:
    """Manages OAuth 2.1 PKCE state and Free/Pro deck generation quotas via immutable records."""

    def __init__(self, base_url: str = "http://localhost:8793") -> None:
        self.base_url = base_url.rstrip("/")
        self._clients: Dict[str, RegisteredClient] = {
            "claude-connector-client": RegisteredClient(
                client_id="claude-connector-client",
                client_name="Claude Connectors Directory",
                redirect_uris=("https://claude.ai/api/mcp/auth_callback", "http://localhost:8793/callback"),
                created_at=time.time(),
            ),
            "chatgpt-mcp-client": RegisteredClient(
                client_id="chatgpt-mcp-client",
                client_name="ChatGPT Apps & MCP Directory",
                redirect_uris=("https://chatgpt.com/connector_platform_oauth_redirect", "http://localhost:8793/callback"),
                created_at=time.time(),
            ),
        }
        self._codes: Dict[str, AuthCodeRecord] = {}
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._quotas: Dict[str, QuotaAccount] = {
            "df_free_demo": QuotaAccount(
                api_key="df_free_demo", tier="free", decks_used=0, decks_limit=3
            ),
            "df_pro_enterprise": QuotaAccount(
                api_key="df_pro_enterprise", tier="pro", decks_used=0, decks_limit=999999
            ),
        }

    def discovery_metadata(self, base_url_override: str | None = None) -> Dict[str, Any]:
        issuer_base = (base_url_override or self.base_url).rstrip("/")
        return {
            "issuer": issuer_base,
            "authorization_endpoint": f"{issuer_base}/oauth/authorize",
            "token_endpoint": f"{issuer_base}/oauth/token",
            "registration_endpoint": f"{issuer_base}/oauth/register",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
            "scopes_supported": ["mcp:tools", "deck:export", "slides:sync"],
        }

    def register_client(self, client_name: str, redirect_uris: List[str]) -> Dict[str, Any]:
        cid = f"df_client_{secrets.token_hex(6)}"
        record = RegisteredClient(
            client_id=cid,
            client_name=client_name or "MCP Client",
            redirect_uris=tuple(redirect_uris or [f"{self.base_url}/callback"]),
            created_at=time.time(),
        )
        self._clients = {**self._clients, cid: record}
        return {
            "client_id": record.client_id,
            "client_name": record.client_name,
            "redirect_uris": list(record.redirect_uris),
            "token_endpoint_auth_method": "none",
        }

    def issue_authorization_code(
        self,
        client_id: str,
        redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str,
        scope: str,
        state: str,
    ) -> Dict[str, Any]:
        if code_challenge_method != "S256":
            raise ValueError("OAuth 2.1 requires code_challenge_method='S256'.")
        if not code_challenge or len(code_challenge) < 16:
            raise ValueError("Invalid S256 code_challenge length.")

        code = f"df_code_{secrets.token_urlsafe(18)}"
        rec = AuthCodeRecord(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method="S256",
            scope=scope or "mcp:tools deck:export",
            expires_at=time.time() + 600.0,
        )
        self._codes = {**self._codes, code: rec}
        return {
            "code": code,
            "state": state,
            "redirect_uri": redirect_uri,
            "redirect_url": f"{redirect_uri}?code={code}&state={state}",
        }

    def exchange_code_for_token(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> Dict[str, Any]:
        rec = self._codes.get(code)
        if not rec:
            raise ValueError("Invalid or unknown authorization code.")
        if rec.used or time.time() > rec.expires_at:
            raise ValueError("Authorization code has expired or already been used.")
        if rec.client_id != client_id:
            raise ValueError("client_id mismatch during token exchange.")
        if not code_verifier or len(code_verifier) < 20:
            raise ValueError("Missing or invalid PKCE code_verifier.")

        expected = compute_s256_challenge(code_verifier)
        if not secrets.compare_digest(expected, rec.code_challenge):
            raise ValueError("PKCE S256 verification failed: code_verifier does not match code_challenge.")

        self._codes = {**self._codes, code: replace(rec, used=True)}
        access_token = f"df_oauth_{secrets.token_urlsafe(24)}"
        refresh_token = f"df_refresh_{secrets.token_urlsafe(24)}"
        token_payload = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "scope": rec.scope,
        }
        self._tokens = {**self._tokens, access_token: token_payload}
        return token_payload

    def get_quota_status(self, api_key: str) -> Dict[str, Any]:
        key = (api_key or "df_free_demo").strip()
        is_pro = key.startswith("df_pro_") or key.startswith("df_oauth_")
        account = self._quotas.get(key)
        if not account:
            account = QuotaAccount(
                api_key=key,
                tier="pro" if is_pro else "free",
                decks_used=0,
                decks_limit=999999 if is_pro else 3,
            )
            self._quotas = {**self._quotas, key: account}

        remaining = max(0, account.decks_limit - account.decks_used)
        return {
            "api_key": account.api_key,
            "tier": account.tier,
            "price_label": "$24/mo Unlimited Pro" if account.tier == "pro" else "Free Tier (3 decks/mo)",
            "decks_used": account.decks_used,
            "decks_limit": account.decks_limit,
            "remaining": remaining,
            "upgrade_url": f"{self.base_url}/?upgrade=pro",
        }

    def consume_deck_quota(self, api_key: str) -> Dict[str, Any]:
        status = self.get_quota_status(api_key)
        key = status["api_key"]
        account = self._quotas[key]
        if account.tier == "free" and account.decks_used >= account.decks_limit:
            raise PermissionError(
                f"Free tier limit reached ({account.decks_limit}/{account.decks_limit} decks/mo). "
                "Upgrade to DeckForge Pro tier ($24/mo) using key 'df_pro_enterprise' for unlimited PPTX & Google Slides generation."
            )
        updated = replace(account, decks_used=account.decks_used + 1)
        self._quotas = {**self._quotas, key: updated}
        return self.get_quota_status(key)
