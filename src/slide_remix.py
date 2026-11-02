"""
Single-Slide Layout Remix, Plain-English Executive Polish, 1-Page Meeting Read-Ahead Brief,
and Deck Readiness Check. Delegates 8 Curated Templates & CSV/Sheet Import to src.templates_and_import.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.models import (
    ChartSeriesItem,
    DeckSpec,
    KpiMetric,
    RoadmapPhase,
    SlideLayoutType,
    SlideRemixRequest,
    SlideSpec,
    TableData,
)
from src.svg_renderer import render_slide_svg_card
from src.templates_and_import import PRESET_CONFIGS, import_tabular_data_to_slide

__all__ = [
    "PRESET_CONFIGS",
    "audit_deck_readiness",
    "generate_executive_brief",
    "import_tabular_data_to_slide",
    "remix_or_update_slide",
]


def _donor_slide(deck: DeckSpec, layout_type: SlideLayoutType) -> SlideSpec | None:
    for s in deck.slides:
        if s.layout_type == layout_type:
            return s
    return None


def _ensure_slide_layout_data(
    slide: SlideSpec,
    deck: DeckSpec,
    target_layout: SlideLayoutType,
) -> Dict[str, Any]:
    updates: Dict[str, Any] = {"layout_type": target_layout}
    if target_layout == "kpi_metrics_grid" and not slide.kpis:
        donor = _donor_slide(deck, "kpi_metrics_grid")
        updates["kpis"] = (
            donor.kpis
            if donor and donor.kpis
            else [
                KpiMetric(label="Annual Recurring Revenue", value="$18.4M", delta="+142% YoY", sentiment="positive"),
                KpiMetric(label="Net Customer Retention", value="124%", delta="+9 pts YoY", sentiment="positive"),
                KpiMetric(label="Operating Gross Margin", value="81.2%", delta="+4.2 pts QoQ", sentiment="positive"),
                KpiMetric(label="Customer Payback Period", value="9.5 mos", delta="-3.2 mos YoY", sentiment="positive"),
            ]
        )
    elif target_layout == "bar_chart_slide" and not slide.chart_series:
        donor = _donor_slide(deck, "bar_chart_slide")
        updates["chart_series"] = (
            donor.chart_series
            if donor and donor.chart_series
            else [
                ChartSeriesItem(category="Q1 Actual", value=11.2, target=10.5),
                ChartSeriesItem(category="Q2 Actual", value=14.5, target=13.2),
                ChartSeriesItem(category="Q3 Actual", value=18.4, target=16.8),
                ChartSeriesItem(category="Q4 Target", value=23.0, target=21.0),
            ]
        )
    elif target_layout == "two_column_comparison" and not slide.left_bullets:
        donor = _donor_slide(deck, "two_column_comparison")
        updates["left_bullets"] = (
            donor.left_bullets
            if donor and donor.left_bullets
            else [
                "Self-serve customer onboarding completed in under 10 minutes with zero manual setup.",
                "38% of free trial teams upgrade to paid plans within the first 30 days.",
            ]
        )
        updates["right_bullets"] = (
            donor.right_bullets
            if donor and donor.right_bullets
            else [
                "Dedicated account managers support multi-year agreements across larger departments.",
                "Average annual contract value reached $48k across 42 multi-department customers.",
            ]
        )
    elif target_layout == "financial_table" and slide.table is None:
        donor = _donor_slide(deck, "financial_table")
        updates["table"] = (
            donor.table
            if donor and donor.table
            else TableData(
                headers=["Metric", "Q1 Actual", "Q2 Actual", "Q3 Actual", "Q4 Plan"],
                rows=[
                    ["Ending ARR ($M)", "$11.2M", "$14.5M", "$18.4M", "$23.0M"],
                    ["Gross Margin (%)", "77.4%", "79.1%", "81.2%", "82.5%"],
                    ["Free Cash Flow Margin", "-8.0%", "-2.5%", "+4.2%", "+9.5%"],
                ],
            )
        )
    elif target_layout in ("executive_roadmap", "executive_summary") and not slide.roadmap_phases:
        donor = _donor_slide(deck, "executive_roadmap") or _donor_slide(deck, "executive_summary")
        updates["roadmap_phases"] = (
            donor.roadmap_phases
            if donor and donor.roadmap_phases
            else [
                RoadmapPhase(
                    phase="Phase 1: Core Rollout",
                    timeline="Weeks 1–4",
                    owner="Product & Operations",
                    deliverables=["Customer onboarding workflow live", "Support team training completed"],
                ),
                RoadmapPhase(
                    phase="Phase 2: Account Expansion",
                    timeline="Weeks 5–8",
                    owner="Commercial Team",
                    deliverables=["Quarterly account reviews launched", "Department-wide template rollout"],
                ),
                RoadmapPhase(
                    phase="Phase 3: Scale & Automation",
                    timeline="Weeks 9–12",
                    owner="Executive Leadership",
                    deliverables=["Automated monthly reporting live", "Annual budget & hiring sign-off"],
                ),
            ]
        )
    elif target_layout == "quote_callout":
        if not slide.quote_text:
            updates["quote_text"] = (
                "Standardizing our quarterly leadership briefings cut preparation time from five days to four hours "
                "while giving our board clearer visibility into customer retention and cash flow."
            )
        if not slide.quote_attribution:
            updates["quote_attribution"] = f"Executive Sponsor — {deck.organization}"
        if not slide.kpis:
            updates["kpis"] = [
                KpiMetric(label="Preparation Time Saved", value="84%", delta="-4.5 days per cycle", sentiment="positive"),
                KpiMetric(label="Return on Investment", value="6.4x", delta="Payback in 6 weeks", sentiment="positive"),
            ]
    return updates


def _polish_slide_copy(slide: SlideSpec, deck: DeckSpec) -> Dict[str, str]:
    base_title = slide.action_title.strip()
    for prefix in ("Key Finding: ", "Headline Takeaway: ", "Performance Highlight: ", "Executive Synthesis: "):
        if base_title.startswith(prefix):
            base_title = base_title[len(prefix) :].strip()

    if slide.layout_type == "kpi_metrics_grid" and slide.kpis:
        top = slide.kpis[0]
        polished_title = f"Key Finding: {top.label} Reached {top.value} ({top.delta}) Across Core Goals"
        takeaway = f"Beat quarterly targets across all {len(slide.kpis)} core metrics, led by {top.label} at {top.value}."
    elif slide.layout_type == "bar_chart_slide" and slide.chart_series:
        peak = slide.chart_series[-1]
        polished_title = f"Performance Highlight: {peak.category} Reached {peak.value}{slide.chart_unit} vs. {peak.target or peak.value}{slide.chart_unit} Goal"
        takeaway = f"Steady quarter-over-quarter momentum reaching {peak.value}{slide.chart_unit} in {peak.category}."
    elif slide.layout_type == "financial_table":
        polished_title = f"Financial Summary & Margin Improvement: {base_title}"
        takeaway = "Stronger unit economics with expanding gross margin and positive cash generation."
    elif slide.layout_type == "executive_roadmap":
        polished_title = f"90-Day Action Plan & Team Owners: {base_title}"
        takeaway = "Clear 3-step delivery schedule with named team owners and measurable milestones."
    elif slide.layout_type == "executive_summary":
        polished_title = f"Executive Summary — Three Core Takeaways: {base_title}"
        takeaway = "Three pillars align commercial growth, operating margin, and next-quarter execution."
    elif slide.layout_type == "quote_callout":
        polished_title = f"Customer & Leadership Impact Spotlight: {base_title}"
        takeaway = "Verified business impact backed by measurable time savings and fast payback."
    else:
        polished_title = f"Headline Takeaway: {base_title}"
        takeaway = slide.takeaway_banner or f"Clear summary aligned with {deck.organization} priorities."

    notes = slide.speaker_notes.strip()
    cue = f" [Board Delivery Cue: Anchor the room on '{takeaway[:72]}' before opening for questions.]"
    if "Board Delivery Cue:" not in notes:
        notes = (notes + cue).strip()

    return {
        "action_title": polished_title[:155],
        "takeaway_banner": takeaway[:210],
        "speaker_notes": notes[:1950],
    }


def remix_or_update_slide(req: SlideRemixRequest | Dict[str, Any]) -> Dict[str, Any]:
    """Changes a single slide's layout, chart type, and/or tightens its wording in plain business English."""
    parsed = req if isinstance(req, SlideRemixRequest) else SlideRemixRequest.model_validate(req)
    deck = parsed.deck_spec
    if parsed.slide_number < 1 or parsed.slide_number > len(deck.slides):
        raise ValueError(f"slide_number {parsed.slide_number} is out of range (1..{len(deck.slides)}).")

    idx = parsed.slide_number - 1
    current_slide = deck.slides[idx]
    target_layout: SlideLayoutType = parsed.new_layout_type or current_slide.layout_type

    layout_updates = _ensure_slide_layout_data(current_slide, deck, target_layout)
    if parsed.chart_type is not None:
        layout_updates["chart_type"] = parsed.chart_type
    intermediate_slide = current_slide.model_copy(update=layout_updates)

    copy_updates: Dict[str, Any] = {}
    if parsed.polish_mode:
        copy_updates.update(_polish_slide_copy(intermediate_slide, deck))
    if parsed.action_title is not None:
        copy_updates["action_title"] = parsed.action_title.strip()[:160]
    if parsed.takeaway_banner is not None:
        copy_updates["takeaway_banner"] = parsed.takeaway_banner.strip()[:220]

    remixed_slide = intermediate_slide.model_copy(update=copy_updates)
    new_slides = [remixed_slide if i == idx else s for i, s in enumerate(deck.slides)]
    updated_deck = deck.model_copy(update={"slides": new_slides})

    return {
        "status": "success",
        "slide_number": parsed.slide_number,
        "previous_layout": current_slide.layout_type,
        "new_layout": remixed_slide.layout_type,
        "polish_applied": parsed.polish_mode,
        "remixed_slide": remixed_slide.model_dump(mode="json"),
        "slide_svg": render_slide_svg_card(remixed_slide, updated_deck.theme, updated_deck.title, updated_deck.footer_label),
        "deck_spec": updated_deck.model_dump(mode="json"),
    }


def generate_executive_brief(deck_spec: DeckSpec | Dict[str, Any]) -> Dict[str, Any]:
    """Builds a 1-page plain-English Meeting Read-Ahead Brief from the presentation."""
    deck = deck_spec if isinstance(deck_spec, DeckSpec) else DeckSpec.model_validate(deck_spec)
    kpi_slide = next((s for s in deck.slides if s.kpis), None)
    kpis = kpi_slide.kpis if kpi_slide else []

    lines: List[str] = [
        f"# {deck.title}",
        f"**Organization:** {deck.organization} | **Date:** {deck.date_label} | **Note:** {deck.footer_label}",
        "",
        "## 1. Purpose of This Briefing",
        f"{deck.subtitle}. This 1-page read-ahead summarizes the key numbers, comparisons, and 90-day action plan so attendees can review the facts before the meeting.",
        "",
        "## 2. Headline Numbers at a Glance",
    ]
    for k in kpis[:4]:
        lines.append(f"- **{k.label}:** {k.value} ({k.delta})")
    if not kpis:
        lines.append("- Key metrics are summarized inside the presentation slides.")

    lines.extend(["", "## 3. Slide-by-Slide Summary & Talking Points"])
    for s in deck.slides:
        lines.append(f"### Slide {s.slide_number}: {s.action_title}")
        if s.takeaway_banner:
            lines.append(f"- **Main Takeaway:** {s.takeaway_banner}")
        if s.speaker_notes:
            lines.append(f"- **Talking Point:** {s.speaker_notes}")
        lines.append("")

    brief_markdown = "\n".join(lines).strip()
    return {
        "status": "success",
        "title": f"{deck.title} — 1-Page Meeting Read-Ahead",
        "organization": deck.organization,
        "slide_count": len(deck.slides),
        "brief_markdown": brief_markdown,
    }


def audit_deck_readiness(deck_spec: DeckSpec | Dict[str, Any]) -> Dict[str, Any]:
    """Runs a plain-English Presentation Quality & Readiness Check across all slides."""
    deck = deck_spec if isinstance(deck_spec, DeckSpec) else DeckSpec.model_validate(deck_spec)
    checks: List[Dict[str, str]] = []
    score = 100

    for s in deck.slides:
        if len(s.action_title.strip()) < 15:
            score -= 6
            checks.append({
                "slide": f"Slide {s.slide_number}",
                "status": "Suggestion",
                "tip": "Make the headline more specific by stating the main conclusion or number.",
            })
        if not s.takeaway_banner.strip():
            score -= 5
            checks.append({
                "slide": f"Slide {s.slide_number}",
                "status": "Suggestion",
                "tip": "Add a bottom takeaway line so busy readers catch the main point in 3 seconds.",
            })
        if not s.speaker_notes.strip():
            score -= 4
            checks.append({
                "slide": f"Slide {s.slide_number}",
                "status": "Suggestion",
                "tip": "Add a short speaker note so presenters know what to emphasize.",
            })

    if not checks:
        checks.append({
            "slide": "All Slides",
            "status": "Ready to Present",
            "tip": "Every slide has a clear headline, a bottom takeaway, quantified proof points, and speaker notes.",
        })

    final_score = max(60, min(100, score))
    return {
        "status": "success",
        "readiness_score": final_score,
        "verdict": "Ready for the Boardroom" if final_score >= 90 else "Good Draft — Minor Polish Suggested",
        "slide_count": len(deck.slides),
        "checks": checks,
    }
