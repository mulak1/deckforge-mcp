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
    THEME_PRESETS,
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

COMPACT_DECK_SPEC_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "description": "Presentation spec with title, theme, and slides.",
    "properties": {
        "title": {"type": "string", "description": "Presentation title."},
        "subtitle": {"type": "string", "description": "Cover subtitle."},
        "palette_id": {"type": "string", "description": "Theme palette id."},
        "visual_style": {"type": "string", "description": "Visual style id."},
        "slides": {
            "type": "array",
            "description": "Ordered slide objects (action_title, layout_type, bullet_points).",
            "items": {"type": "object", "description": "Slide object."},
        },
    },
}

_LAYOUT_ALIASES: Dict[str, str] = {
    "title": "title_hero", "cover": "title_hero", "hero": "title_hero", "title_slide": "title_hero",
    "summary": "executive_summary", "bullets": "two_column_comparison", "bullet": "two_column_comparison",
    "comparison": "two_column_comparison", "two_column": "two_column_comparison",
    "kpi": "kpi_metrics_grid", "kpis": "kpi_metrics_grid", "metrics": "kpi_metrics_grid", "numbers": "kpi_metrics_grid",
    "chart": "bar_chart_slide", "bar_chart": "bar_chart_slide", "graph": "bar_chart_slide",
    "table": "financial_table", "data_table": "financial_table",
    "roadmap": "executive_roadmap", "plan": "executive_roadmap", "timeline": "executive_roadmap",
    "quote": "quote_callout",
}
_VALID_LAYOUTS = {
    "title_hero", "executive_summary", "kpi_metrics_grid", "two_column_comparison",
    "bar_chart_slide", "financial_table", "executive_roadmap", "quote_callout",
}


def normalize_cold_deck_spec(raw: Any) -> Dict[str, Any]:
    """Forgivingly normalizes cold-call LLM inputs (aliases like deck_title, title, layout, bullet_points) into a valid DeckSpec dict."""
    if isinstance(raw, DeckSpec):
        return raw.model_dump(mode="json")
    if isinstance(raw, str):
        memo = raw if len(raw.strip()) >= 20 else f"{raw.strip()} — Executive presentation overview and key metrics."
        return transform_memo_to_slide_spec(MemoTransformRequest(raw_memo=memo))["deck_spec"]
    if not isinstance(raw, dict):
        raw = {}
    out = dict(raw)
    title = str(out.get("title") or out.get("deck_title") or out.get("name") or "Executive Presentation Update").strip()
    out["title"] = title if len(title) >= 3 else f"{title} — Briefing"
    palette_key = str(out.get("palette_id") or out.get("theme_preset") or "").strip().lower()
    if palette_key in THEME_PRESETS and "theme" not in out:
        out["theme"] = THEME_PRESETS[palette_key].model_dump(mode="json")
    elif isinstance(out.get("theme"), str) and out["theme"].lower() in THEME_PRESETS:
        out["theme"] = THEME_PRESETS[out["theme"].lower()].model_dump(mode="json")

    raw_slides = out.get("slides")
    if not isinstance(raw_slides, list) or not raw_slides:
        raw_slides = [{"slide_number": 1, "layout_type": "title_hero", "action_title": out["title"]}]
    norm_slides: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw_slides, 1):
        s = dict(item) if isinstance(item, dict) else {"action_title": str(item)}
        s["slide_number"] = int(s.get("slide_number") or idx)
        raw_lt = str(s.get("layout_type") or s.get("layout") or ("title_hero" if idx == 1 else "two_column_comparison")).strip().lower()
        s["layout_type"] = raw_lt if raw_lt in _VALID_LAYOUTS else _LAYOUT_ALIASES.get(raw_lt, "two_column_comparison")
        act = str(s.get("action_title") or s.get("title") or s.get("headline") or f"Slide {idx} Key Takeaway").strip()
        s["action_title"] = (act if len(act) >= 3 else f"{act} — Overview")[:160]
        bullets = s.pop("bullet_points", None) or s.pop("bullets", None) or s.pop("points", None)
        if isinstance(bullets, list) and bullets:
            clean_b = [str(b).strip() for b in bullets if str(b).strip()]
            if not s.get("left_bullets"):
                mid = max(1, (len(clean_b) + 1) // 2)
                s["left_bullets"] = clean_b[:mid]
                s["right_bullets"] = clean_b[mid:] or ["On track against quarterly execution plan"]
            if s["layout_type"] == "title_hero" and not s.get("subtitle"):
                s["subtitle"] = " · ".join(clean_b[:3])[:240]
            if s["layout_type"] == "kpi_metrics_grid" and not s.get("kpis"):
                s["kpis"] = [{"label": f"Highlight {i+1}", "value": b[:38], "delta": "On Track", "sentiment": "positive"} for i, b in enumerate(clean_b[:4])]
        norm_slides.append(s)
    out["slides"] = norm_slides
    return out


def _ensure_schema_descriptions(
    node: Any, prop_name: str = "", defs: Dict[str, Any] | None = None
) -> Any:
    """Recursively guarantees every property has an explicit JSON Schema 'type' and plain-English 'description'."""
    if not isinstance(node, dict):
        return node
    if prop_name == "deck_spec":
        return dict(COMPACT_DECK_SPEC_SCHEMA)
    out = dict(node)
    root_defs = defs if defs is not None else out.get("$defs", {})

    if "anyOf" in out and isinstance(out["anyOf"], list):
        non_null = [branch for branch in out["anyOf"] if isinstance(branch, dict) and branch.get("type") != "null"]
        if non_null:
            primary = dict(non_null[0])
            out.pop("anyOf", None)
            if out.get("default") is None:
                out.pop("default", None)
            saved_desc = out.get("description")
            out = {**primary, **out}
            if saved_desc:
                out["description"] = saved_desc

    if "$ref" in out and isinstance(out["$ref"], str):
        ref_key = out.pop("$ref").split("/")[-1]
        ref_target = dict(root_defs.get(ref_key, {}))
        saved_desc = out.get("description")
        out = {**ref_target, **out}
        if saved_desc:
            out["description"] = saved_desc
        if "type" not in out:
            out["type"] = "object"

    if prop_name and "type" not in out:
        out["type"] = "object" if "properties" in out else "string"

    if not prop_name:
        out.pop("description", None)
    elif "description" not in out:
        readable = prop_name.replace("_", " ").strip().capitalize()
        out["description"] = f"{readable}."
    elif isinstance(out.get("description"), str) and len(out["description"]) > 44:
        out["description"] = out["description"].split(" (")[0][:44].rstrip("., ") + "."

    if "properties" in out and isinstance(out["properties"], dict):
        out["properties"] = {
            k: _ensure_schema_descriptions(v, prop_name=k, defs=root_defs)
            for k, v in out["properties"].items()
        }
    if "items" in out and isinstance(out["items"], dict):
        out["items"] = _ensure_schema_descriptions(out["items"], prop_name=prop_name or "item", defs=root_defs)
    for k in ("$defs", "title", "minLength", "maxLength", "minimum", "maximum", "enum", "default"):
        out.pop(k, None)
    return out


def _read_only_ann(title: str) -> Dict[str, Any]:
    return {"title": title, "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


def get_mcp_resources_catalog() -> List[Dict[str, Any]]:
    """Returns the interactive presentation studio resource for inline display."""
    return [{
        "uri": STUDIO_RESOURCE_URI,
        "name": "DeckForge Executive Slide Studio",
        "description": "Interactive presentation workspace with 16:9 Slide Stage, Reading View, Storyboard Grid, 1-click themes, live slide editing, and instant PowerPoint download.",
        "mimeType": "text/html",
    }]


def get_mcp_tools_catalog() -> List[Dict[str, Any]]:
    """Returns presentation tools with plain-English descriptions and store safety annotations."""
    return [
        {
            "name": "generate_editable_pptx",
            "title": "Format Editable PowerPoint (.pptx) Presentation",
            "description": "Statelessly formats and returns an editable PowerPoint (.pptx) deck with KPI cards, charts, tables, and notes.",
            "inputSchema": _ensure_schema_descriptions(GeneratePptxRequest.model_json_schema()),
            "annotations": _read_only_ann("Format Editable PowerPoint (.pptx)"),
            "_meta": UI_META,
        },
        {
            "name": "transform_memo_to_slide_spec",
            "title": "Analyze Notes or Memo into a Structured Slide Plan",
            "description": "Statelessly analyzes meeting notes or metrics and returns a structured 6-slide presentation plan.",
            "inputSchema": _ensure_schema_descriptions(MemoTransformRequest.model_json_schema()),
            "annotations": _read_only_ann("Analyze Notes into Slide Plan"),
            "_meta": UI_META,
        },
        {
            "name": "generate_google_slides_batch_requests",
            "title": "Render 16:9 Slide Previews & Layout Elements",
            "description": "Statelessly computes 16:9 SVG slide previews and layout elements for the presentation.",
            "inputSchema": _ensure_schema_descriptions(GoogleSlidesExportRequest.model_json_schema()),
            "annotations": _read_only_ann("Render 16:9 Slide Previews"),
            "_meta": UI_META,
        },
        {
            "name": "remix_or_update_slide",
            "title": "Compute Alternate Slide Layout & Polished Wording",
            "description": "Statelessly computes an alternate layout and sharpened wording for a single slide.",
            "inputSchema": _ensure_schema_descriptions(SlideRemixRequest.model_json_schema()),
            "annotations": _read_only_ann("Compute Alternate Layout & Wording"),
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
        deck_raw = normalize_cold_deck_spec(arguments.get("deck_spec", arguments))
        deck = DeckSpec.model_validate(deck_raw)
        quota_info = quota_store.consume_deck_quota(api_key)
        pptx_out = generate_editable_pptx(deck)
        enriched = {**pptx_out, "quota": quota_info}
        summary = (
            f"Your presentation '{pptx_out['filename']}' is ready to download "
            f"({pptx_out['slide_count']} editable slides, {pptx_out['file_size_bytes']} bytes).\n"
            f"Direct Download (.pptx): {pptx_out['download_url']}"
        )
        return {"content": [{"type": "text", "text": summary}], "structuredContent": enriched, "isError": False}

    if tool_name == "generate_google_slides_batch_requests":
        norm_args = {**arguments, "deck_spec": normalize_cold_deck_spec(arguments.get("deck_spec", arguments))}
        req = GoogleSlidesExportRequest.model_validate(norm_args)
        gslides_out = generate_google_slides_batch_requests(req)
        summary = (
            f"Prepared {gslides_out['slide_count']} visual slides ({gslides_out['operations_count']} layout elements) "
            f"for presentation '{gslides_out['presentation_id']}'."
        )
        return {"content": [{"type": "text", "text": summary}], "structuredContent": gslides_out, "isError": False}

    if tool_name == "remix_or_update_slide":
        norm_args = {**arguments, "deck_spec": normalize_cold_deck_spec(arguments.get("deck_spec", arguments))}
        raw_lt = norm_args.get("new_layout_type") or norm_args.get("layout")
        if isinstance(raw_lt, str):
            lt_low = raw_lt.strip().lower()
            norm_args["new_layout_type"] = lt_low if lt_low in _VALID_LAYOUTS else _LAYOUT_ALIASES.get(lt_low, "kpi_metrics_grid")
        req = SlideRemixRequest.model_validate(norm_args)
        remix_out = remix_or_update_slide(req)
        summary = f"Updated Slide {remix_out['slide_number']} to layout '{remix_out['new_layout']}' and sharpened the executive wording."
        return {"content": [{"type": "text", "text": summary}], "structuredContent": remix_out, "isError": False}

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
                "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False}},
                "serverInfo": {"name": "deckforge-mcp", "title": "DeckForge — Executive Presentation & Slide Builder", "version": "1.0.0"},
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
        return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": get_mcp_resources_catalog()}}

    if method == "resources/read":
        uri = str(params.get("uri", ""))
        if uri == STUDIO_RESOURCE_URI:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"contents": [{"uri": STUDIO_RESOURCE_URI, "mimeType": "text/html", "text": render_studio_html()}]}}
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Unknown resource URI '{uri}'."}}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": get_mcp_tools_catalog()}}

    if method == "tools/call":
        tool_name = str(params.get("name", ""))
        arguments = params.get("arguments") or {}
        try:
            call_result = _execute_mcp_tool(tool_name, arguments, quota_store)
            src = detect_source(user_agent, path="/mcp")
            record_event(event_type="tool_call", source=src, tool_name=tool_name, detail="mcp tools/call")
            return {"jsonrpc": "2.0", "id": req_id, "result": call_result}
        except (ValidationError, PermissionError, KeyError, ValueError) as exc:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Tool execution error: {exc}"}], "isError": True}}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method '{method}' not found."}}
