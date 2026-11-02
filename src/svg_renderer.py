"""
Bespoke 16:9 Vector SVG Slide Renderer for DeckForge (960x540 viewBox).
Renders designer-grade vector graphics across 8 executive slide layouts and 4 architectural visual styles:
- Layouts: title_hero, executive_summary, kpi_metrics_grid, bar_chart_slide (4 chart types),
  two_column_comparison, financial_table, executive_roadmap, quote_callout.
- Styles: classic_boardroom, editorial_serif, modern_minimal, bold_keynote.
"""

from __future__ import annotations

from typing import Dict, List
from xml.sax.saxutils import escape

from src.models import KpiMetric, SlideSpec, ThemePalette
from src.svg_charts_and_layouts import (
    render_chart_body_svg,
    render_executive_summary_body_svg,
    render_quote_callout_body_svg,
)

PLAIN_LAYOUT_BADGES: Dict[str, str] = {
    "title_hero": "COVER SLIDE",
    "executive_summary": "KEY SUMMARY",
    "kpi_metrics_grid": "KEY NUMBERS",
    "bar_chart_slide": "TREND CHART",
    "two_column_comparison": "COMPARISON",
    "financial_table": "SUMMARY TABLE",
    "executive_roadmap": "ACTION PLAN",
    "quote_callout": "CUSTOMER PROOF",
}


def _esc(val: str) -> str:
    return escape(str(val or ""), {'"': "&quot;", "'": "&apos;"})


def _is_dark_hex(hex_str: str) -> bool:
    """Computes relative luminance from a #RRGGBB hex string; returns True for dark surfaces."""
    cleaned = str(hex_str or "").strip().lstrip("#")
    if len(cleaned) != 6:
        return False
    r = int(cleaned[0:2], 16) / 255.0
    g = int(cleaned[2:4], 16) / 255.0
    b = int(cleaned[4:6], 16) / 255.0
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) < 0.45


def _surface_tokens(theme: ThemePalette) -> Dict[str, str]:
    if _is_dark_hex(theme.background_hex) or theme.style_family == "bold_keynote":
        return {
            "card_bg": "#1E293B", "card_alt_bg": "#0F172A", "chip_bg": "#334155", "card_border": "#475569",
            "card_text": "#F8FAFC", "card_muted": "#CBD5E1",
            "card_primary": "#F8FAFC" if _is_dark_hex(theme.primary_hex) else theme.primary_hex,
            "grid_line": "#334155", "summary_row_bg": "#1E3A5F", "summary_fg": "#F8FAFC",
        }
    return {
        "card_bg": "#FFFFFF", "card_alt_bg": "#F8FAFC", "chip_bg": theme.background_hex, "card_border": "#CBD5E1",
        "card_text": theme.text_hex, "card_muted": theme.muted_hex, "card_primary": theme.primary_hex,
        "grid_line": "#E2E8F0", "summary_row_bg": "#E0F2FE", "summary_fg": theme.primary_hex,
    }


def _wrap_text(text: str, max_chars: int = 58, max_lines: int = 2) -> List[str]:
    words = str(text or "").split()
    if not words:
        return [""]
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        elif len(lines) < max_lines - 1:
            lines.append(current)
            current = word
        else:
            if len(current) + 1 + len(word) <= max_chars + 10:
                current += " " + word
            else:
                current = current[:max_chars].rstrip() + "…"
                break
    lines.append(current)
    return lines[:max_lines]


_wrap_lines = _wrap_text


def _render_chrome_header_and_footer(
    slide: SlideSpec, theme: ThemePalette, deck_title: str, body_svg: str,
    footer_label: str = "Confidential — Leadership Briefing",
) -> str:
    badge_label = PLAIN_LAYOUT_BADGES.get(slide.layout_type, "SLIDE")
    takeaway = _esc((slide.takeaway_banner or "Key milestone on track.")[:108])
    footer_clean = _esc(footer_label[:64])
    title_lines = _wrap_lines(slide.action_title, 66, 2)
    style = theme.style_family or "classic_boardroom"
    font_css = _esc(theme.font_family or "Inter,-apple-system,BlinkMacSystemFont,sans-serif")
    rx = theme.card_radius

    is_light_hdr = style in ("editorial_serif", "modern_minimal") and not _is_dark_hex(theme.background_hex)
    title_fg = theme.primary_hex if is_light_hdr else "#FFFFFF"
    sub_fg = theme.muted_hex if is_light_hdr else "#CBD5E1"
    tx = 50 if style == "editorial_serif" else 36

    if len(title_lines) == 1:
        header_title_svg = (
            f'<text x="{tx}" y="34" font-size="18" font-weight="800" fill="{title_fg}">{_esc(title_lines[0])}</text>'
            f'<text x="{tx}" y="62" font-size="12.5" font-weight="500" fill="{sub_fg}">{_esc((slide.subtitle or deck_title)[:98])}</text>'
        )
    else:
        header_title_svg = (
            f'<text x="{tx}" y="28" font-size="15.5" font-weight="800" fill="{title_fg}">{_esc(title_lines[0])}</text>'
            f'<text x="{tx}" y="47" font-size="15.5" font-weight="800" fill="{title_fg}">{_esc(title_lines[1])}</text>'
            f'<text x="{tx}" y="68" font-size="11.5" font-weight="500" fill="{sub_fg}">{_esc((slide.subtitle or deck_title)[:98])}</text>'
        )

    if style == "editorial_serif":
        header_bg_svg = (
            f'<rect width="960" height="88" fill="{theme.background_hex}"/>'
            f'<rect width="960" height="5" fill="{theme.primary_hex}"/>'
            f'<rect x="36" y="16" width="5" height="58" rx="2" fill="{theme.accent_hex}"/>'
            f'<line x1="36" y1="86" x2="924" y2="86" stroke="{theme.primary_hex}" stroke-width="1.5"/>'
        )
    elif style == "modern_minimal":
        header_bg_svg = (
            f'<rect width="960" height="88" fill="#FFFFFF"/>'
            f'<rect width="960" height="6" fill="{theme.secondary_hex}"/>'
            f'<line x1="0" y1="87" x2="960" y2="87" stroke="#CBD5E1" stroke-width="1.5"/>'
        )
    else:
        header_bg_svg = (
            f'<rect width="960" height="88" fill="{theme.primary_hex}"/>'
            f'<rect y="84" width="960" height="4" fill="{theme.accent_hex}"/>'
        )

    bg_fill = "#0F172A" if style == "bold_keynote" else theme.background_hex
    return (
        f'<svg data-layout="{_esc(slide.layout_type)}" data-style="{_esc(style)}" data-slide="{slide.slide_number}" '
        'viewBox="0 0 960 540" width="100%" xmlns="http://www.w3.org/2000/svg" '
        f'style="font-family:{font_css};border-radius:12px;'
        'box-shadow:0 12px 32px rgba(15,23,42,0.18);display:block;">'
        f'<rect width="960" height="540" fill="{bg_fill}"/>'
        f"{header_bg_svg}"
        f'<rect x="780" y="18" width="148" height="24" rx="{min(rx, 12)}" fill="{theme.secondary_hex}" opacity="0.92"/>'
        f'<text x="854" y="34" text-anchor="middle" font-size="10" font-weight="800" fill="#FFFFFF" letter-spacing="0.6">'
        f"SLIDE {slide.slide_number:02d} • {_esc(badge_label)}</text>"
        f"{header_title_svg}"
        f"{body_svg}"
        f'<rect x="36" y="450" width="888" height="52" rx="{rx}" fill="{theme.primary_hex}"/>'
        f'<rect x="36" y="450" width="8" height="52" rx="4" fill="{theme.accent_hex}"/>'
        f'<text x="58" y="470" font-size="10" font-weight="800" fill="{theme.accent_hex}" letter-spacing="0.8">BOTTOM LINE</text>'
        f'<text x="58" y="489" font-size="13" font-weight="700" fill="#FFFFFF">{takeaway}</text>'
        f'<text x="36" y="524" font-size="10.5" font-weight="600" fill="{theme.muted_hex}">{footer_clean}</text>'
        f'<text x="924" y="524" text-anchor="end" font-size="10.5" font-weight="700" fill="{theme.muted_hex}">Page {slide.slide_number}</text>'
        "</svg>"
    )


def _render_title_hero_svg(
    slide: SlideSpec, theme: ThemePalette, deck_title: str,
    footer_label: str = "Confidential — Leadership Briefing",
) -> str:
    font_css = _esc(theme.font_family or "Inter,-apple-system,BlinkMacSystemFont,sans-serif")
    title_lines = _wrap_text(slide.action_title or deck_title, max_chars=44, max_lines=2)
    title_nodes = "".join(
        f'<text x="64" y="{208 + idx * 46}" font-size="34" font-weight="900" fill="#FFFFFF" letter-spacing="-0.6">{_esc(line)}</text>'
        for idx, line in enumerate(title_lines)
    )
    sub_lines = _wrap_text(slide.subtitle or deck_title, max_chars=72, max_lines=2)
    sub_nodes = "".join(
        f'<text x="64" y="{306 + idx * 24}" font-size="16" font-weight="500" fill="#E2E8F0">{_esc(line)}</text>'
        for idx, line in enumerate(sub_lines)
    )
    takeaway = _esc((slide.takeaway_banner or "Executive Summary & Key Takeaways")[:104])
    footer_clean = _esc(footer_label[:64])
    return (
        f'<svg data-layout="title_hero" data-style="{_esc(theme.style_family)}" data-slide="{slide.slide_number}" '
        'viewBox="0 0 960 540" width="100%" xmlns="http://www.w3.org/2000/svg" '
        f'style="font-family:{font_css};border-radius:12px;'
        'box-shadow:0 12px 32px rgba(15,23,42,0.22);display:block;">'
        f'<rect width="960" height="540" fill="{theme.primary_hex}"/>'
        f'<polygon points="620,0 960,0 960,540 470,540" fill="{theme.secondary_hex}" opacity="0.22"/>'
        f'<circle cx="850" cy="110" r="160" fill="{theme.accent_hex}" opacity="0.14"/>'
        f'<circle cx="780" cy="420" r="110" fill="{theme.secondary_hex}" opacity="0.18"/>'
        f'<rect x="64" y="62" width="6" height="295" rx="3" fill="{theme.accent_hex}"/>'
        f'<rect x="86" y="64" width="290" height="30" rx="15" fill="{theme.secondary_hex}"/>'
        f'<text x="104" y="84" font-size="11" font-weight="800" fill="#FFFFFF" letter-spacing="1.1">'
        f"EXECUTIVE BRIEFING • SLIDE {slide.slide_number:02d}</text>"
        f'<rect x="740" y="64" width="156" height="30" rx="15" fill="#0F172A" opacity="0.55" stroke="{theme.accent_hex}" stroke-width="1.5"/>'
        f'<text x="818" y="84" text-anchor="middle" font-size="11" font-weight="700" fill="{theme.accent_hex}">{_esc(theme.name[:18])}</text>'
        f"{title_nodes}{sub_nodes}"
        f'<rect x="64" y="396" width="832" height="84" rx="{theme.card_radius}" fill="#FFFFFF" opacity="0.97"/>'
        f'<rect x="64" y="396" width="10" height="84" rx="5" fill="{theme.accent_hex}"/>'
        f'<text x="92" y="426" font-size="11" font-weight="800" fill="{theme.secondary_hex}" letter-spacing="0.9">HEADLINE TAKEAWAY</text>'
        f'<text x="92" y="454" font-size="15.5" font-weight="800" fill="{theme.primary_hex}">{takeaway}</text>'
        f'<text x="64" y="514" font-size="11" font-weight="600" fill="#CBD5E1">{footer_clean}</text>'
        "</svg>"
    )


def _render_kpi_grid_body(slide: SlideSpec, theme: ThemePalette) -> str:
    tok = _surface_tokens(theme)
    rx = theme.card_radius
    kpis = (slide.kpis or [
        KpiMetric(label="Annual Recurring Revenue", value="$18.4M", delta="+142% YoY", sentiment="positive"),
        KpiMetric(label="Net Dollar Retention", value="124%", delta="+900 bps YoY", sentiment="positive"),
        KpiMetric(label="Operating Gross Margin", value="81.2%", delta="+420 bps QoQ", sentiment="positive"),
        KpiMetric(label="Customer Payback Period", value="9.5 mos", delta="-3.2 mos YoY", sentiment="positive"),
    ])[:4]
    cards: List[str] = []
    for idx, kpi in enumerate(kpis):
        x = 36 + (idx % 2) * 452
        y = 108 + (idx // 2) * 164
        pill_bg = "#DCFCE7" if kpi.sentiment == "positive" else ("#FEE2E2" if kpi.sentiment == "negative" else "#E0F2FE")
        pill_fg = "#15803D" if kpi.sentiment == "positive" else ("#B91C1C" if kpi.sentiment == "negative" else "#0369A1")
        arrow = "▼" if kpi.sentiment == "negative" else ("◆" if kpi.sentiment == "neutral" else "▲")
        delta_text = kpi.delta or "+18% QoQ"
        cards.append(
            f'<g transform="translate({x},{y})">'
            f'<rect width="436" height="148" rx="{rx}" fill="{tok["card_bg"]}" stroke="{tok["card_border"]}" stroke-width="1.5"/>'
            f'<rect width="436" height="7" rx="3.5" fill="{theme.secondary_hex if idx % 2 == 0 else theme.accent_hex}"/>'
            f'<text x="22" y="36" font-size="11.5" font-weight="800" fill="{tok["card_muted"]}" letter-spacing="0.6">{_esc(kpi.label.upper()[:38])}</text>'
            f'<text x="22" y="88" font-size="38" font-weight="900" fill="{tok["card_primary"]}" letter-spacing="-0.8">{_esc(kpi.value)}</text>'
            f'<rect x="22" y="104" width="168" height="28" rx="14" fill="{pill_bg}"/>'
            f'<text x="36" y="122" font-size="12" font-weight="800" fill="{pill_fg}">{arrow} {_esc(delta_text[:22])}</text>'
            f'<circle cx="396" cy="42" r="16" fill="{tok["chip_bg"]}" stroke="{theme.secondary_hex}" stroke-width="1.5"/>'
            f'<text x="396" y="47" text-anchor="middle" font-size="11" font-weight="800" fill="{theme.secondary_hex}">0{idx + 1}</text>'
            "</g>"
        )
    return "".join(cards)


def _render_two_column_body(slide: SlideSpec, theme: ThemePalette) -> str:
    tok = _surface_tokens(theme)
    rx = theme.card_radius
    parts: List[str] = [
        f'<rect x="36" y="108" width="424" height="330" rx="{rx}" fill="{tok["card_bg"]}" stroke="{theme.secondary_hex}" stroke-width="2"/>',
        f'<rect x="36" y="108" width="424" height="46" rx="{rx}" fill="{theme.secondary_hex}"/>',
        f'<text x="56" y="136" font-size="14" font-weight="800" fill="#FFFFFF">01 • {_esc(slide.left_column_title[:38])}</text>',
        f'<rect x="500" y="108" width="424" height="330" rx="{rx}" fill="{tok["card_bg"]}" stroke="{theme.accent_hex}" stroke-width="2"/>',
        f'<rect x="500" y="108" width="424" height="46" rx="{rx}" fill="{theme.primary_hex}"/>',
        f'<text x="520" y="136" font-size="14" font-weight="800" fill="#FFFFFF">02 • {_esc(slide.right_column_title[:38])}</text>',
    ]
    for idx, bullet in enumerate((slide.left_bullets or [])[:4]):
        ry = 170 + idx * 62
        lines = _wrap_text(bullet, max_chars=48, max_lines=2)
        t1, t2 = _esc(lines[0]), (_esc(lines[1]) if len(lines) > 1 else "")
        parts.append(
            f'<rect x="52" y="{ry}" width="392" height="52" rx="8" fill="{tok["chip_bg"]}"/>'
            f'<circle cx="72" cy="{ry + 26}" r="11" fill="{theme.secondary_hex}"/>'
            f'<text x="72" y="{ry + 30}" text-anchor="middle" font-size="10.5" font-weight="800" fill="#FFFFFF">{idx + 1}</text>'
            f'<text x="92" y="{ry + (22 if t2 else 30)}" font-size="12" font-weight="600" fill="{tok["card_text"]}">{t1}</text>'
            + (f'<text x="92" y="{ry + 39}" font-size="11.5" font-weight="500" fill="{tok["card_muted"]}">{t2}</text>' if t2 else "")
        )
    for idx, bullet in enumerate((slide.right_bullets or [])[:4]):
        ry = 170 + idx * 62
        lines = _wrap_text(bullet, max_chars=48, max_lines=2)
        t1, t2 = _esc(lines[0]), (_esc(lines[1]) if len(lines) > 1 else "")
        parts.append(
            f'<rect x="516" y="{ry}" width="392" height="52" rx="8" fill="{tok["chip_bg"]}"/>'
            f'<circle cx="536" cy="{ry + 26}" r="11" fill="{theme.accent_hex}"/>'
            f'<text x="536" y="{ry + 30}" text-anchor="middle" font-size="10.5" font-weight="800" fill="#FFFFFF">{idx + 1}</text>'
            f'<text x="556" y="{ry + (22 if t2 else 30)}" font-size="12" font-weight="600" fill="{tok["card_text"]}">{t1}</text>'
            + (f'<text x="556" y="{ry + 39}" font-size="11.5" font-weight="500" fill="{tok["card_muted"]}">{t2}</text>' if t2 else "")
        )
    parts.append(
        f'<circle cx="480" cy="272" r="22" fill="{theme.primary_hex}" stroke="{tok["card_bg"]}" stroke-width="3"/>'
        f'<text x="480" y="277" text-anchor="middle" font-size="12" font-weight="900" fill="#FFFFFF">VS</text>'
    )
    return "".join(parts)


def _render_financial_table_body(slide: SlideSpec, theme: ThemePalette) -> str:
    tok = _surface_tokens(theme)
    rx = theme.card_radius
    tbl = slide.table
    headers = (tbl.headers if tbl and tbl.headers else ["Metric", "Q1", "Q2", "Q3", "Q4"])[:6]
    rows = (
        tbl.rows
        if tbl and tbl.rows
        else [
            ["Ending ARR ($M)", "$11.2M", "$14.5M", "$18.4M", "$23.0M"],
            ["Gross Margin (%)", "77.4%", "79.1%", "81.2%", "82.5%"],
            ["Free Cash Flow Margin", "-8.0%", "-2.5%", "+4.2%", "+9.5%"],
        ]
    )[:6]
    col_count = max(len(headers), 1)
    first_col_w = 280
    rem_w = int(600 / max(col_count - 1, 1))

    nodes: List[str] = [
        f'<rect x="36" y="108" width="888" height="330" rx="{rx}" fill="{tok["card_bg"]}" stroke="{tok["card_border"]}" stroke-width="1.5"/>',
        f'<rect x="36" y="108" width="888" height="46" rx="{rx}" fill="{theme.primary_hex}"/>',
    ]
    for c_idx, h_text in enumerate(headers):
        cx = 56 if c_idx == 0 else (36 + first_col_w + (c_idx - 1) * rem_w + rem_w // 2)
        anchor = "start" if c_idx == 0 else "middle"
        nodes.append(
            f'<text x="{cx}" y="136" text-anchor="{anchor}" font-size="12.5" font-weight="800" fill="#FFFFFF" letter-spacing="0.4">{_esc(h_text[:(34 if c_idx == 0 else 22)])}</text>'
        )

    for r_idx, row in enumerate(rows):
        ry = 154 + r_idx * 46
        is_last = r_idx == len(rows) - 1
        row_bg = tok["summary_row_bg"] if is_last else (tok["card_bg"] if r_idx % 2 == 0 else tok["card_alt_bg"])
        nodes.append(
            f'<rect x="38" y="{ry}" width="884" height="45" fill="{row_bg}"/>'
            f'<line x1="38" y1="{ry + 45}" x2="922" y2="{ry + 45}" stroke="{tok["grid_line"]}" stroke-width="1"/>'
        )
        for c_idx, cell_val in enumerate(row[:col_count]):
            cx = 56 if c_idx == 0 else (36 + first_col_w + (c_idx - 1) * rem_w + rem_w // 2)
            anchor = "start" if c_idx == 0 else "middle"
            cell_str = str(cell_val).strip()
            fw = "800" if (c_idx == 0 or is_last or c_idx == col_count - 1 or cell_str.startswith(("+", "-"))) else "600"
            if c_idx > 0 and cell_str.startswith("+"):
                fg = "#15803D"
            elif c_idx > 0 and cell_str.startswith("-"):
                fg = "#B91C1C"
            elif is_last or c_idx == 0:
                fg = tok["summary_fg"]
            elif c_idx == col_count - 1:
                fg = theme.secondary_hex
            else:
                fg = tok["card_text"]
            nodes.append(
                f'<text x="{cx}" y="{ry + 28}" text-anchor="{anchor}" font-size="13" font-weight="{fw}" fill="{fg}">{_esc(cell_str[:(38 if c_idx == 0 else 24)])}</text>'
            )
    return "".join(nodes)


def _render_roadmap_body(slide: SlideSpec, theme: ThemePalette) -> str:
    tok = _surface_tokens(theme)
    rx = theme.card_radius
    phases = (slide.roadmap_phases or [])[:3]
    nodes: List[str] = []
    for idx, phase in enumerate(phases):
        x = 36 + idx * 302
        y = 110
        header_fill = theme.primary_hex if idx == 0 else (theme.secondary_hex if idx == 1 else theme.accent_hex)
        nodes.append(
            f'<g transform="translate({x},{y})">'
            f'<rect width="284" height="326" rx="{rx}" fill="{tok["card_bg"]}" stroke="{tok["card_border"]}" stroke-width="1.5"/>'
            f'<rect width="284" height="58" rx="{rx}" fill="{header_fill}"/>'
            f'<text x="18" y="26" font-size="13.5" font-weight="800" fill="#FFFFFF">{_esc(phase.phase[:28])}</text>'
            f'<rect x="18" y="34" width="96" height="18" rx="9" fill="#0F172A" opacity="0.35"/>'
            f'<text x="66" y="47" text-anchor="middle" font-size="10.5" font-weight="700" fill="#FFFFFF">{_esc(phase.timeline[:16])}</text>'
            f'<text x="124" y="47" font-size="10.5" font-weight="600" fill="#E2E8F0">• {_esc(phase.owner[:18])}</text>'
        )
        for d_idx, deliv in enumerate((phase.deliverables or [])[:3]):
            dy = 78 + d_idx * 76
            d_lines = _wrap_text(deliv, max_chars=30, max_lines=2)
            l1, l2 = _esc(d_lines[0]), (_esc(d_lines[1]) if len(d_lines) > 1 else "")
            nodes.append(
                f'<rect x="16" y="{dy}" width="252" height="64" rx="8" fill="{tok["chip_bg"]}"/>'
                f'<circle cx="34" cy="{dy + 32}" r="10" fill="{header_fill}"/>'
                f'<text x="34" y="{dy + 36}" text-anchor="middle" font-size="11" font-weight="900" fill="#FFFFFF">✓</text>'
                f'<text x="52" y="{dy + (27 if l2 else 36)}" font-size="11.5" font-weight="700" fill="{tok["card_text"]}">{l1}</text>'
                + (f'<text x="52" y="{dy + 44}" font-size="11" font-weight="500" fill="{tok["card_muted"]}">{l2}</text>' if l2 else "")
            )
        nodes.append("</g>")
        if idx < len(phases) - 1:
            ax = x + 286
            nodes.append(
                f'<circle cx="{ax + 7}" cy="272" r="11" fill="{theme.secondary_hex}"/>'
                f'<text x="{ax + 7}" y="276" text-anchor="middle" font-size="12" font-weight="900" fill="#FFFFFF">→</text>'
            )
    return "".join(nodes)


def render_slide_svg_card(
    slide: SlideSpec,
    theme: ThemePalette,
    deck_title: str,
    footer_label: str = "Confidential — Leadership Briefing",
) -> str:
    """Renders a bespoke 16:9 vector SVG card for all 8 DeckForge slide layouts."""
    if slide.layout_type == "title_hero":
        return _render_title_hero_svg(slide, theme, deck_title, footer_label)
    if slide.layout_type == "executive_summary":
        body_svg = render_executive_summary_body_svg(slide, theme, _wrap_text, _esc, _surface_tokens)
    elif slide.layout_type == "kpi_metrics_grid":
        body_svg = _render_kpi_grid_body(slide, theme)
    elif slide.layout_type == "bar_chart_slide":
        body_svg = render_chart_body_svg(slide, theme, _esc, _surface_tokens)
    elif slide.layout_type == "two_column_comparison":
        body_svg = _render_two_column_body(slide, theme)
    elif slide.layout_type == "financial_table":
        body_svg = _render_financial_table_body(slide, theme)
    elif slide.layout_type == "quote_callout":
        body_svg = render_quote_callout_body_svg(slide, theme, _wrap_text, _esc, _surface_tokens)
    else:
        body_svg = _render_roadmap_body(slide, theme)
    return _render_chrome_header_and_footer(slide, theme, deck_title, body_svg, footer_label)
