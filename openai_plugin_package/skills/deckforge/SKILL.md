---
name: deckforge
description: Use when the user wants to turn meeting notes, written memos, spreadsheet numbers, or business metrics into a structured 6-slide presentation, change a slide layout, preview slides in 16:9, or export an editable PowerPoint (.pptx) file.
---

# DeckForge: Executive Slide Decks Workflow

1. When the user pastes meeting notes, a memo, or quarterly business metrics to turn into a presentation, call `transform_memo_to_slide_spec`.
   - Present the structured 6-slide outline, extracted KPI cards, chart series, financial table, and speaker talking points in plain business English.
2. When the user wants to change a specific slide's layout (such as `kpi_metrics_grid`, `bar_chart_slide`, `executive_summary`, `two_column_comparison`, `financial_table`, `executive_roadmap`, or `quote_callout`) or tighten its wording, call `remix_or_update_slide`.
3. When the user wants an editable PowerPoint (`.pptx`) presentation or 16:9 visual slide previews, call `generate_editable_pptx` and/or `generate_google_slides_batch_requests`.
