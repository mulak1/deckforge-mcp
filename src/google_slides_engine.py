"""
Google Slides REST API (`presentations.batchUpdate`) Payload Generator & Interactive SVG/HTML Renderer.
Converts a DeckSpec into deterministic batchUpdate operations and standalone SVG slide cards.
"""

from __future__ import annotations

from typing import Any, Dict, List
from xml.sax.saxutils import escape

from src.models import DeckSpec, GoogleSlidesExportRequest, SlideSpec, ThemePalette
from src.svg_renderer import render_slide_svg_card


def _hex_to_rgb_float(hex_str: str) -> Dict[str, float]:
    cleaned = hex_str.lstrip("#")
    return {
        "red": round(int(cleaned[0:2], 16) / 255.0, 4),
        "green": round(int(cleaned[2:4], 16) / 255.0, 4),
        "blue": round(int(cleaned[4:6], 16) / 255.0, 4),
    }


def _esc(val: str) -> str:
    return escape(str(val or ""), {'"': "&quot;", "'": "&apos;"})


def _shape_with_text_ops(
    page_id: str,
    obj_id: str,
    x: int,
    y: int,
    w: int,
    h: int,
    text: str,
    shape_type: str = "ROUND_RECTANGLE",
) -> List[Dict[str, Any]]:
    return [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": shape_type,
                "elementProperties": {
                    "pageObjectId": page_id,
                    "size": {
                        "width": {"magnitude": w, "unit": "PT"},
                        "height": {"magnitude": h, "unit": "PT"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": x,
                        "translateY": y,
                        "unit": "PT",
                    },
                },
            }
        },
        {
            "insertText": {
                "objectId": obj_id,
                "insertionIndex": 0,
                "text": text,
            }
        },
    ]


def _build_layout_body_ops(s_id: str, slide: SlideSpec) -> List[Dict[str, Any]]:
    ops: List[Dict[str, Any]] = []
    if slide.layout_type == "kpi_metrics_grid" and slide.kpis:
        for idx, kpi in enumerate(slide.kpis[:4]):
            kx = 30 + (idx % 2) * 336
            ky = 82 + (idx // 2) * 130
            ops.extend(
                _shape_with_text_ops(
                    s_id,
                    f"{s_id}_kpi_{idx + 1}",
                    kx,
                    ky,
                    318,
                    118,
                    f"{kpi.label}\n{kpi.value} ({kpi.delta})",
                )
            )
        return ops

    if slide.layout_type == "two_column_comparison":
        left_txt = f"{slide.left_column_title}\n" + "\n".join(f"• {b}" for b in slide.left_bullets[:4])
        right_txt = f"{slide.right_column_title}\n" + "\n".join(f"• {b}" for b in slide.right_bullets[:4])
        ops.extend(_shape_with_text_ops(s_id, f"{s_id}_col_left", 30, 82, 320, 250, left_txt))
        ops.extend(_shape_with_text_ops(s_id, f"{s_id}_col_right", 370, 82, 320, 250, right_txt))
        return ops

    if slide.layout_type == "executive_roadmap" and slide.roadmap_phases:
        for idx, phase in enumerate(slide.roadmap_phases[:3]):
            px = 30 + idx * 224
            ptxt = f"{phase.phase} ({phase.timeline})\nOwner: {phase.owner}\n" + "\n".join(
                f"✓ {d}" for d in phase.deliverables[:3]
            )
            ops.extend(_shape_with_text_ops(s_id, f"{s_id}_phase_{idx + 1}", px, 82, 212, 250, ptxt))
        return ops

    return _shape_with_text_ops(s_id, f"{s_id}_body", 30, 82, 660, 260, _summarize_slide_body_text(slide))


def _build_slide_batch_ops(slide: SlideSpec, theme: ThemePalette) -> List[Dict[str, Any]]:
    s_id = f"df_slide_{slide.slide_number:02d}"
    hdr_id = f"{s_id}_header"
    note_id = f"{s_id}_takeaway"

    ops: List[Dict[str, Any]] = [
        {
            "createSlide": {
                "objectId": s_id,
                "insertionIndex": slide.slide_number - 1,
                "slideLayoutReference": {"predefinedLayout": "BLANK"},
            }
        },
        {
            "createShape": {
                "objectId": hdr_id,
                "shapeType": "RECTANGLE",
                "elementProperties": {
                    "pageObjectId": s_id,
                    "size": {
                        "width": {"magnitude": 720, "unit": "PT"},
                        "height": {"magnitude": 64, "unit": "PT"},
                    },
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "PT"},
                },
            }
        },
        {
            "updateShapeProperties": {
                "objectId": hdr_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {
                        "solidFill": {"color": {"rgbColor": _hex_to_rgb_float(theme.primary_hex)}}
                    }
                },
                "fields": "shapeBackgroundFill.solidFill.color",
            }
        },
        {
            "insertText": {
                "objectId": hdr_id,
                "insertionIndex": 0,
                "text": f"{slide.action_title}\n{slide.subtitle}",
            }
        },
    ]

    ops.extend(_build_layout_body_ops(s_id, slide))

    if slide.takeaway_banner:
        ops.extend(
            _shape_with_text_ops(
                s_id,
                note_id,
                30,
                354,
                660,
                36,
                f"KEY TAKEAWAY: {slide.takeaway_banner}",
                shape_type="RECTANGLE",
            )
        )
    return ops


def _summarize_slide_body_text(slide: SlideSpec) -> str:
    if slide.layout_type == "kpi_metrics_grid":
        return "\n".join(f"• {k.label}: {k.value} ({k.delta})" for k in slide.kpis)
    if slide.layout_type == "bar_chart_slide":
        return "\n".join(
            f"• {c.category}: {c.value}{slide.chart_unit} (Target: {c.target or 'N/A'})"
            for c in slide.chart_series
        )
    if slide.layout_type == "two_column_comparison":
        left = "; ".join(slide.left_bullets[:3])
        right = "; ".join(slide.right_bullets[:3])
        return f"[{slide.left_column_title}] {left}\n[{slide.right_column_title}] {right}"
    if slide.layout_type == "financial_table" and slide.table:
        rows = [" | ".join(slide.table.headers)] + [" | ".join(r) for r in slide.table.rows[:5]]
        return "\n".join(rows)
    if slide.layout_type == "executive_roadmap":
        return "\n".join(
            f"{p.phase} ({p.timeline} - {p.owner}): {', '.join(p.deliverables)}"
            for p in slide.roadmap_phases
        )
    return f"{slide.action_title}\n{slide.subtitle}\n{slide.takeaway_banner}"


def _render_slide_svg_card(
    slide: SlideSpec,
    theme: ThemePalette,
    deck_title: str,
    footer_label: str = "Confidential — Leadership Briefing",
) -> str:
    """Delegates 16:9 vector SVG rendering for all 6 layouts to src.svg_renderer."""
    return render_slide_svg_card(slide, theme, deck_title, footer_label)


def generate_google_slides_batch_requests(
    req: GoogleSlidesExportRequest | Dict[str, Any],
) -> Dict[str, Any]:
    """Generates Google Slides presentations.batchUpdate JSON requests and interactive SVG preview."""
    parsed = (
        req
        if isinstance(req, GoogleSlidesExportRequest)
        else GoogleSlidesExportRequest.model_validate(req)
    )
    deck = parsed.deck_spec
    requests: List[Dict[str, Any]] = []
    svg_cards: List[Dict[str, Any]] = []

    for slide in deck.slides:
        requests.extend(_build_slide_batch_ops(slide, deck.theme))
        svg_cards.append(
            {
                "slide_number": slide.slide_number,
                "layout_type": slide.layout_type,
                "action_title": slide.action_title,
                "subtitle": slide.subtitle,
                "takeaway_banner": slide.takeaway_banner,
                "speaker_notes": slide.speaker_notes,
                "svg": _render_slide_svg_card(slide, deck.theme, deck.title, deck.footer_label),
            }
        )

    joined_svgs = "".join(
        f'<div class="df-slide-card" style="margin-bottom:20px;">{c["svg"]}</div>' for c in svg_cards
    )
    html_preview = (
        f'<section data-deck-title="{_esc(deck.title)}" style="padding:16px;">'
        f"<h3>{_esc(deck.title)} ({len(deck.slides)} Slides)</h3>"
        f"{joined_svgs}</section>"
    )

    return {
        "status": "success",
        "presentation_id": parsed.presentation_id,
        "api_endpoint": f"https://slides.googleapis.com/v1/presentations/{parsed.presentation_id}:batchUpdate",
        "slide_count": len(deck.slides),
        "operations_count": len(requests),
        "requests": requests,
        "slide_svg_cards": svg_cards,
        "html_preview": html_preview,
    }
