"""
Privacy-safe real-time telemetry, analytics dashboard (/analytics & /api/analytics),
and ChatGPT OpenAPI 3.1.0 schema (/chatgpt-openapi.json) for DeckForge MCP.
Zero confidential meeting notes or slide text is ever stored — only aggregate counters
and anonymized event metadata (timestamp, platform, tool name, theme/layout).
"""

from __future__ import annotations

import html
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict

_COUNTERS: dict[str, int] = {
    "total_events": 0,
    "mcp_connections": 0,
    "tool_calls_total": 0,
    "pptx_downloads": 0,
    "web_page_views": 0,
    "pro_unlocks": 0,
}

_BY_SOURCE: dict[str, int] = {
    "Claude": 0,
    "ChatGPT": 0,
    "Web Desk": 0,
    "Other MCP Client": 0,
}

_BY_TOOL: dict[str, int] = {
    "transform_memo_to_slide_spec": 0,
    "generate_editable_pptx": 0,
    "generate_google_slides_batch_requests": 0,
    "remix_or_update_slide": 0,
    "import_tabular_data_to_slide": 0,
}

_RECENT_EVENTS: deque[dict[str, str]] = deque(maxlen=50)


def detect_source(user_agent: str, path: str = "", client_name: str = "") -> str:
    """Classify the request caller as Claude, ChatGPT, Web Desk, or Other MCP Client."""
    ua = (user_agent or "").lower()
    cn = (client_name or "").lower()
    if "claude" in ua or "anthropic" in ua or "claude" in cn or "anthropic" in cn:
        return "Claude"
    if "chatgpt" in ua or "openai" in ua or "gpt" in cn or "/chatgpt" in path:
        return "ChatGPT"
    if path.startswith("/mcp"):
        return "Claude" if not ua or "python" not in ua else "Other MCP Client"
    return "Web Desk"


def record_event(
    *,
    event_type: str,
    source: str,
    tool_name: str = "-",
    detail: str = "",
) -> None:
    """Record a privacy-safe telemetry event in memory."""
    _COUNTERS["total_events"] += 1
    if source in _BY_SOURCE:
        _BY_SOURCE[source] += 1
    else:
        _BY_SOURCE["Other MCP Client"] += 1

    if event_type == "mcp_connect":
        _COUNTERS["mcp_connections"] += 1
    elif event_type == "tool_call":
        _COUNTERS["tool_calls_total"] += 1
        if tool_name in _BY_TOOL:
            _BY_TOOL[tool_name] += 1
    elif event_type == "pptx_download":
        _COUNTERS["pptx_downloads"] += 1
    elif event_type == "page_view":
        _COUNTERS["web_page_views"] += 1
    elif event_type == "pro_unlock":
        _COUNTERS["pro_unlocks"] += 1

    _RECENT_EVENTS.appendleft(
        {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "source": str(source)[:40],
            "event": str(event_type)[:40],
            "tool": str(tool_name or "-")[:80],
            "detail": str(detail or "-")[:80],
        }
    )


def get_analytics_snapshot() -> Dict[str, Any]:
    """Return current telemetry counters and recent anonymized events."""
    return {
        "service": "deckforge-mcp",
        "counters": dict(_COUNTERS),
        "by_source": dict(_BY_SOURCE),
        "by_tool": dict(_BY_TOOL),
        "recent_events": list(_RECENT_EVENTS),
    }


def render_analytics_html() -> str:
    """Render the live HTML Analytics Dashboard for DeckForge across Claude, ChatGPT, and Web."""
    snap = get_analytics_snapshot()
    c = snap["counters"]
    src = snap["by_source"]
    tools = snap["by_tool"]
    esc = lambda v: html.escape(str(v), quote=True)
    rows = "".join(
        f"<tr><td>{esc(ev['timestamp'])}</td><td><strong>{esc(ev['source'])}</strong></td>"
        f"<td>{esc(ev['event'])}</td><td><code>{esc(ev['tool'])}</code></td><td>{esc(ev['detail'])}</td></tr>"
        for ev in snap["recent_events"]
    ) or '<tr><td colspan="5" style="color:#94a3b8;">No events recorded yet in this container session.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Live Analytics (Claude, ChatGPT &amp; Web) — DeckForge</title>
  <style>
    body {{ font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif; background:#070b14; color:#f8fafc; margin:0; padding:2.5rem 1.25rem; line-height:1.6; }}
    main {{ max-width:980px; margin:0 auto; background:#0f172a; border:1px solid #334155; border-radius:16px; padding:2.5rem; }}
    h1 {{ font-size:2rem; font-weight:800; margin:0 0 0.35rem; color:#ffffff; }}
    h2 {{ font-size:1.1rem; font-weight:700; margin:2rem 0 0.75rem; color:#38bdf8; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(175px,1fr)); gap:12px; margin-top:1rem; }}
    .card {{ background:#020617; border:1px solid #334155; border-radius:12px; padding:1.1rem 1.25rem; }}
    .val {{ font-size:1.85rem; font-weight:800; color:#38bdf8; font-variant-numeric:tabular-nums; }}
    .lbl {{ font-size:0.84rem; color:#94a3b8; margin-top:2px; }}
    table {{ width:100%; border-collapse:collapse; margin-top:0.5rem; font-size:0.9rem; }}
    th, td {{ text-align:left; padding:0.6rem 0.75rem; border-bottom:1px solid #334155; color:#e2e8f0; }}
    th {{ background:#020617; color:#38bdf8; font-weight:700; }}
    code {{ background:#020617; border:1px solid #334155; color:#38bdf8; padding:0.15rem 0.4rem; border-radius:6px; font-size:0.84rem; }}
    a {{ color:#38bdf8; text-decoration:none; font-weight:600; }}
  </style>
</head>
<body>
  <main>
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;margin-bottom:1rem;">
      <a href="/">← Return to DeckForge Presentation Studio</a>
      <a href="/analytics">↻ Refresh Live Telemetry</a>
    </div>
    <h1>DeckForge Live Analytics</h1>
    <p style="color:#94a3b8;margin-top:0;">Real-time, privacy-safe usage telemetry across <strong>Claude</strong>, <strong>ChatGPT</strong>, and the <strong>Web Presentation Studio</strong> (zero meeting notes or slide text stored).</p>

    <div class="grid">
      <div class="card"><div class="val">{src.get('Claude', 0)}</div><div class="lbl">Claude Events</div></div>
      <div class="card"><div class="val">{src.get('ChatGPT', 0)}</div><div class="lbl">ChatGPT Events</div></div>
      <div class="card"><div class="val">{src.get('Web Desk', 0)}</div><div class="lbl">Web Studio Events</div></div>
      <div class="card"><div class="val">{c.get('tool_calls_total', 0)}</div><div class="lbl">Total Tool Runs</div></div>
      <div class="card"><div class="val">{c.get('pptx_downloads', 0)}</div><div class="lbl">PowerPoint (.pptx) Exports</div></div>
      <div class="card"><div class="val">{c.get('mcp_connections', 0)}</div><div class="lbl">MCP Connections</div></div>
    </div>

    <h2>Tool Breakdown</h2>
    <div class="grid">
      <div class="card"><div class="val">{tools.get('transform_memo_to_slide_spec', 0)}</div><div class="lbl">Turn Notes into Slides</div></div>
      <div class="card"><div class="val">{tools.get('generate_editable_pptx', 0)}</div><div class="lbl">Build PowerPoint (.pptx)</div></div>
      <div class="card"><div class="val">{tools.get('generate_google_slides_batch_requests', 0)}</div><div class="lbl">16:9 Slide Previews</div></div>
      <div class="card"><div class="val">{tools.get('remix_or_update_slide', 0)}</div><div class="lbl">Remix &amp; Polish Slide</div></div>
      <div class="card"><div class="val">{tools.get('import_tabular_data_to_slide', 0)}</div><div class="lbl">Spreadsheet / CSV Import</div></div>
    </div>

    <h2>Recent Activity Feed (Last 50 Events)</h2>
    <table>
      <thead>
        <tr><th>Timestamp</th><th>Platform</th><th>Event</th><th>Tool</th><th>Detail</th></tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </main>
</body>
</html>"""


def get_chatgpt_openapi_spec() -> Dict[str, Any]:
    """Return the OpenAPI 3.1.0 schema for ChatGPT Plugin / Actions integration."""
    ok_resp = {
        "200": {
            "description": "Successful presentation slide deck response.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                        },
                    }
                }
            },
        }
    }
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "DeckForge: Executive Slide Decks",
            "description": "Turn meeting notes, written memos, spreadsheet tables, and quarterly business metrics into structured 6-slide presentations, 16:9 visual previews, and editable PowerPoint (.pptx) decks.",
            "version": "1.0.0",
        },
        "servers": [{"url": "https://deckforge-mcp-production.up.railway.app"}],
        "paths": {
            "/api/tools/transform-memo": {
                "post": {
                    "operationId": "transformMemoToSlideSpec",
                    "summary": "Turn rough meeting notes, memos, or quarterly numbers into a structured 6-slide presentation plan.",
                    "x-openai-isConsequential": False,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["raw_memo"],
                                    "properties": {
                                        "raw_memo": {"type": "string", "description": "Raw meeting notes, written memo, or quarterly business numbers to turn into slides."},
                                        "deck_title": {"type": "string", "default": "Executive Strategy & Performance Update", "description": "Title for the generated presentation."},
                                        "organization": {"type": "string", "default": "Northstar Enterprise", "description": "Company or team name displayed on the presentation."},
                                        "theme_preset": {
                                            "type": "string",
                                            "enum": ["boardroom_navy", "executive_indigo", "modern_slate", "heritage_emerald", "royal_plum"],
                                            "default": "boardroom_navy",
                                            "description": "Color palette preset for the slide deck.",
                                        },
                                        "target_slide_count": {"type": "integer", "default": 6, "description": "Number of slides to generate (3 to 12)."},
                                    },
                                }
                            }
                        },
                    },
                    "responses": ok_resp,
                }
            },
            "/api/tools/import-data": {
                "post": {
                    "operationId": "importTabularDataToSlide",
                    "summary": "Import CSV, TSV, or spreadsheet rows into a formatted Table or Data Chart slide.",
                    "x-openai-isConsequential": False,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["raw_tabular_text"],
                                    "properties": {
                                        "raw_tabular_text": {"type": "string", "description": "CSV, TSV, or pipe-separated rows with header row."},
                                        "target_mode": {"type": "string", "enum": ["table", "chart"], "default": "chart", "description": "Import as a Table slide or Chart slide."},
                                        "chart_type": {"type": "string", "enum": ["vertical_bar", "horizontal_bar", "line_trend", "stacked_bar"], "default": "vertical_bar", "description": "Chart style when importing as a chart."},
                                        "slide_title": {"type": "string", "default": "Quarterly Performance Breakdown", "description": "Headline for the imported slide."},
                                    },
                                }
                            }
                        },
                    },
                    "responses": ok_resp,
                }
            },
        },
    }
