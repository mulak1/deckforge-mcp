"""
Strict Pydantic v2 schemas and immutable domain models for DeckForge.
Enforces boundary validation on colors, visual styles, chart configs, slide counts, audiences, and layouts.
"""

from __future__ import annotations

import re
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

SlideLayoutType = Literal[
    "title_hero",
    "executive_summary",
    "kpi_metrics_grid",
    "two_column_comparison",
    "bar_chart_slide",
    "financial_table",
    "executive_roadmap",
    "quote_callout",
]

ChartType = Literal[
    "vertical_bar",
    "horizontal_bar",
    "line_trend",
    "stacked_bar",
]

DesignStyleType = Literal[
    "classic_boardroom",
    "editorial_serif",
    "modern_minimal",
    "bold_keynote",
]

SentimentType = Literal["positive", "negative", "neutral"]

AudienceType = Literal["board", "leadership", "client", "team"]

DESIGN_STYLE_PRESETS: dict[DesignStyleType, dict[str, str | int]] = {
    "classic_boardroom": {
        "label": "Classic Boardroom",
        "description": "Solid executive header bar, crisp rounded cards, and clean geometric sans-serif.",
        "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        "card_radius": 10,
    },
    "editorial_serif": {
        "label": "Editorial Magazine",
        "description": "Refined serif headlines, open paper header with bottom accent rule, and crisp framing.",
        "font_family": "Georgia, 'Playfair Display', 'Times New Roman', serif",
        "card_radius": 4,
    },
    "modern_minimal": {
        "label": "Modern Swiss Grid",
        "description": "Architectural top-accent header, sharp grid geometry, and high-contrast numbers.",
        "font_family": "'Plus Jakarta Sans', Inter, system-ui, sans-serif",
        "card_radius": 2,
    },
    "bold_keynote": {
        "label": "Executive Keynote Dark",
        "description": "Dark-stage presentation canvas with elevated slate cards and luminous accents.",
        "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        "card_radius": 16,
    },
}


class ThemePalette(BaseModel):
    """Immutable brand color palette and architectural design style for presentations."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(default="Boardroom Navy", min_length=2, max_length=60, description="Display name of the presentation color palette")
    primary_hex: str = Field(default="#0B1F3A", description="Primary header and brand hex color (#RRGGBB)")
    secondary_hex: str = Field(default="#1D4ED8", description="Secondary accent hex color (#RRGGBB)")
    accent_hex: str = Field(default="#0EA5E9", description="Highlight and callout hex color (#RRGGBB)")
    background_hex: str = Field(default="#F8FAFC", description="Slide canvas background hex color (#RRGGBB)")
    text_hex: str = Field(default="#0F172A", description="Primary slide body text hex color (#RRGGBB)")
    muted_hex: str = Field(default="#64748B", description="Supporting caption and subtitle hex color (#RRGGBB)")
    style_family: DesignStyleType = Field(default="classic_boardroom", description="Architectural visual design style (classic_boardroom, editorial_serif, modern_minimal, or bold_keynote)")
    font_family: str = Field(default="Inter, -apple-system, BlinkMacSystemFont, sans-serif", max_length=120, description="Typography font stack used across slide headings and body copy")
    card_radius: int = Field(default=10, ge=0, le=28, description="Corner rounding radius in pixels for slide cards and callout boxes")

    @field_validator(
        "primary_hex",
        "secondary_hex",
        "accent_hex",
        "background_hex",
        "text_hex",
        "muted_hex",
    )
    @classmethod
    def validate_hex_color(cls, value: str) -> str:
        cleaned = value.strip()
        if not HEX_COLOR_RE.match(cleaned):
            raise ValueError(f"Invalid 6-digit hex color '{value}'. Expected #RRGGBB.")
        return cleaned.upper()


class KpiMetric(BaseModel):
    """Single quantified key metric card for summary slides."""

    model_config = ConfigDict(frozen=True)

    label: str = Field(..., min_length=1, max_length=80, description="Short business metric label (for example, Annual Recurring Revenue or Net Retention)")
    value: str = Field(..., min_length=1, max_length=40, description="Headline metric value with unit (for example, $18.4M or 124%)")
    delta: str = Field(default="", max_length=50, description="Period-over-period change or comparison badge (for example, +142% YoY)")
    sentiment: SentimentType = Field(default="positive", description="Directional indicator for the metric (positive, negative, or neutral)")


class ChartSeriesItem(BaseModel):
    """Data point for chart slides."""

    model_config = ConfigDict(frozen=True)

    category: str = Field(..., min_length=1, max_length=50, description="Period or category label on the chart axis (for example, Q1 Actual or North America)")
    value: float = Field(..., description="Actual numeric value for this category")
    target: Optional[float] = Field(default=None, description="Optional plan goal or target benchmark value for comparison")


class TableData(BaseModel):
    """Structured financial or operational table specification."""

    model_config = ConfigDict(frozen=True)

    headers: List[str] = Field(default_factory=list, max_length=8, description="Column headers for the slide table")
    rows: List[List[str]] = Field(default_factory=list, max_length=15, description="Table data rows where each row is a list of cell values")


class RoadmapPhase(BaseModel):
    """Action plan phase or summary pillar block with timeline/tag, owner, and deliverables."""

    model_config = ConfigDict(frozen=True)

    phase: str = Field(..., min_length=1, max_length=60, description="Name of the roadmap phase or strategic summary pillar")
    timeline: str = Field(..., min_length=1, max_length=40, description="Target timeframe or milestone window (for example, Weeks 1-4 or Q1)")
    owner: str = Field(default="Leadership Team", max_length=60, description="Team or leader responsible for delivering this phase")
    deliverables: List[str] = Field(default_factory=list, max_length=6, description="Concrete action items and milestones included in this phase")


class SlideSpec(BaseModel):
    """Specification for a single slide in a presentation."""

    model_config = ConfigDict(frozen=True)

    slide_number: int = Field(..., ge=1, le=50, description="1-based position of the slide in the presentation")
    layout_type: SlideLayoutType = Field(..., description="Visual layout template for this slide (title_hero, executive_summary, kpi_metrics_grid, two_column_comparison, bar_chart_slide, financial_table, executive_roadmap, or quote_callout)")
    action_title: str = Field(..., min_length=3, max_length=160, description="Headline takeaway at the top of the slide stating the main conclusion")
    subtitle: str = Field(default="", max_length=240, description="Supporting subtitle providing context under the main headline")
    takeaway_banner: str = Field(default="", max_length=220, description="Bottom-line summary sentence displayed in the slide footer callout bar")
    kpis: List[KpiMetric] = Field(default_factory=list, max_length=6, description="List of key metric cards displayed on KPI grid or quote spotlight slides")
    left_column_title: str = Field(default="Core Business Drivers", max_length=80, description="Heading for the left column on side-by-side comparison slides")
    left_bullets: List[str] = Field(default_factory=list, max_length=8, description="Bullet points for the left column on side-by-side comparison slides")
    right_column_title: str = Field(default="Growth & Expansion Priorities", max_length=80, description="Heading for the right column on side-by-side comparison slides")
    right_bullets: List[str] = Field(default_factory=list, max_length=8, description="Bullet points for the right column on side-by-side comparison slides")
    chart_title: str = Field(default="Quarterly Performance vs. Goal", max_length=100, description="Heading displayed above the chart canvas")
    chart_unit: str = Field(default="$M", max_length=20, description="Unit prefix or suffix for chart values (such as $M, %, or k)")
    chart_type: ChartType = Field(default="vertical_bar", description="Chart visualization style (vertical_bar, horizontal_bar, line_trend, or stacked_bar)")
    chart_show_target: bool = Field(default=True, description="Whether to display the plan/target benchmark series on the chart")
    chart_show_values: bool = Field(default=True, description="Whether to display numeric value labels directly on data points")
    chart_show_grid: bool = Field(default=True, description="Whether to display horizontal reference gridlines on the chart")
    chart_series: List[ChartSeriesItem] = Field(default_factory=list, max_length=12, description="Ordered data points for the slide chart")
    table: Optional[TableData] = Field(default=None, description="Structured headers and rows for financial or data table slides")
    roadmap_phases: List[RoadmapPhase] = Field(default_factory=list, max_length=5, description="Phases or strategic pillars for roadmap and executive summary slides")
    quote_text: str = Field(default="", max_length=420, description="Featured customer or leadership quote for quote callout slides")
    quote_attribution: str = Field(default="", max_length=140, description="Speaker name, role, and organization for the featured quote")
    speaker_notes: str = Field(default="", max_length=2000, description="Plain-English talking points for the presenter to deliver in the room")


class DeckSpec(BaseModel):
    """Complete presentation specification ready for slide export."""

    model_config = ConfigDict(frozen=True)

    title: str = Field(..., min_length=3, max_length=140, description="Overall presentation title shown on the cover slide and header")
    subtitle: str = Field(default="Leadership Strategy & Performance Review", max_length=220, description="Cover slide subtitle summarizing the purpose of the briefing")
    author: str = Field(default="Presentation Studio", max_length=80, description="Author or presenter name")
    organization: str = Field(default="Executive Operations", max_length=100, description="Company, organization, or department name")
    date_label: str = Field(default="Q4 2026", max_length=40, description="Reporting period or presentation date label")
    audience: AudienceType = Field(default="board", description="Target audience for tone and framing (board, leadership, client, or team)")
    footer_label: str = Field(default="Confidential — Leadership Briefing", max_length=80, description="Footer confidentiality or distribution note shown on every slide")
    theme: ThemePalette = Field(default_factory=ThemePalette, description="Color palette and architectural design style for the presentation")
    slides: List[SlideSpec] = Field(..., min_length=1, max_length=25, description="Ordered list of slides in the presentation")


ThemePresetName = Literal[
    "boardroom_navy",
    "executive_indigo",
    "modern_slate",
    "heritage_emerald",
    "royal_plum",
    "warm_terracotta",
    "pacific_atlas",
    "sage_report",
    "warm_sandstone",
    # Backward-compatible internal keys
    "mckinsey_navy",
    "stripe_indigo",
    "linear_obsidian",
    "sequoia_emerald",
    "pitch_violet",
    "gamma_editorial",
    "kimi_atlas",
    "kimi_jade",
    "miro_spatial",
]


class MemoTransformRequest(BaseModel):
    """Input boundary schema for transforming notes or memos into a slide deck."""

    model_config = ConfigDict(frozen=True)

    raw_memo: str = Field(..., min_length=20, max_length=50000, description="Raw meeting notes, written memo, bullet points, or quarterly business numbers to turn into slides")
    deck_title: str = Field(default="Executive Strategy & Performance Update", min_length=3, max_length=140, description="Title for the generated presentation")
    organization: str = Field(default="Northstar Enterprise", min_length=2, max_length=100, description="Company or team name displayed on the presentation")
    theme_preset: ThemePresetName = Field(default="boardroom_navy", description="Color palette preset (such as boardroom_navy, executive_indigo, modern_slate, heritage_emerald, or royal_plum)")
    target_slide_count: int = Field(default=6, ge=3, le=12, description="Target number of slides to generate (between 3 and 12, default 6)")
    audience: AudienceType = Field(default="board", description="Target audience for slide headlines and talking points (board, leadership, client, or team)")
    footer_label: str = Field(default="Confidential — Leadership Briefing", max_length=80, description="Confidentiality note or footer text displayed across all slides")


class GeneratePptxRequest(BaseModel):
    """Input boundary schema for generating an editable PowerPoint file."""

    model_config = ConfigDict(frozen=True)

    deck_spec: DeckSpec = Field(..., description="Structured presentation specification containing title, theme, and slides")
    api_key: str = Field(default="df_free_demo", min_length=3, max_length=120, description="Optional account plan key (works immediately without setup; use default or df_pro_enterprise)")


class GoogleSlidesExportRequest(BaseModel):
    """Input boundary schema for generating online slide payloads and previews."""

    model_config = ConfigDict(frozen=True)

    deck_spec: DeckSpec = Field(..., description="Structured presentation specification to render as 16:9 visual slide previews and online slide elements")
    presentation_id: str = Field(
        default="1DeckForgePresId_AutoGenerated",
        min_length=4,
        max_length=128,
        description="Identifier for the target online presentation deck",
    )


class SlideRemixRequest(BaseModel):
    """Input boundary schema for changing a single slide's layout, chart type, or wording."""

    model_config = ConfigDict(frozen=True)

    deck_spec: DeckSpec = Field(..., description="Current presentation specification containing the slide to update")
    slide_number: int = Field(default=1, ge=1, le=50, description="1-based slide number to update or change layout")
    new_layout_type: Optional[SlideLayoutType] = Field(default=None, description="Optional new slide layout template (such as kpi_metrics_grid, bar_chart_slide, executive_summary, financial_table, executive_roadmap, or quote_callout)")
    chart_type: Optional[ChartType] = Field(default=None, description="Optional chart style when using a chart layout (vertical_bar, horizontal_bar, line_trend, or stacked_bar)")
    polish_mode: bool = Field(
        default=True,
        description="Tighten the slide headline, key takeaway, and talking points in plain business English",
    )
    action_title: Optional[str] = Field(default=None, min_length=3, max_length=160, description="Optional custom headline override for the slide")
    takeaway_banner: Optional[str] = Field(default=None, max_length=220, description="Optional custom bottom takeaway sentence override for the slide")


class DataImportRequest(BaseModel):
    """Input boundary schema for importing CSV, TSV, or spreadsheet rows into a Table or Chart slide."""

    model_config = ConfigDict(frozen=True)

    raw_tabular_text: str = Field(..., min_length=5, max_length=50000, description="Raw CSV, TSV, pipe-separated, or spreadsheet rows including a header row")
    target_mode: Literal["table", "chart"] = Field(default="table", description="Whether to import the data as a formatted Table slide ('table') or Data Chart slide ('chart')")
    chart_type: ChartType = Field(default="vertical_bar", description="Chart visualization style if importing as a chart")
    chart_unit: str = Field(default="$M", max_length=20, description="Unit label for chart values (such as $M, %, or k)")
    slide_title: str = Field(default="Imported Performance Data & Key Trends", min_length=3, max_length=160, description="Headline takeaway for the imported data slide")
    deck_spec: Optional[DeckSpec] = Field(default=None, description="Optional existing presentation to append or update with the imported slide")
    replace_slide_number: Optional[int] = Field(default=None, ge=1, le=25, description="Optional 1-based slide number to replace instead of appending a new slide")


PRIMARY_THEMES: dict[str, ThemePalette] = {
    "boardroom_navy": ThemePalette(
        name="Boardroom Navy", primary_hex="#0B1F3A", secondary_hex="#1D4ED8", accent_hex="#0284C7",
        background_hex="#F8FAFC", text_hex="#0F172A", muted_hex="#475569", style_family="classic_boardroom",
    ),
    "executive_indigo": ThemePalette(
        name="Executive Indigo", primary_hex="#1E1B4B", secondary_hex="#4F46E5", accent_hex="#06B6D4",
        background_hex="#F9FAFB", text_hex="#111827", muted_hex="#4B5563", style_family="modern_minimal",
        font_family="'Plus Jakarta Sans', Inter, system-ui, sans-serif", card_radius=4,
    ),
    "modern_slate": ThemePalette(
        name="Modern Slate", primary_hex="#090D16", secondary_hex="#3B82F6", accent_hex="#38BDF8",
        background_hex="#0F172A", text_hex="#F8FAFC", muted_hex="#CBD5E1", style_family="bold_keynote",
        card_radius=16,
    ),
    "heritage_emerald": ThemePalette(
        name="Heritage Emerald", primary_hex="#064E3B", secondary_hex="#059669", accent_hex="#10B981",
        background_hex="#F8FAFC", text_hex="#0F172A", muted_hex="#475569", style_family="editorial_serif",
        font_family="Georgia, 'Playfair Display', serif", card_radius=4,
    ),
    "royal_plum": ThemePalette(
        name="Royal Plum", primary_hex="#1E1035", secondary_hex="#7C3AED", accent_hex="#A855F7",
        background_hex="#FAF8FF", text_hex="#130A24", muted_hex="#5B4B73", style_family="classic_boardroom",
    ),
    "warm_terracotta": ThemePalette(
        name="Warm Terracotta", primary_hex="#2C1810", secondary_hex="#D97706", accent_hex="#EA580C",
        background_hex="#FFFDF9", text_hex="#1C1917", muted_hex="#78716C", style_family="editorial_serif",
        font_family="Georgia, 'Playfair Display', serif", card_radius=4,
    ),
    "pacific_atlas": ThemePalette(
        name="Pacific Blue", primary_hex="#071936", secondary_hex="#0284C7", accent_hex="#38BDF8",
        background_hex="#F0F7FF", text_hex="#082F49", muted_hex="#475569", style_family="modern_minimal",
        font_family="'Plus Jakarta Sans', Inter, system-ui, sans-serif", card_radius=2,
    ),
    "sage_report": ThemePalette(
        name="Sage & Gold", primary_hex="#0B2E26", secondary_hex="#0D9488", accent_hex="#F59E0B",
        background_hex="#F7FBF9", text_hex="#0F2922", muted_hex="#4B635C", style_family="editorial_serif",
        font_family="Georgia, 'Playfair Display', serif", card_radius=4,
    ),
    "warm_sandstone": ThemePalette(
        name="Warm Sandstone", primary_hex="#18181B", secondary_hex="#2563EB", accent_hex="#F59E0B",
        background_hex="#FEFCE8", text_hex="#18181B", muted_hex="#52525B", style_family="modern_minimal",
        font_family="'Plus Jakarta Sans', Inter, system-ui, sans-serif", card_radius=4,
    ),
}

THEME_PRESETS: dict[str, ThemePalette] = {
    **PRIMARY_THEMES,
    "mckinsey_navy": PRIMARY_THEMES["boardroom_navy"],
    "stripe_indigo": PRIMARY_THEMES["executive_indigo"],
    "linear_obsidian": PRIMARY_THEMES["modern_slate"],
    "sequoia_emerald": PRIMARY_THEMES["heritage_emerald"],
    "pitch_violet": PRIMARY_THEMES["royal_plum"],
    "gamma_editorial": PRIMARY_THEMES["warm_terracotta"],
    "kimi_atlas": PRIMARY_THEMES["pacific_atlas"],
    "kimi_jade": PRIMARY_THEMES["sage_report"],
    "miro_spatial": PRIMARY_THEMES["warm_sandstone"],
}
