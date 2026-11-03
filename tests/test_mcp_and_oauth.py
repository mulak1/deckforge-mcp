"""
TDD Test Suite 2: Streamable HTTP MCP Protocol, OAuth 2.1 PKCE S256, Quota Gate & Web Studio.
Covers Claude Connectors Directory & ChatGPT MCP Store submission requirements.
"""

import base64
import hashlib
import json
from pathlib import Path
from fastapi.testclient import TestClient

from src.app import create_app


def _make_pkce_pair(verifier: str = "deckforge-pkce-secret-verifier-string-2026-xyzabc123456"):
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def test_health_and_web_studio_ui():
    """Verifies GET /health and GET / interactive presentation studio on port 8793."""
    app = create_app()
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    data = health.json()
    assert data["status"] == "ok"
    assert data["service"] == "deckforge-mcp"
    assert data["port"] == 8793

    studio = client.get("/")
    assert studio.status_code == 200
    assert "DeckForge" in studio.text
    assert "Welcome!" in studio.text
    assert "http://localhost:8793/mcp" in studio.text
    assert "Series A Board Update" in studio.text


def test_oauth21_pkce_s256_complete_flow():
    """
    Verifies OAuth 2.1 Discovery, Client Registration, Authorize with S256 challenge,
    and Token exchange with code_verifier check.
    """
    app = create_app()
    client = TestClient(app)

    # 1. Discovery metadata
    meta_resp = client.get("/.well-known/oauth-authorization-server")
    assert meta_resp.status_code == 200
    meta = meta_resp.json()
    assert "S256" in meta["code_challenge_methods_supported"]
    assert meta["authorization_endpoint"].endswith("/oauth/authorize")
    assert meta["token_endpoint"].endswith("/oauth/token")

    # 2. Dynamic Client Registration
    reg_resp = client.post(
        "/oauth/register",
        json={
            "client_name": "Claude Connectors Directory Client",
            "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
        },
    )
    assert reg_resp.status_code == 201
    client_id = reg_resp.json()["client_id"]

    # 3. Authorize with S256 PKCE
    verifier, challenge = _make_pkce_pair()
    auth_resp = client.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "xyz_state_123",
            "scope": "mcp:tools deck:export",
        },
        follow_redirects=False,
    )
    assert auth_resp.status_code in (200, 302)
    auth_payload = auth_resp.json()
    assert auth_payload["state"] == "xyz_state_123"
    code = auth_payload["code"]

    # 4. Reject invalid code_verifier
    bad_token_resp = client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
            "code_verifier": "wrong_verifier_value_that_must_fail_sha256_check_0000",
        },
    )
    assert bad_token_resp.status_code == 400

    # 5. Issue new code and exchange with valid S256 code_verifier
    auth_resp2 = client.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "state_ok",
        },
    )
    code2 = auth_resp2.json()["code"]
    good_token_resp = client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code2,
            "client_id": client_id,
            "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
            "code_verifier": verifier,
        },
    )
    assert good_token_resp.status_code == 200
    token_data = good_token_resp.json()
    assert token_data["token_type"] == "Bearer"
    assert token_data["access_token"].startswith("df_oauth_")


def test_streamable_http_mcp_lifecycle_and_tool_annotations():
    """
    Verifies Streamable HTTP GET /mcp & POST /mcp JSON-RPC 2.0:
    initialize, notifications/initialized, tools/list (annotations), and tools/call.
    """
    app = create_app()
    client = TestClient(app)

    # GET /mcp discovery
    get_mcp = client.get("/mcp")
    assert get_mcp.status_code == 200
    assert get_mcp.json()["protocolVersion"] == "2025-03-26"

    # 1. initialize
    init_resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "clientInfo": {"name": "claude-ai", "version": "1.0.0"},
                "capabilities": {},
            },
        },
    )
    assert init_resp.status_code == 200
    init_body = init_resp.json()
    assert init_body["result"]["serverInfo"]["name"] == "deckforge-mcp"

    # 2. notifications/initialized
    notif_resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
    )
    assert notif_resp.status_code == 200

    # 3. tools/list with required store annotations
    list_resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )
    assert list_resp.status_code == 200
    tools = list_resp.json()["result"]["tools"]
    tool_names = {t["name"] for t in tools}
    assert tool_names == {
        "generate_editable_pptx",
        "transform_memo_to_slide_spec",
        "generate_google_slides_batch_requests",
        "remix_or_update_slide",
    }
    for tool in tools:
        ann = tool["annotations"]
        assert ann["readOnlyHint"] is True
        assert ann["destructiveHint"] is False
        assert ann["idempotentHint"] is True
        assert ann["openWorldHint"] is False
        schema = tool["inputSchema"]
        for prop_name, prop_val in schema.get("properties", {}).items():
            assert prop_val.get("description"), f"Missing description on {tool['name']}.{prop_name}"
        for def_name, def_val in schema.get("$defs", {}).items():
            for nested_name, nested_val in def_val.get("properties", {}).items():
                assert nested_val.get("description"), f"Missing description on {def_name}.{nested_name}"

    # 4. tools/call -> transform_memo_to_slide_spec
    call_memo = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "transform_memo_to_slide_spec",
                "arguments": {
                    "raw_memo": "Series A Update: ARR hit $6.4M (+180% YoY), NRR at 131%, Gross Margin 84%. Q1 $3.1M, Q2 $4.6M, Q3 $6.4M.",
                    "deck_title": "Series A Investor Update",
                    "organization": "DeckForge Labs",
                    "theme_preset": "stripe_indigo",
                    "target_slide_count": 6,
                },
            },
        },
    )
    assert call_memo.status_code == 200
    memo_res = call_memo.json()["result"]
    assert memo_res["isError"] is False
    deck_spec = memo_res["structuredContent"]["deck_spec"]

    # 5. tools/call -> generate_editable_pptx
    call_pptx = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "generate_editable_pptx",
                "arguments": {
                    "deck_spec": deck_spec,
                    "api_key": "df_pro_enterprise",
                },
            },
        },
    )
    assert call_pptx.status_code == 200
    pptx_res = call_pptx.json()["result"]
    assert pptx_res["isError"] is False
    assert pptx_res["structuredContent"]["file_size_bytes"] > 4000

    # 6. tools/call -> generate_google_slides_batch_requests
    call_gslides = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "generate_google_slides_batch_requests",
                "arguments": {
                    "deck_spec": deck_spec,
                    "presentation_id": "pres_12345",
                },
            },
        },
    )
    assert call_gslides.status_code == 200
    gslides_res = call_gslides.json()["result"]
    assert gslides_res["isError"] is False
    assert len(gslides_res["structuredContent"]["requests"]) > 10


def test_free_vs_pro_quota_enforcement_and_pptx_binary_download():
    """
    Verifies Free tier (3 decks/mo) blocks the 4th deck with an upgrade prompt,
    while Pro tier ($24/mo) allows unlimited generation, and /api/pptx/download serves binary .pptx.
    """
    app = create_app()
    client = TestClient(app)

    presets = client.get("/api/presets").json()["presets"]
    deck_spec = presets[0]["deck_spec"]

    free_key = "df_free_test_user"
    for attempt in range(3):
        resp = client.post(
            "/api/tools/generate-pptx",
            json={"deck_spec": deck_spec, "api_key": free_key},
        )
        assert resp.status_code == 200, f"Attempt {attempt + 1} should succeed"

    # 4th attempt on free tier must return 402 Payment Required / Quota Exceeded
    fourth = client.post(
        "/api/tools/generate-pptx",
        json={"deck_spec": deck_spec, "api_key": free_key},
    )
    assert fourth.status_code == 402
    assert "Pro tier ($24/mo)" in fourth.json()["error"]

    # Pro tier key succeeds without restriction
    pro_resp = client.post(
        "/api/tools/generate-pptx",
        json={"deck_spec": deck_spec, "api_key": "df_pro_enterprise"},
    )
    assert pro_resp.status_code == 200

    # Direct binary .pptx download
    dl_resp = client.post(
        "/api/pptx/download",
        json={"deck_spec": deck_spec, "api_key": "df_pro_enterprise"},
    )
    assert dl_resp.status_code == 200
    assert (
        dl_resp.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert dl_resp.content[:2] == b"PK"


def test_store_submission_manifests_valid():
    """Verifies claude-connector-manifest.json and openai-mcp-app.json exist and are valid."""
    root = Path(__file__).resolve().parent.parent
    claude_manifest = json.loads((root / "claude-connector-manifest.json").read_text())
    openai_manifest = json.loads((root / "openai-mcp-app.json").read_text())

    assert claude_manifest["name"] == "DeckForge MCP"
    assert claude_manifest["auth"]["type"] == "oauth2"
    assert claude_manifest["auth"]["pkce_required"] is True
    assert len(claude_manifest["tools"]) == 4

    assert openai_manifest["name_for_human"] == "DeckForge MCP"
    assert openai_manifest["mcp_endpoint"].endswith("/mcp")
    assert len(openai_manifest["tools"]) == 4


def test_mcp_error_paths_and_manifest_routes():
    """Covers ping, unknown method, unknown tool, malformed JSON, OAuth edge cases, and manifest endpoints."""
    app = create_app()
    client = TestClient(app)

    ping = client.post("/mcp", json={"jsonrpc": "2.0", "id": 10, "method": "ping"})
    assert ping.status_code == 200 and ping.json()["result"] == {}

    unk_method = client.post("/mcp", json={"jsonrpc": "2.0", "id": 11, "method": "unknown/method"})
    assert unk_method.status_code == 200 and unk_method.json()["error"]["code"] == -32601

    unk_tool = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 12, "method": "tools/call", "params": {"name": "nonexistent_tool", "arguments": {}}},
    )
    assert unk_tool.status_code == 200 and unk_tool.json()["result"]["isError"] is True

    bad_json = client.post("/mcp", content=b"{not-valid-json", headers={"Content-Type": "application/json"})
    assert bad_json.status_code == 400 and bad_json.json()["error"]["code"] == -32700

    bad_rt = client.get(
        "/oauth/authorize",
        params={"response_type": "token", "client_id": "claude-connector-client", "code_challenge": "abcdef1234567890abcdef"},
    )
    assert bad_rt.status_code == 400

    bad_method = client.get(
        "/oauth/authorize",
        params={"response_type": "code", "client_id": "claude-connector-client", "code_challenge": "abcdef1234567890abcdef", "code_challenge_method": "plain"},
    )
    assert bad_method.status_code == 400

    assert client.get("/manifests/claude").status_code == 200
    assert client.get("/manifests/openai").status_code == 200
    docs_res = client.get("/docs")
    assert docs_res.status_code == 200 and "Kader Mula" in docs_res.text and "mulak1@gmail.com" in docs_res.text
    assert client.get("/documentation").status_code == 200
    about_res = client.get("/about")
    assert about_res.status_code == 200 and "Kader Mula" in about_res.text and "mulak1@gmail.com" in about_res.text
    assert client.get("/privacy").status_code == 200
    assert client.get("/terms").status_code == 200
    analytics_html = client.get("/analytics")
    assert analytics_html.status_code == 200 and "DeckForge Live Analytics" in analytics_html.text
    analytics_json = client.get("/api/analytics").json()
    assert "counters" in analytics_json and "by_source" in analytics_json
    openapi_spec = client.get("/chatgpt-openapi.json").json()
    assert openapi_spec["openapi"] == "3.1.0"
    for path_item in openapi_spec["paths"].values():
        assert "content" in path_item["post"]["responses"]["200"]
    q_resp = client.get("/api/quota", params={"api_key": "df_free_demo"})
    assert q_resp.status_code == 200 and q_resp.json()["tier"] == "free"


def test_mcp_apps_ui_resource_and_multi_view_studio():
    """
    Verifies Anthropic/OpenAI MCP Apps UI standard:
    - _meta.ui.resourceUri == 'ui://deckforge/studio' in tools/list
    - resources capability in initialize
    - resources/list and resources/read for 'ui://deckforge/studio'
    - 3-Pane Pitch/Gamma/Kimi/Miro Studio views & live theme bar in GET /
    """
    app = create_app()
    client = TestClient(app)

    init_resp = client.post("/mcp", json={"jsonrpc": "2.0", "id": 20, "method": "initialize", "params": {}})
    assert init_resp.status_code == 200
    assert "resources" in init_resp.json()["result"]["capabilities"]

    tools_resp = client.post("/mcp", json={"jsonrpc": "2.0", "id": 21, "method": "tools/list", "params": {}})
    for tool in tools_resp.json()["result"]["tools"]:
        assert tool["_meta"]["ui"]["resourceUri"] == "ui://deckforge/studio"

    res_list = client.post("/mcp", json={"jsonrpc": "2.0", "id": 22, "method": "resources/list", "params": {}})
    assert res_list.status_code == 200
    resources = res_list.json()["result"]["resources"]
    assert any(r["uri"] == "ui://deckforge/studio" and r["mimeType"] == "text/html" for r in resources)

    res_read = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 23, "method": "resources/read", "params": {"uri": "ui://deckforge/studio"}},
    )
    assert res_read.status_code == 200
    contents = res_read.json()["result"]["contents"]
    assert len(contents) == 1 and contents[0]["uri"] == "ui://deckforge/studio"
    assert contents[0]["mimeType"] == "text/html"
    assert "Slide Stage (16:9)" in contents[0]["text"]
    assert "Reading View (Cards)" in contents[0]["text"]
    assert "Storyboard Grid (All Slides)" in contents[0]["text"]

    res_bad = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 24, "method": "resources/read", "params": {"uri": "ui://deckforge/nonexistent"}},
    )
    assert res_bad.status_code == 200 and "error" in res_bad.json()


