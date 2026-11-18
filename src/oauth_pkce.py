"""
OAuth 2.1 with S256 PKCE Server & Tiered Quota Manager (Free 3 decks/mo vs. Pro $24/mo).
Supports Dynamic Client Registration, Authorization Code issuance, and S256 code_verifier validation.
"""

from __future__ import annotations

import base64
from collections import OrderedDict
import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Set

MAX_STORE_SIZE = 4096
_PRO_KEY_SECRET = os.environ.get(
    "DECKFORGE_PRO_SECRET",
    "df-hmac-v1-pro-signing-secret-8f7e6d5c4b3a2918",
).encode("utf-8")


def _is_prod_runtime() -> bool:
    return bool(
        os.environ.get("RAILWAY_ENVIRONMENT", "").strip()
        or os.environ.get("RAILWAY_PROJECT_ID", "").strip()
        or os.environ.get("PUBLIC_BASE_URL", "").strip()
    )


def _bounded_put(store: "OrderedDict[str, Any]", key: str, value: Any) -> None:
    if key in store:
        store.move_to_end(key)
    store[key] = value
    while len(store) > MAX_STORE_SIZE:
        store.popitem(last=False)


def issue_pro_api_key(label: str = "pro") -> str:
    """Mint an HMAC-SHA256 signed DeckForge Pro API key."""
    nonce = secrets.token_hex(8)
    mac = hmac.new(_PRO_KEY_SECRET, f"df_pro:{label}:{nonce}".encode("ascii"), hashlib.sha256).hexdigest()[:16]
    return f"df_pro_{label}_{nonce}_{mac}"


def verify_signed_pro_key(key: str) -> bool:
    """Verify whether a df_pro_<label>_<nonce>_<mac> key carries a valid HMAC-SHA256 signature."""
    parts = key.split("_")
    if len(parts) != 5 or parts[0] != "df" or parts[1] != "pro":
        return False
    _, _, label, nonce, provided_mac = parts
    expected_mac = hmac.new(_PRO_KEY_SECRET, f"df_pro:{label}:{nonce}".encode("ascii"), hashlib.sha256).hexdigest()[:16]
    return hmac.compare_digest(provided_mac, expected_mac)


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
        self._codes: "OrderedDict[str, AuthCodeRecord]" = OrderedDict()
        self._tokens: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self._test_pro_keys: Set[str] = {
            "df_pro_enterprise",
            "df_pro_directory_reviewer_2026",
        }
        self._pro_keys: Set[str] = {
            k.strip()
            for k in os.environ.get("DECKFORGE_PRO_KEYS", "").split(",")
            if k.strip()
        }
        self._quotas: "OrderedDict[str, QuotaAccount]" = OrderedDict({
            "df_free_demo": QuotaAccount(
                api_key="df_free_demo", tier="free", decks_used=0, decks_limit=3
            ),
            "df_pro_enterprise": QuotaAccount(
                api_key="df_pro_enterprise", tier="pro", decks_used=0, decks_limit=999999
            ),
        })

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
        _bounded_put(self._codes, code, rec)
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

        _bounded_put(self._codes, code, replace(rec, used=True))
        access_token = f"df_oauth_{secrets.token_urlsafe(24)}"
        refresh_token = f"df_refresh_{secrets.token_urlsafe(24)}"
        token_payload = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "scope": rec.scope,
        }
        _bounded_put(self._tokens, access_token, token_payload)
        return token_payload

    def is_valid_pro_key(self, api_key: str) -> bool:
        key = (api_key or "").strip()
        if not key:
            return False
        return (
            key in self._pro_keys
            or key in self._tokens
            or verify_signed_pro_key(key)
            or (not _is_prod_runtime() and key in self._test_pro_keys)
        )

    def get_quota_status(self, api_key: str, *, caller_id: str | None = None) -> Dict[str, Any]:
        raw_key = (api_key or "").strip()
        is_pro = self.is_valid_pro_key(raw_key)
        bucket_key = raw_key if is_pro else ((caller_id or "").strip() or raw_key or "df_free_demo")
        account = self._quotas.get(bucket_key)
        if not account or (account.tier == "pro" and not is_pro):
            account = QuotaAccount(
                api_key=bucket_key,
                tier="pro" if is_pro else "free",
                decks_used=0,
                decks_limit=999999 if is_pro else 3,
            )
            _bounded_put(self._quotas, bucket_key, account)

        remaining = max(0, account.decks_limit - account.decks_used)
        return {
            "api_key": account.api_key,
            "tier": account.tier,
            "price_label": "$24/mo Unlimited Pro" if account.tier == "pro" else "Free Tier (3 decks/mo)",
            "decks_used": account.decks_used,
            "decks_limit": account.decks_limit,
            "remaining": remaining,
            "upgrade_url": "https://buy.stripe.com/9B67sL7pH3FR7W53fYfAc02",
        }

    def consume_deck_quota(self, api_key: str, *, caller_id: str | None = None) -> Dict[str, Any]:
        status = self.get_quota_status(api_key, caller_id=caller_id)
        key = status["api_key"]
        account = self._quotas[key]
        if account.tier == "free" and account.decks_used >= account.decks_limit:
            raise PermissionError(
                f"Free tier limit reached ({account.decks_limit}/{account.decks_limit} decks/mo). "
                "Upgrade to DeckForge Pro tier ($24/mo) at https://buy.stripe.com/9B67sL7pH3FR7W53fYfAc02 "
                "and pass your Pro api_key for unlimited PPTX & Google Slides generation."
            )
        updated = replace(account, decks_used=account.decks_used + 1)
        _bounded_put(self._quotas, key, updated)
        return self.get_quota_status(key)
