"""
Spreadsheet / CSV / TSV / Excel-Paste Data Importer and 8 Curated Business Templates for DeckForge.
Supports importing tabular data directly into either a Financial/Data Table slide or a 4-mode Chart slide.
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any, Dict, List

from src.models import (
    ChartSeriesItem,
    DataImportRequest,
    MemoTransformRequest,
    SlideSpec,
    TableData,
    ThemePalette,
)
from src.svg_renderer import render_slide_svg_card

NUMERIC_CLEAN_RE = re.compile(r"[^0-9.\-]")


def _parse_raw_rows(raw_text: str) -> List[List[str]]:
    lines = [ln.strip() for ln in raw_text.strip().splitlines() if ln.strip()]
    if not lines:
        return []
    first = lines[0]
    if "\t" in first:
        return [[c.strip() for c in ln.split("\t") if c.strip() != ""] for ln in lines]
    if "|" in first:
        rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in lines]
        # Skip markdown separator lines like |---|---|
        return [r for r in rows if not all(set(c) <= {"-", ":"} for c in r if c)]
    delimiter = ";" if (";" in first and "," not in first) else ","
    reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=delimiter)
    return [[c.strip() for c in row if c is not None] for row in reader if any(c.strip() for c in row)]


def _to_float(val: str) -> float | None:
    cleaned = NUMERIC_CLEAN_RE.sub("", str(val or ""))
    if not cleaned or cleaned in ("-", ".", "-."):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def import_tabular_data_to_slide(req: DataImportRequest | Dict[str, Any]) -> Dict[str, Any]:
    """Parses CSV, TSV, pipe-delimited, or Excel-pasted rows into a Table slide or Chart slide."""
    parsed = req if isinstance(req, DataImportRequest) else DataImportRequest.model_validate(req)
    raw_rows = _parse_raw_rows(parsed.raw_tabular_text)
    if len(raw_rows) < 2:
        raise ValueError("Please provide at least a header row and one data row (CSV, TSV, or pasted cells).")

    headers = [h[:36] for h in raw_rows[0][:8]]
    data_rows = [[c[:36] for c in r[: len(headers)]] for r in raw_rows[1:13] if r]

    slide_num = parsed.replace_slide_number or (len(parsed.deck_spec.slides) + 1 if parsed.deck_spec else 1)

    if parsed.target_mode == "chart":
        series: List[ChartSeriesItem] = []
        for r in data_rows[:10]:
            if len(r) < 2:
                continue
            cat = r[0] or f"Item {len(series) + 1}"
            val = _to_float(r[1])
            if val is None:
                continue
            target_val = _to_float(r[2]) if len(r) >= 3 else None
            series.append(ChartSeriesItem(category=cat[:40], value=val, target=target_val))
        if not series:
            raise ValueError("Could not find numeric values in the second column to build a chart.")

        peak = max(series, key=lambda item: item.value)
        new_slide = SlideSpec(
            slide_number=slide_num,
            layout_type="bar_chart_slide",
            action_title=parsed.slide_title,
            subtitle=f"Imported {len(series)} data points from spreadsheet ({headers[0]} vs. {headers[1] if len(headers) > 1 else 'Value'})",
            chart_title=parsed.slide_title[:80],
            chart_unit=parsed.chart_unit,
            chart_type=parsed.chart_type,
            chart_series=series,
            takeaway_banner=f"Highest performance recorded in {peak.category} at {peak.value}{parsed.chart_unit}.",
            speaker_notes=f"Walk through the imported chart series across {len(series)} categories, highlighting {peak.category}.",
        )
    else:
        new_slide = SlideSpec(
            slide_number=slide_num,
            layout_type="financial_table",
            action_title=parsed.slide_title,
            subtitle=f"Structured data table imported with {len(headers)} columns and {len(data_rows)} rows",
            table=TableData(headers=headers, rows=data_rows),
            takeaway_banner=f"Summary table covering {len(data_rows)} key rows across {', '.join(headers[:3])}.",
            speaker_notes="Review the imported table rows and call out the bottom-line figures.",
        )

    theme = parsed.deck_spec.theme if parsed.deck_spec else ThemePalette()
    deck_title = parsed.deck_spec.title if parsed.deck_spec else parsed.slide_title
    footer = parsed.deck_spec.footer_label if parsed.deck_spec else "Confidential — Leadership Briefing"

    updated_deck_dump = None
    if parsed.deck_spec:
        slides = list(parsed.deck_spec.slides)
        if parsed.replace_slide_number and 1 <= parsed.replace_slide_number <= len(slides):
            slides[parsed.replace_slide_number - 1] = new_slide
        elif len(slides) < 25:
            slides.append(new_slide.model_copy(update={"slide_number": len(slides) + 1}))
        updated_deck = parsed.deck_spec.model_copy(update={"slides": slides})
        updated_deck_dump = updated_deck.model_dump(mode="json")

    return {
        "status": "success",
        "target_mode": parsed.target_mode,
        "rows_imported": len(data_rows),
        "columns_imported": len(headers),
        "slide": new_slide.model_dump(mode="json"),
        "slide_svg": render_slide_svg_card(new_slide, theme, deck_title, footer),
        "deck_spec": updated_deck_dump,
    }


PRESET_CONFIGS: List[Dict[str, Any]] = [
    {
        "id": "series_a_board",
        "label": "Series A Board Update",
        "badge": "Board & Investors",
        "description": "6-slide Boardroom Navy update with revenue growth, net customer retention, P&L table & 90-day plan.",
        "req": MemoTransformRequest(
            raw_memo=(
                "Series A Board Update: ARR reached $18.4M (+142% YoY), Net Dollar Retention hit 124%, "
                "Gross Margin expanded to 81.2% (+420 bps), CAC Payback dropped to 9.5 mos. "
                "Q1: $11.2M, Q2: $14.5M, Q3: $18.4M, Q4: $23.0M. "
                "- Self-serve customer referrals drove 68% of new customer additions with zero paid ad spend.\n"
                "- Average annual contract value expanded to $48k across 42 multi-department enterprise accounts.\n"
                "- Standardized onboarding templates saved account teams 6.5 hours of manual preparation per client.\n"
                "- Positive Free Cash Flow (+4.2% margin) achieved two quarters ahead of the annual plan."
            ),
            deck_title="Series A Board of Directors Update — Q3 2026",
            organization="Northstar Enterprise Corp",
            theme_preset="boardroom_navy",
            target_slide_count=6,
            audience="board",
        ),
    },
    {
        "id": "q3_saas_review",
        "label": "Q3 SaaS Revenue & Retention Review",
        "badge": "Sales & Finance",
        "description": "Executive Indigo quarterly business review covering net new revenue, customer renewals & pipeline.",
        "req": MemoTransformRequest(
            raw_memo=(
                "Q3 SaaS Revenue Review: Net New ARR reached $4.9M (+88% YoY), Enterprise NRR hit 131%, "
                "Logo Retention at 96.4% (+180 bps), Magic Number reached 1.4x. "
                "Q1: $9.8M, Q2: $13.1M, Q3: $18.0M, Q4: $24.2M. "
                "- Multi-product adoption increased from 22% to 47% across mid-market customer accounts.\n"
                "- Seat expansion in existing accounts contributed 39% of third-quarter net new revenue.\n"
                "- Average sales cycle shortened from 46 days to 21 days using clear ROI business cases.\n"
                "- International customer renewals and upgrades grew 210% quarter-over-quarter."
            ),
            deck_title="Q3 SaaS Revenue, Retention & GTM Efficiency Review",
            organization="Meridian Commercial Group",
            theme_preset="executive_indigo",
            target_slide_count=6,
            audience="leadership",
        ),
    },
    {
        "id": "enterprise_launch",
        "label": "Enterprise Product Launch Strategy",
        "badge": "Product & Go-To-Market",
        "description": "Heritage Emerald rollout plan with customer pilot metrics, adoption rates & launch milestones.",
        "req": MemoTransformRequest(
            raw_memo=(
                "Enterprise Launch Strategy: Design Partner Pipeline reached $12.6M (+195% QoQ), "
                "Weekly Active Teams hit 84.5% (+12% MoM), Time-to-First-Deck dropped to 38s, "
                "Security Audit Score reached 98%. Q1: $4.0M, Q2: $7.5M, Q3: $12.6M, Q4: $19.5M. "
                "- Completed 40 customer pilot programs across finance, operations, and regional sales teams.\n"
                "- Works out of the box with standard presentation software across desktop and web.\n"
                "- Completed independent security and privacy review for regulated enterprise buyers.\n"
                "- Self-serve team plan ($24/month) converts pilot teams after their first 3 presentations."
            ),
            deck_title="Enterprise Product Rollout & Go-To-Market Plan",
            organization="Vanguard Operations Suite",
            theme_preset="heritage_emerald",
            target_slide_count=6,
            audience="client",
        ),
    },
    {
        "id": "annual_operations_report",
        "label": "Annual Operations & Productivity Report",
        "badge": "Executive Briefing",
        "description": "Pacific Blue executive briefing on operational efficiency, unit cost reduction & team adoption.",
        "req": MemoTransformRequest(
            raw_memo=(
                "Annual Operations Report: Annual Cost Savings reached $34.2M (+215% YoY), "
                "Unit Cost Reduction hit 78.5%, Cross-Team Adoption Rate at 91.4% (+340 bps), "
                "On-Time Project Delivery reached 88.6%. Q1: $14.0M, Q2: $21.5M, Q3: $28.8M, Q4: $34.2M. "
                "- Standardized reporting templates replaced 74% of manual weekly spreadsheet formatting.\n"
                "- Connected sales, finance, and operations numbers into a single weekly leadership scorecard.\n"
                "- Monthly financial close and board pack preparation dropped from 5 days to 1 day.\n"
                "- Regulated financial services and healthcare client accounts expanded 3.1x year-over-year."
            ),
            deck_title="2026 Annual Operations & Productivity Impact Report",
            organization="Horizon Advisory Group",
            theme_preset="pacific_atlas",
            target_slide_count=6,
            audience="board",
        ),
    },
    {
        "id": "customer_discovery_roadmap",
        "label": "Customer Research & 90-Day Roadmap",
        "badge": "Product & Operations",
        "description": "Warm Sandstone planning deck mapping customer research findings, delivery pace & 3-phase release plan.",
        "req": MemoTransformRequest(
            raw_memo=(
                "Customer Discovery Synthesis: Validated Enterprise Prototype Score reached 92.4% (+28% QoQ), "
                "Quarterly Delivery Volume hit 14.2M, Trial-to-Paid Conversion at 64.8% (+890 bps), "
                "Customer Effort Time dropped to 4.2 mos. Q1: $6.4M, Q2: $9.2M, Q3: $13.8M, Q4: $18.9M. "
                "- Visual storyboard reviews helped product and sales teams agree on quarterly priorities 3x faster.\n"
                "- Shared company color palettes kept customer presentation decks consistent across 18 regional teams.\n"
                "- Side-by-side slide previews and 1-page read-ahead briefs cut meeting review cycles in half.\n"
                "- Clear phase owners and weekly check-ins kept 94% of quarterly milestones on schedule."
            ),
            deck_title="Customer Discovery Findings & 90-Day Delivery Roadmap",
            organization="Summit Product Group",
            theme_preset="warm_sandstone",
            target_slide_count=6,
            audience="team",
        ),
    },
    {
        "id": "ma_strategic_partnership",
        "label": "M&A & Strategic Partnership Proposal",
        "badge": "Board & Strategy",
        "description": "Royal Plum acquisition & partnership briefing with combined revenue synergies & integration plan.",
        "req": MemoTransformRequest(
            raw_memo=(
                "Strategic Partnership & M&A Memo: Combined Annual Revenue reached $64.0M (+48% YoY), "
                "Annual Cost Synergies hit $8.5M, Cross-Sell Account Overlap at 72%, Accretion Timeline dropped to 6.0 mos. "
                "Q1: $48.0M, Q2: $53.5M, Q3: $58.2M, Q4: $64.0M. "
                "- Combining regional distribution teams unlocks 140 enterprise accounts in Europe and North America.\n"
                "- Shared procurement and cloud infrastructure saves $8.5M in annual operating expenses.\n"
                "- 90-day post-close integration plan retains 100% of key engineering and account leadership."
            ),
            deck_title="Strategic Acquisition & Partnership Value Evaluation",
            organization="Sterling Capital & Corporate Development",
            theme_preset="royal_plum",
            target_slide_count=6,
            audience="board",
        ),
    },
    {
        "id": "cfo_budget_vs_actuals",
        "label": "CFO Quarterly Financial Close & Budget Review",
        "badge": "Finance & FP&A",
        "description": "Sage & Gold financial close deck comparing budget vs. actuals, EBITDA margin, and cash runway.",
        "req": MemoTransformRequest(
            raw_memo=(
                "Quarterly CFO Financial Close: Net Operating Revenue reached $38.6M (+29% YoY), "
                "Adjusted EBITDA Margin hit 26.4% (+410 bps), Free Cash Flow Conversion at 89.2%, "
                "Operating Expense Variance dropped to 1.8%. Q1: $29.4M, Q2: $32.1M, Q3: $35.0M, Q4: $38.6M. "
                "- Disciplined vendor consolidation reduced annual software and G&A overhead by $2.4M.\n"
                "- Net working capital efficiency improved by 11 days through automated invoicing.\n"
                "- Cash reserves increased to $54.0M with zero debt drawdown required."
            ),
            deck_title="Q4 CFO Financial Close & Budget vs. Actuals Review",
            organization="Crestview Financial Holdings",
            theme_preset="sage_report",
            target_slide_count=6,
            audience="leadership",
        ),
    },
    {
        "id": "customer_case_study_roi",
        "label": "Enterprise Customer Case Study & ROI Proof",
        "badge": "Client & Sales Proposal",
        "description": "Warm Terracotta client impact story showcasing verified savings, payback speed & deployment timeline.",
        "req": MemoTransformRequest(
            raw_memo=(
                "Customer ROI Case Study: Verified Annual Savings reached $4.8M (+165% YoY), "
                "Team Productivity Gain hit 68%, Deployment Speed reached 96%, Payback Period dropped to 3.5 mos. "
                "Q1: $1.4M, Q2: $2.6M, Q3: $3.7M, Q4: $4.8M. "
                "- Eliminated 18 hours per week of manual status reporting across 120 project managers.\n"
                "- Executive stakeholders approved Phase 2 expansion within 45 days of initial launch.\n"
                "- Dedicated customer success onboarding achieved 94% weekly active adoption in month one."
            ),
            deck_title="Customer Impact Case Study & Verified ROI Briefing",
            organization="beacon Commercial Advisory",
            theme_preset="warm_terracotta",
            target_slide_count=6,
            audience="client",
        ),
    },
]
