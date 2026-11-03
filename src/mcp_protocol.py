"""
Streamable HTTP MCP Protocol Handler for DeckForge.
Provides initialize (with warm user welcome), notifications/initialized, ping,
resources/list, resources/read, tools/list, and tools/call.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from pydantic import ValidationError

from src.analytics import detect_source, record_event
from src.google_slides_engine import generate_google_slides_batch_requests
from src.memo_transformer import (
    get_welcome_greeting,
    remix_or_update_slide,
    transform_memo_to_slide_spec,
)
from src.models import (
    DeckSpec,
    GeneratePptxRequest,
    GoogleSlidesExportRequest,
    MemoTransformRequest,
    SlideRemixRequest,
)
from src.oauth_pkce import OAuthAndQuotaStore
from src.pptx_engine import generate_editable_pptx
from src.studio_ui import render_studio_html

MCP_PROTOCOL_VERSION = "2025-03-26"
STUDIO_RESOURCE_URI = "ui://deckforge/studio"
UI_META = {"ui": {"resourceUri": STUDIO_RESOURCE_URI}}


def _ensure_schema_descriptions(node: Any, prop_name: str = "") -> Any:
    """Recursively guarantees every property and nested $defs field has a plain-English description."""
    if not isinstance(node, dict):
        return node
    out = dict(node)
    if prop_name and "description" not in out:
        readable = prop_name.replace("_", " ").strip().capitalize()
        out["description"] = f"{readable} parameter for the presentation slide deck."
    if "properties" in out and isinstance(out["properties"], dict):
        out["properties"] = {
            k: _ensure_schema_descriptions(v, prop_name=k)
            for k, v in out["properties"].items()
        }
    if "$defs" in out and isinstance(out["$defs"], dict):
        out["$defs"] = {
            k: _ensure_schema_descriptions(v, prop_name="")
            for k, v in out["$defs"].items()
        }
    return out


def get_mcp_resources_catalog() -> List[Dict[str, Any]]:
    """Returns the interactive presentation studio resource for inline display."""
    return [
        {
            "uri": STUDIO_RESOURCE_URI,
            "name": "DeckForge Executive Slide Studio",
            "description": (
                "Interactive presentation workspace with 16:9 Slide Stage, Reading View, "
                "and Storyboard Grid, plus 1-click color themes, live slide editing, and instant PowerPoint download."
            ),
            "mimeType": "text/html",
        }
    ]


def get_mcp_tools_catalog() -> List[Dict[str, Any]]:
    """Returns presentation tools with plain-English descriptions and store safety annotations."""
    return [
        {
            "name": "generate_editable_pptx",
            "title": "Build Editable PowerPoint (.pptx) Presentation",
            "description": (
                "Creates a ready-to-present, fully editable PowerPoint (.pptx) slide deck complete with "
                "headline takeaways, 4-card key number grids, comparison charts, financial tables, "
                "90-day roadmaps, and speaker talking points."
            ),
            "inputSchema": _ensure_schema_descriptions(GeneratePptxRequest.model_json_schema()),
            "annotations": {
                "title": "Build Editable PowerPoint (.pptx)",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "_meta": UI_META,
        },
        {
            "name": "transform_memo_to_slide_spec",
            "title": "Turn Notes or Memo into a Structured Slide Deck",
            "description": (
                "Turns rough meeting notes, quarterly numbers, or a written memo into a clear "
                "6-slide presentation plan with strong headlines, key metric cards, comparison charts, "
                "summary tables, and speaker talking points."
            ),
            "inputSchema": _ensure_schema_descriptions(MemoTransformRequest.model_json_schema()),
            "annotations": {
                "title": "Turn Notes into Slide Deck",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "_meta": UI_META,
        },
        {
            "name": "generate_google_slides_batch_requests",
            "title": "Prepare Online Slides Export & Interactive Preview",
            "description": (
                "Prepares your presentation for online slide tools and builds a crisp, "
                "interactive 16:9 visual preview of every slide in the deck."
            ),
            "inputSchema": _ensure_schema_descriptions(GoogleSlidesExportRequest.model_json_schema()),
            "annotations": {
                "title": "Prepare Online Slides & Visual Preview",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "_meta": UI_META,
        },
        {
            "name": "remix_or_update_slide",
            "title": "Change Slide Layout or Tighten Slide Wording",
            "description": (
                "Changes a single slide to a different layout (such as Key Numbers Grid, "
                "Quarterly Bar Chart, Side-by-Side Comparison, Financial Table, or 90-Day Roadmap) "
                "and sharpens its headline, bottom takeaway, and speaker notes in plain business English."
            ),
            "inputSchema": _ensure_schema_descriptions(SlideRemixRequest.model_json_schema()),
            "annotations": {
                "title": "Change Layout or Polish Slide Wording",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "_meta": UI_META,
        },
    ]


def _execute_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    quota_store: OAuthAndQuotaStore,
) -> Dict[str, Any]:
    if tool_name == "transform_memo_to_slide_spec":
        req = MemoTransformRequest.model_validate(arguments)
        output = transform_memo_to_slide_spec(req)
        welcome = get_welcome_greeting()["headline"]
        summary = (
            f"{welcome}\n"
            f"Organized your notes into a {output['slide_count']}-slide presentation "
            f"using the '{output['theme_applied']}' color palette with {output['extracted_kpi_count']} key metrics."
        )
        return {
            "content": [{"type": "text", "text": f"{summary}\n\n{json.dumps(output, indent=2)}"}],
            "structuredContent": output,
            "isError": False,
        }

    if tool_name == "generate_editable_pptx":
        api_key = str(arguments.get("api_key") or "df_pro_enterprise")
        deck_raw = arguments.get("deck_spec", arguments)
        deck = DeckSpec.model_validate(deck_raw)
        quota_info = quota_store.consume_deck_quota(api_key)
        pptx_out = generate_editable_pptx(deck)
        enriched = {**pptx_out, "quota": quota_info}
        summary = (
            f"Your presentation '{pptx_out['filename']}' is ready to download "
            f"({pptx_out['slide_count']} editable slides, {pptx_out['file_size_bytes']} bytes)."
        )
        return {
            "content": [{"type": "text", "text": summary}],
            "structuredContent": enriched,
            "isError": False,
        }

    if tool_name == "generate_google_slides_batch_requests":
        req = GoogleSlidesExportRequest.model_validate(arguments)
        gslides_out = generate_google_slides_batch_requests(req)
        summary = (
            f"Prepared {gslides_out['slide_count']} visual slides ({gslides_out['operations_count']} layout elements) "
            f"for presentation '{gslides_out['presentation_id']}'."
        )
        return {
            "content": [{"type": "text", "text": summary}],
            "structuredContent": gslides_out,
            "isError": False,
        }

    if tool_name == "remix_or_update_slide":
        req = SlideRemixRequest.model_validate(arguments)
        remix_out = remix_or_update_slide(req)
        summary = (
            f"Updated Slide {remix_out['slide_number']} to layout '{remix_out['new_layout']}' "
            f"and sharpened the executive wording."
        )
        return {
            "content": [{"type": "text", "text": summary}],
            "structuredContent": remix_out,
            "isError": False,
        }

    raise KeyError(f"Unknown tool '{tool_name}'.")


def handle_mcp_jsonrpc(
    payload: Dict[str, Any],
    quota_store: OAuthAndQuotaStore,
    user_agent: str = "",
) -> Dict[str, Any]:
    """Processes a single request for the /mcp endpoint."""
    req_id = payload.get("id")
    method = payload.get("method", "")
    params = payload.get("params") or {}

    if method == "initialize":
        client_info = params.get("clientInfo") or {}
        src = detect_source(user_agent, path="/mcp", client_name=str(client_info.get("name", "")))
        record_event(event_type="mcp_connect", source=src, tool_name="initialize", detail=str(client_info.get("name", "mcp-client")))
        greeting = get_welcome_greeting()
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"listChanged": False},
                },
                "serverInfo": {
                    "name": "deckforge-mcp",
                    "title": "DeckForge — Executive Presentation & Slide Builder",
                    "version": "1.0.0",
                },
                "instructions": (
                    f"{greeting['headline']} {greeting['message']} "
                    "Always greet the user warmly in plain business English. "
                    "Use transform_memo_to_slide_spec to turn their notes or numbers into a 6-slide plan, "
                    "remix_or_update_slide to adjust any individual slide, and generate_editable_pptx "
                    "to give them a downloadable PowerPoint file."
                ),
                "welcome": greeting,
            },
        }

    if method in ("notifications/initialized", "initialized"):
        return {"jsonrpc": "2.0", "id": req_id, "result": {"acknowledged": True}}

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"resources": get_mcp_resources_catalog()},
        }

    if method == "resources/read":
        uri = str(params.get("uri", ""))
        if uri == STUDIO_RESOURCE_URI:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "contents": [
                        {
                            "uri": STUDIO_RESOURCE_URI,
                            "mimeType": "text/html",
                            "text": render_studio_html(),
                        }
                    ]
                },
            }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": f"Unknown resource URI '{uri}'."},
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": get_mcp_tools_catalog()},
        }

    if method == "tools/call":
        tool_name = str(params.get("name", ""))
        arguments = params.get("arguments") or {}
        try:
            call_result = _execute_mcp_tool(tool_name, arguments, quota_store)
            src = detect_source(user_agent, path="/mcp")
            record_event(event_type="tool_call", source=src, tool_name=tool_name, detail="mcp tools/call")
            return {"jsonrpc": "2.0", "id": req_id, "result": call_result}
        except (ValidationError, PermissionError, KeyError, ValueError) as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Tool execution error: {exc}"}],
                    "isError": True,
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method '{method}' not found."},
    }
