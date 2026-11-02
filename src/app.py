"""
FastAPI Application & Entrypoint for DeckForge (Port 8793).
Exposes the Interactive Presentation Studio (/), Welcome Greeting (/api/greeting),
1-Page Meeting Read-Ahead Brief (/api/tools/executive-brief), Deck Readiness Check (/api/tools/audit-deck),
Streamable HTTP MCP (/mcp), and OAuth 2.1 with S256 PKCE endpoints.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
import uvicorn

from src.google_slides_engine import generate_google_slides_batch_requests
from src.mcp_protocol import MCP_PROTOCOL_VERSION, get_mcp_tools_catalog, handle_mcp_jsonrpc
from src.memo_transformer import (
    audit_deck_readiness,
    generate_executive_brief,
    get_executive_presets,
    get_welcome_greeting,
    remix_or_update_slide,
    transform_memo_to_slide_spec,
)
from src.models import (
    DESIGN_STYLE_PRESETS,
    PRIMARY_THEMES,
    DataImportRequest,
    GeneratePptxRequest,
    GoogleSlidesExportRequest,
    MemoTransformRequest,
    SlideRemixRequest,
)
from src.oauth_pkce import OAuthAndQuotaStore
from src.pptx_engine import build_pptx_bytes, generate_editable_pptx
from src.public_pages import render_about_html, render_docs_html, render_privacy_html, render_terms_html
from src.studio_ui import render_studio_html
from src.templates_and_import import import_tabular_data_to_slide

PORT = 8793
ROOT_DIR = Path(__file__).resolve().parent.parent


def create_app() -> FastAPI:
    app = FastAPI(
        title="DeckForge MCP",
        version="1.0.0",
        description="Executive Presentation & Slide Deck Studio",
        docs_url="/openapi-docs",
        redoc_url=None,
    )
    store = OAuthAndQuotaStore(base_url=f"http://localhost:{PORT}")

    @app.get("/", response_class=HTMLResponse)
    async def index_studio() -> HTMLResponse:
        return HTMLResponse(content=render_studio_html(), status_code=200)

    @app.get("/docs", response_class=HTMLResponse)
    @app.get("/documentation", response_class=HTMLResponse)
    async def documentation_page() -> HTMLResponse:
        return HTMLResponse(content=render_docs_html(), status_code=200)

    @app.get("/about", response_class=HTMLResponse)
    async def about_page() -> HTMLResponse:
        return HTMLResponse(content=render_about_html(), status_code=200)

    @app.get("/privacy", response_class=HTMLResponse)
    async def privacy_policy() -> HTMLResponse:
        return HTMLResponse(content=render_privacy_html(), status_code=200)

    @app.get("/terms", response_class=HTMLResponse)
    async def terms_of_service() -> HTMLResponse:
        return HTMLResponse(content=render_terms_html(), status_code=200)

    @app.get("/api/greeting")
    async def api_greeting() -> Dict[str, Any]:
        return get_welcome_greeting()

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "service": "deckforge-mcp",
            "version": "1.0.0",
            "port": PORT,
            "mcp_protocol_version": MCP_PROTOCOL_VERSION,
            "oauth21_pkce": "S256",
            "tools": [t["name"] for t in get_mcp_tools_catalog()],
        }

    # --- OAuth 2.1 with S256 PKCE Endpoints ---
    @app.get("/.well-known/oauth-authorization-server")
    async def oauth_discovery(request: Request) -> Dict[str, Any]:
        req_base = str(request.base_url).rstrip("/")
        if request.headers.get("x-forwarded-proto") == "https" or "railway.app" in req_base:
            req_base = req_base.replace("http://", "https://", 1)
        override = req_base if "testserver" not in req_base else None
        return store.discovery_metadata(base_url_override=override)

    @app.post("/oauth/register")
    async def oauth_register(request: Request) -> JSONResponse:
        body = await request.json()
        client_name = str(body.get("client_name", "Presentation Studio Client"))
        redirect_uris = list(body.get("redirect_uris") or [])
        registered = store.register_client(client_name=client_name, redirect_uris=redirect_uris)
        return JSONResponse(content=registered, status_code=201)

    @app.get("/oauth/authorize")
    async def oauth_authorize(
        response_type: str = Query(default="code"),
        client_id: str = Query(...),
        redirect_uri: str = Query(default="http://localhost:8793/callback"),
        code_challenge: str = Query(...),
        code_challenge_method: str = Query(default="S256"),
        scope: str = Query(default="mcp:tools deck:export"),
        state: str = Query(default=""),
    ) -> JSONResponse:
        if response_type != "code":
            return JSONResponse(
                content={"error": "unsupported_response_type", "error_description": "Expected response_type=code"},
                status_code=400,
            )
        try:
            issued = store.issue_authorization_code(
                client_id=client_id,
                redirect_uri=redirect_uri,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                scope=scope,
                state=state,
            )
            return JSONResponse(content=issued, status_code=200)
        except ValueError as exc:
            return JSONResponse(
                content={"error": "invalid_request", "error_description": str(exc)},
                status_code=400,
            )

    @app.post("/oauth/token")
    async def oauth_token(request: Request) -> JSONResponse:
        raw_body = (await request.body()).decode("utf-8", errors="ignore")
        params: Dict[str, str] = {}
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type or raw_body.strip().startswith("{"):
            try:
                parsed_json = json.loads(raw_body)
                params = {k: str(v) for k, v in parsed_json.items()}
            except Exception:
                params = {}
        else:
            parsed_qs = parse_qs(raw_body, keep_blank_values=True)
            params = {k: v[0] for k, v in parsed_qs.items() if v}

        grant_type = params.get("grant_type", "authorization_code")
        code = params.get("code", "")
        client_id = params.get("client_id", "")
        redirect_uri = params.get("redirect_uri", "")
        code_verifier = params.get("code_verifier", "")

        if grant_type != "authorization_code":
            return JSONResponse(
                content={"error": "unsupported_grant_type", "error_description": "Use authorization_code"},
                status_code=400,
            )
        try:
            token_data = store.exchange_code_for_token(
                code=code,
                client_id=client_id,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier,
            )
            return JSONResponse(content=token_data, status_code=200)
        except ValueError as exc:
            return JSONResponse(
                content={"error": "invalid_grant", "error_description": str(exc)},
                status_code=400,
            )

    # --- Streamable HTTP MCP Endpoint (GET /mcp & POST /mcp) ---
    @app.get("/mcp")
    async def mcp_stream_info() -> Dict[str, Any]:
        return {
            "name": "deckforge-mcp",
            "version": "1.0.0",
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "transport": "streamable-http",
            "endpoint": "/mcp",
            "oauth_metadata": "/.well-known/oauth-authorization-server",
            "welcome": get_welcome_greeting()["headline"],
            "tools": [t["name"] for t in get_mcp_tools_catalog()],
        }

    @app.post("/mcp")
    async def mcp_jsonrpc_endpoint(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(
                content={"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
                status_code=400,
            )
        response_data = handle_mcp_jsonrpc(payload, store)
        return JSONResponse(content=response_data, status_code=200)

    # --- Studio REST Endpoints ---
    @app.get("/api/presets")
    async def api_presets() -> Dict[str, Any]:
        return {
            "welcome": get_welcome_greeting(),
            "presets": get_executive_presets(),
            "themes": {k: v.model_dump(mode="json") for k, v in PRIMARY_THEMES.items()},
            "design_styles": DESIGN_STYLE_PRESETS,
        }

    @app.get("/api/quota")
    async def api_quota(api_key: str = Query(default="df_free_demo")) -> Dict[str, Any]:
        return store.get_quota_status(api_key)

    @app.post("/api/tools/transform-memo")
    async def api_transform_memo(req: MemoTransformRequest) -> Dict[str, Any]:
        return transform_memo_to_slide_spec(req)

    @app.post("/api/tools/generate-pptx")
    async def api_generate_pptx(req: GeneratePptxRequest) -> JSONResponse:
        try:
            quota_info = store.consume_deck_quota(req.api_key)
            pptx_res = generate_editable_pptx(req.deck_spec)
            return JSONResponse(content={**pptx_res, "quota": quota_info}, status_code=200)
        except PermissionError as exc:
            return JSONResponse(
                content={"status": "quota_exceeded", "error": str(exc), "upgrade_tier": "Pro ($24/mo)"},
                status_code=402,
            )

    @app.post("/api/pptx/download")
    async def api_download_pptx(req: GeneratePptxRequest) -> Response:
        try:
            store.consume_deck_quota(req.api_key)
            raw_bytes = build_pptx_bytes(req.deck_spec)
            slug = "".join(c if c.isalnum() else "_" for c in req.deck_spec.title.lower()).strip("_")[:40]
            filename = f"{slug or 'deckforge_executive_deck'}.pptx"
            return Response(
                content=raw_bytes,
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except PermissionError as exc:
            return JSONResponse(
                content={"status": "quota_exceeded", "error": str(exc), "upgrade_tier": "Pro ($24/mo)"},
                status_code=402,
            )

    @app.post("/api/tools/google-slides")
    async def api_google_slides(req: GoogleSlidesExportRequest) -> Dict[str, Any]:
        return generate_google_slides_batch_requests(req)

    @app.post("/api/tools/remix-slide")
    async def api_remix_slide(req: SlideRemixRequest) -> JSONResponse:
        try:
            return JSONResponse(content=remix_or_update_slide(req), status_code=200)
        except ValueError as exc:
            return JSONResponse(content={"status": "error", "error": str(exc)}, status_code=400)

    @app.post("/api/tools/executive-brief")
    async def api_executive_brief(req: GeneratePptxRequest) -> Dict[str, Any]:
        return generate_executive_brief(req.deck_spec)

    @app.post("/api/tools/audit-deck")
    async def api_audit_deck(req: GeneratePptxRequest) -> Dict[str, Any]:
        return audit_deck_readiness(req.deck_spec)

    @app.post("/api/tools/import-data")
    async def api_import_data(req: DataImportRequest) -> JSONResponse:
        try:
            return JSONResponse(content=import_tabular_data_to_slide(req), status_code=200)
        except ValueError as exc:
            return JSONResponse(content={"status": "error", "error": str(exc)}, status_code=400)

    @app.get("/manifests/claude")
    async def manifest_claude(request: Request) -> Dict[str, Any]:
        is_prod = "railway.app" in str(request.base_url) or request.headers.get("x-forwarded-proto") == "https"
        fname = "claude-connector-manifest.production.json" if is_prod else "claude-connector-manifest.json"
        return json.loads((ROOT_DIR / fname).read_text(encoding="utf-8"))

    @app.get("/manifests/openai")
    async def manifest_openai(request: Request) -> Dict[str, Any]:
        is_prod = "railway.app" in str(request.base_url) or request.headers.get("x-forwarded-proto") == "https"
        fname = "openai-mcp-app.production.json" if is_prod else "openai-mcp-app.json"
        return json.loads((ROOT_DIR / fname).read_text(encoding="utf-8"))

    return app


app = create_app()

if __name__ == "__main__":
    run_port = int(os.environ.get("PORT", str(PORT)))
    uvicorn.run("src.app:app", host="0.0.0.0", port=run_port, reload=False)
