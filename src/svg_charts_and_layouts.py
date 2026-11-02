"""
Bespoke Multi-Chart SVG Engine (Vertical Bar, Horizontal Bar, Line/Area Trend, Stacked Bar)
and Additional Executive Slide Layouts (3-Pillar Executive Summary & Customer Quote Spotlight).
"""

from __future__ import annotations

from typing import Callable, Dict, List

from src.models import ChartSeriesItem, KpiMetric, RoadmapPhase, SlideSpec, ThemePalette


def _default_series(slide: SlideSpec) -> List[ChartSeriesItem]:
    if slide.chart_series:
        return list(slide.chart_series[:8])
    return [
        ChartSeriesItem(category="Q1 Actual", value=11.2, target=10.5),
        ChartSeriesItem(category="Q2 Actual", value=14.5, target=13.2),
        ChartSeriesItem(category="Q3 Actual", value=18.4, target=16.8),
        ChartSeriesItem(category="Q4 Plan", value=23.0, target=21.0),
    ]


def render_chart_body_svg(
    slide: SlideSpec,
    theme: ThemePalette,
    esc_fn: Callable[[str], str],
    surface_fn: Callable[[ThemePalette], Dict[str, str]],
) -> str:
    """Renders 1 of 4 configurable chart types (vertical_bar, horizontal_bar, line_trend, stacked_bar)."""
    s = surface_fn(theme)
    series = _default_series(slide)
    max_val = max((max(c.value, c.target or 0.0) for c in series), default=1.0) or 1.0
    unit = esc_fn(slide.chart_unit)
    chart_type = slide.chart_type or "vertical_bar"
    rx = theme.card_radius

    # Outer chart card + title + legend
    legend_target = (
        f'<rect x="780" y="122" width="12" height="12" rx="3" fill="{theme.accent_hex}" opacity="0.55"/>'
        f'<text x="798" y="132" font-size="11" font-weight="700" fill="{s["card_muted"]}">Plan Target ({unit})</text>'
        if slide.chart_show_target
        else ""
    )
    type_label = {
        "vertical_bar": "VERTICAL COLUMNS",
        "horizontal_bar": "HORIZONTAL BARS",
        "line_trend": "LINE & AREA TREND",
        "stacked_bar": "STACKED vs. GOAL",
    }.get(chart_type, "TREND CHART")

    header_chrome = (
        f'<rect x="36" y="102" width="888" height="334" rx="{rx}" fill="{s["card_bg"]}" stroke="{s["card_border"]}" stroke-width="1.5"/>'
        f'<text x="64" y="134" font-size="15" font-weight="800" fill="{s["card_primary"]}">{esc_fn(slide.chart_title[:64])}</text>'
        f'<rect x="520" y="118" width="118" height="20" rx="10" fill="{s["chip_bg"]}"/>'
        f'<text x="579" y="132" text-anchor="middle" font-size="9.5" font-weight="800" fill="{theme.secondary_hex}">{type_label}</text>'
        f'<rect x="654" y="122" width="12" height="12" rx="3" fill="{theme.secondary_hex}"/>'
        f'<text x="672" y="132" font-size="11" font-weight="700" fill="{s["card_text"]}">Actual ({unit})</text>'
        f"{legend_target}"
    )

    if chart_type == "horizontal_bar":
        rows_svg: List[str] = []
        row_h = int(230 / max(len(series), 1))
        for idx, item in enumerate(series[:6]):
            ry = 158 + idx * row_h
            bar_h = max(min(row_h - 16, 26), 14)
            bar_w = max(int((item.value / max_val) * 520), 24)
            if slide.chart_show_grid:
                rows_svg.append(
                    f'<line x1="210" y1="{ry + bar_h + 6}" x2="880" y2="{ry + bar_h + 6}" stroke="{s["grid_line"]}" stroke-dasharray="3,3"/>'
                )
            rows_svg.append(
                f'<text x="198" y="{ry + int(bar_h * 0.72)}" text-anchor="end" font-size="12" font-weight="700" fill="{s["card_text"]}">{esc_fn(item.category[:22])}</text>'
            )
            if slide.chart_show_target and item.target is not None and item.target > 0:
                tw = max(int((item.target / max_val) * 520), 18)
                rows_svg.append(
                    f'<rect x="210" y="{ry}" width="{tw}" height="{bar_h}" rx="4" fill="{theme.accent_hex}" opacity="0.22" stroke="{theme.accent_hex}" stroke-dasharray="3,2"/>'
                )
            rows_svg.append(
                f'<rect x="210" y="{ry + 2}" width="{bar_w}" height="{max(bar_h - 4, 10)}" rx="4" fill="{theme.secondary_hex}"/>'
            )
            if slide.chart_show_values:
                t_lbl = f" (Goal: {item.target}{unit})" if (slide.chart_show_target and item.target) else ""
                rows_svg.append(
                    f'<text x="{218 + bar_w}" y="{ry + int(bar_h * 0.72)}" font-size="11.5" font-weight="800" fill="{s["card_primary"]}">{item.value}{unit}{t_lbl}</text>'
                )
        return header_chrome + "".join(rows_svg)

    # Gridlines for vertical / line / stacked charts
    grid_svg = ""
    if slide.chart_show_grid:
        for i in range(4):
            gy = 166 + i * 56
            g_val = round(max_val * (1 - i * 0.25), 1)
            grid_svg += (
                f'<line x1="88" y1="{gy}" x2="888" y2="{gy}" stroke="{s["grid_line"]}" stroke-dasharray="4,4"/>'
                f'<text x="78" y="{gy + 4}" text-anchor="end" font-size="10.5" font-weight="600" fill="{s["card_muted"]}">{g_val}{unit}</text>'
            )
    grid_svg += f'<line x1="88" y1="390" x2="888" y2="390" stroke="{s["card_muted"]}" stroke-width="1.5"/>'

    slot_w = int(760 / max(len(series), 1))

    if chart_type == "line_trend":
        pts: List[tuple[int, int, ChartSeriesItem]] = []
        t_pts: List[tuple[int, int]] = []
        for idx, item in enumerate(series):
            cx = 135 + idx * slot_w + int(slot_w * 0.3)
            cy = 390 - max(int((item.value / max_val) * 204), 16)
            pts.append((cx, cy, item))
            if slide.chart_show_target and item.target is not None and item.target > 0:
                ty = 390 - max(int((item.target / max_val) * 204), 14)
                t_pts.append((cx, ty))

        poly_points = " ".join(f"{x},{y}" for x, y, _ in pts)
        area_points = f"{pts[0][0]},390 " + poly_points + f" {pts[-1][0]},390"
        target_line_svg = (
            f'<polyline fill="none" stroke="{theme.accent_hex}" stroke-width="2.5" stroke-dasharray="6,4" points="{" ".join(f"{x},{y}" for x, y in t_pts)}"/>'
            if len(t_pts) >= 2
            else ""
        )
        nodes_svg = ""
        for x, y, item in pts:
            val_Tag = (
                f'<rect x="{x - 34}" y="{y - 28}" width="68" height="20" rx="5" fill="{s["card_bg"]}" stroke="{theme.secondary_hex}" stroke-width="1.2"/>'
                f'<text x="{x}" y="{y - 14}" text-anchor="middle" font-size="11" font-weight="800" fill="{s["card_primary"]}">{item.value}{unit}</text>'
                if slide.chart_show_values
                else ""
            )
            nodes_svg += (
                f'<circle cx="{x}" cy="{y}" r="6" fill="{theme.secondary_hex}" stroke="#FFFFFF" stroke-width="2"/>'
                f"{val_Tag}"
                f'<text x="{x}" y="414" text-anchor="middle" font-size="12" font-weight="700" fill="{s["card_text"]}">{esc_fn(item.category[:18])}</text>'
            )
        return (
            header_chrome
            + grid_svg
            + f'<polygon points="{area_points}" fill="{theme.secondary_hex}" opacity="0.16"/>'
            + target_line_svg
            + f'<polyline fill="none" stroke="{theme.secondary_hex}" stroke-width="3.5" points="{poly_points}"/>'
            + nodes_svg
        )

    # vertical_bar or stacked_bar
    bars_svg: List[str] = []
    bar_w = max(min(int(slot_w * 0.38), 72), 26)
    for idx, item in enumerate(series):
        x_base = 118 + idx * slot_w
        bar_h = max(int((item.value / max_val) * 204), 16)
        by = 390 - bar_h

        if chart_type == "stacked_bar":
            # Full-slot background track + stacked actual/target overlay
            sw = int(bar_w * 1.45)
            bars_svg.append(f'<rect x="{x_base}" y="186" width="{sw}" height="204" rx="6" fill="{s["chip_bg"]}" opacity="0.65"/>')
            if slide.chart_show_target and item.target:
                th = max(int((item.target / max_val) * 204), 12)
                bars_svg.append(
                    f'<rect x="{x_base}" y="{390 - th}" width="{sw}" height="{th}" rx="6" fill="{theme.accent_hex}" opacity="0.35"/>'
                )
            bars_svg.append(f'<rect x="{x_base}" y="{by}" width="{sw}" height="{bar_h}" rx="6" fill="{theme.secondary_hex}"/>')
            if slide.chart_show_values:
                bars_svg.append(
                    f'<text x="{x_base + int(sw / 2)}" y="{by - 8}" text-anchor="middle" font-size="12" font-weight="800" fill="{s["card_primary"]}">{item.value}{unit}</text>'
                )
            bars_svg.append(
                f'<text x="{x_base + int(sw / 2)}" y="414" text-anchor="middle" font-size="12" font-weight="700" fill="{s["card_text"]}">{esc_fn(item.category[:18])}</text>'
            )
        else:
            # Default vertical_bar (Actual + side-by-side Target bar)
            if slide.chart_show_target and item.target is not None and item.target > 0:
                th = max(int((item.target / max_val) * 204), 12)
                ty = 390 - th
                bars_svg.append(
                    f'<rect x="{x_base + bar_w + 6}" y="{ty}" width="{int(bar_w * 0.72)}" height="{th}" rx="5" fill="{theme.accent_hex}" opacity="0.42"/>'
                )
            bars_svg.append(f'<rect x="{x_base}" y="{by}" width="{bar_w}" height="{bar_h}" rx="5" fill="{theme.secondary_hex}"/>')
            if slide.chart_show_values:
                bars_svg.append(
                    f'<text x="{x_base + int(bar_w / 2)}" y="{by - 8}" text-anchor="middle" font-size="12" font-weight="800" fill="{s["card_primary"]}">{item.value}{unit}</text>'
                )
            bars_svg.append(
                f'<text x="{x_base + bar_w}" y="414" text-anchor="middle" font-size="12" font-weight="700" fill="{s["card_text"]}">{esc_fn(item.category[:18])}</text>'
            )
    return header_chrome + grid_svg + "".join(bars_svg)


def render_executive_summary_body_svg(
    slide: SlideSpec,
    theme: ThemePalette,
    wrap_fn: Callable[[str, int, int], List[str]],
    esc_fn: Callable[[str], str],
    surface_fn: Callable[[ThemePalette], Dict[str, str]],
) -> str:
    """Renders a 3-Pillar Executive Summary slide (01, 02, 03 cards with key findings)."""
    s = surface_fn(theme)
    rx = theme.card_radius
    phases = list(slide.roadmap_phases[:3]) if slide.roadmap_phases else [
        RoadmapPhase(
            phase="1. Commercial Momentum",
            timeline="KEY FINDING 01",
            owner="Revenue & Growth",
            deliverables=[
                "Exceeded quarterly growth target by 14% across core accounts",
                "Self-serve customer referrals drove 64% of new team additions",
            ],
        ),
        RoadmapPhase(
            phase="2. Operating Efficiency",
            timeline="KEY FINDING 02",
            owner="Finance & Operations",
            deliverables=[
                "Gross margin expanded to 81.2% with positive free cash flow",
                "Customer payback period shortened to 9.5 months",
            ],
        ),
        RoadmapPhase(
            phase="3. Next-Quarter Priorities",
            timeline="KEY FINDING 03",
            owner="Executive Leadership",
            deliverables=[
                "Scale multi-department enterprise agreements across top 50 clients",
                "Complete automated monthly reporting rollout by end of quarter",
            ],
        ),
    ]
    cards: List[str] = []
    for idx, p in enumerate(phases[:3]):
        x = 36 + idx * 302
        num_badge = f"0{idx + 1}"
        items_svg: List[str] = []
        cy = 248
        for d in p.deliverables[:3]:
            wrapped = wrap_fn(d, 34, 2)
            items_svg.append(
                f'<circle cx="{x + 26}" cy="{cy - 4}" r="4" fill="{theme.secondary_hex}"/>'
                f'<text x="{x + 38}" y="{cy}" font-size="12" font-weight="600" fill="{s["card_text"]}">{esc_fn(wrapped[0])}</text>'
            )
            if len(wrapped) > 1:
                cy += 17
                items_svg.append(
                    f'<text x="{x + 38}" y="{cy}" font-size="11.5" font-weight="500" fill="{s["card_muted"]}">{esc_fn(wrapped[1])}</text>'
                )
            cy += 28

        cards.append(
            f'<g>'
            f'<rect x="{x}" y="102" width="284" height="334" rx="{rx}" fill="{s["card_bg"]}" stroke="{s["card_border"]}" stroke-width="1.5"/>'
            f'<rect x="{x}" y="102" width="284" height="6" rx="3" fill="{theme.secondary_hex}"/>'
            f'<rect x="{x + 20}" y="124" width="44" height="44" rx="10" fill="{theme.primary_hex}"/>'
            f'<text x="{x + 42}" y="152" text-anchor="middle" font-size="18" font-weight="900" fill="#FFFFFF">{num_badge}</text>'
            f'<text x="{x + 76}" y="142" font-size="10.5" font-weight="800" fill="{theme.accent_hex}" letter-spacing="0.8">{esc_fn(p.timeline.upper()[:22])}</text>'
            f'<text x="{x + 76}" y="160" font-size="11.5" font-weight="700" fill="{s["card_muted"]}">Lead: {esc_fn(p.owner[:24])}</text>'
            f'<text x="{x + 20}" y="198" font-size="15.5" font-weight="800" fill="{s["card_primary"]}">{esc_fn(p.phase[:30])}</text>'
            f'<line x1="{x + 20}" y1="214" x2="{x + 264}" y2="214" stroke="{s["grid_line"]}"/>'
            f'{"".join(items_svg)}'
            f'</g>'
        )
    return "".join(cards)


def render_quote_callout_body_svg(
    slide: SlideSpec,
    theme: ThemePalette,
    wrap_fn: Callable[[str, int, int], List[str]],
    esc_fn: Callable[[str], str],
    surface_fn: Callable[[ThemePalette], Dict[str, str]],
) -> str:
    """Renders a Customer Proof / Executive Quote Spotlight slide with 2 impact stat cards."""
    s = surface_fn(theme)
    rx = theme.card_radius
    quote = slide.quote_text or (
        "Standardizing our quarterly leadership briefings cut preparation time from five days to four hours "
        "while giving our board clearer visibility into customer retention and cash flow."
    )
    attrib = slide.quote_attribution or "Chief Operating Officer — Enterprise Customer Case Study"
    q_lines = wrap_fn(quote, 48, 4)
    q_svg = "".join(
        f'<text x="72" y="{206 + i * 28}" font-size="17" font-style="italic" font-weight="700" fill="{s["card_primary"]}">"{esc_fn(ln)}"</text>'
        if i == 0
        else f'<text x="72" y="{206 + i * 28}" font-size="17" font-style="italic" font-weight="700" fill="{s["card_primary"]}">{esc_fn(ln)}</text>'
        for i, ln in enumerate(q_lines)
    )
    kpis = list(slide.kpis[:2]) if slide.kpis else [
        KpiMetric(label="Time Saved per Review Cycle", value="84%", delta="-4.5 days prep", sentiment="positive"),
        KpiMetric(label="Return on Investment", value="6.4x", delta="Payback in 6 wks", sentiment="positive"),
    ]
    stat_cards = ""
    for idx, k in enumerate(kpis[:2]):
        ky = 102 + idx * 174
        stat_cards += (
            f'<rect x="616" y="{ky}" width="308" height="160" rx="{rx}" fill="{s["card_bg"]}" stroke="{s["card_border"]}" stroke-width="1.5"/>'
            f'<rect x="616" y="{ky}" width="8" height="160" rx="4" fill="{theme.secondary_hex}"/>'
            f'<text x="642" y="{ky + 38}" font-size="11.5" font-weight="800" fill="{s["card_muted"]}">{esc_fn(k.label.upper()[:32])}</text>'
            f'<text x="642" y="{ky + 94}" font-size="38" font-weight="900" fill="{s["card_primary"]}">{esc_fn(k.value[:14])}</text>'
            f'<text x="642" y="{ky + 130}" font-size="13" font-weight="800" fill="#15803D">▲ {esc_fn(k.delta[:26])}</text>'
        )
    return (
        f'<rect x="36" y="102" width="560" height="334" rx="{rx}" fill="{s["card_bg"]}" stroke="{s["card_border"]}" stroke-width="1.5"/>'
        f'<rect x="36" y="102" width="560" height="8" rx="4" fill="{theme.accent_hex}"/>'
        f'<text x="68" y="168" font-size="56" font-weight="900" fill="{theme.accent_hex}" opacity="0.32">“</text>'
        f'<text x="116" y="152" font-size="11.5" font-weight="800" fill="{theme.secondary_hex}" letter-spacing="1">VERIFIED CUSTOMER &amp; LEADERSHIP OUTCOME</text>'
        f"{q_svg}"
        f'<line x1="72" y1="348" x2="540" y2="348" stroke="{s["grid_line"]}"/>'
        f'<text x="72" y="380" font-size="13.5" font-weight="800" fill="{s["card_text"]}">— {esc_fn(attrib[:64])}</text>'
        f'<text x="72" y="402" font-size="11.5" font-weight="600" fill="{s["card_muted"]}">Quantified business impact shown on the right</text>'
        f"{stat_cards}"
    )
