"""
Public HTML Pages for DeckForge MCP (/docs, /documentation, /about, /privacy, /terms).
Designed for End Users, IT Administrators, and Anthropic Claude / OpenAI MCP Directory Reviewers.
"""

from __future__ import annotations

PUBLIC_PAGE_STYLE = """
  body { font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#070b14; color:#f8fafc; margin:0; padding:2.5rem 1.25rem; line-height:1.65; font-size:15.5px; }
  main { max-width:840px; margin:0 auto; background:#0f172a; border:1px solid #334155; border-radius:16px; padding:2.5rem; }
  h1 { font-size:1.95rem; font-weight:800; color:#ffffff; margin:0 0 0.5rem; letter-spacing:-0.02em; }
  h2 { font-size:1.15rem; font-weight:700; margin:1.85rem 0 0.55rem; color:#38bdf8; }
  p, li { color:#cbd5e1; max-width:72ch; }
  code { background:#020617; border:1px solid #334155; color:#38bdf8; padding:0.15rem 0.45rem; border-radius:6px; font-size:0.88rem; }
  table { width:100%; border-collapse:collapse; margin:1rem 0; font-size:0.92rem; }
  th, td { text-align:left; padding:0.65rem 0.75rem; border-bottom:1px solid #334155; vertical-align:top; color:#e2e8f0; }
  th { font-weight:700; color:#38bdf8; background:#020617; }
  a { color:#38bdf8; text-decoration:none; font-weight:600; }
  a:hover { text-decoration:underline; }
  .nav-links { display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.5rem; padding-bottom:1rem; border-bottom:1px solid #334155; font-size:0.9rem; }
"""

TOP_NAV = """
  <nav class="nav-links">
    <a href="/">← Return to DeckForge Presentation Studio</a>
    <a href="/about">About</a>
    <a href="/docs">Documentation</a>
    <a href="/privacy">Privacy Policy</a>
    <a href="/terms">Terms of Service</a>
  </nav>
"""


def render_docs_html() -> str:
    """Returns the Public User & IT Administrator Documentation page (/docs & /documentation)."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>User &amp; IT Admin Documentation — DeckForge: Executive Slide Decks</title>
  <style>{PUBLIC_PAGE_STYLE}</style>
</head>
<body>
  <main>
    {TOP_NAV}
    <h1>User &amp; IT Administrator Documentation</h1>
    <p><strong>Connector Name:</strong> DeckForge: Executive Slide Decks<br/>
    <strong>Remote MCP Server URL:</strong> <code>https://deckforge-mcp-production.up.railway.app/mcp</code><br/>
    <strong>Founder &amp; Creator:</strong> Kader Mula<br/>
    <strong>Support Contact:</strong> <a href="mailto:mulak1@gmail.com">mulak1@gmail.com</a></p>

    <h2>1. Overview for End Users &amp; Business Teams</h2>
    <p>DeckForge turns meeting notes, written memos, spreadsheet tables, and quarterly business metrics into structured, ready-to-present 6-slide presentations. Users can preview every slide in 16:9 across 4 architectural design styles and 8 slide layouts, refine individual slide headlines and speaker talking points in plain business English, and download a fully editable PowerPoint (<code>.pptx</code>) presentation.</p>

    <h2>2. Security &amp; IT Administrator Review Summary</h2>
    <ul>
      <li><strong>100% Read-Only &amp; Idempotent Tools:</strong> All four MCP tools exposed by DeckForge (<code>transform_memo_to_slide_spec</code>, <code>remix_or_update_slide</code>, <code>generate_editable_pptx</code>, and <code>generate_google_slides_batch_requests</code>) are strictly stateless, read-only (<code>readOnlyHint: true</code>), non-destructive (<code>destructiveHint: false</code>), and idempotent (<code>idempotentHint: true</code>). The service cannot mutate, modify, or delete any external systems or user records.</li>
      <li><strong>Zero Model Training &amp; Ephemeral Memory Processing:</strong> Submitted meeting notes, financial numbers, and generated PowerPoint (<code>.pptx</code>) files are processed strictly in ephemeral memory to fulfill the active request. No customer notes or presentations are stored in persistent databases or used to train AI models.</li>
      <li><strong>Transport &amp; Authentication Security:</strong> All traffic is encrypted over HTTPS (TLS 1.3). Works immediately with zero external setup required, and also provides OAuth 2.1 with S256 PKCE discovery at <code>/.well-known/oauth-authorization-server</code>.</li>
    </ul>

    <h2>3. Included MCP Tools &amp; Permission Scope</h2>
    <table>
      <thead>
        <tr><th>Tool Name</th><th>Permission Scope</th><th>Plain-English Description</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><code>transform_memo_to_slide_spec</code></td>
          <td>Read-Only · Idempotent</td>
          <td>Turns rough meeting notes, quarterly numbers, or a written memo into a structured 6-slide presentation plan with headline takeaways, 4-card key metric grids, comparison charts, summary tables, 90-day roadmaps, and speaker talking points.</td>
        </tr>
        <tr>
          <td><code>remix_or_update_slide</code></td>
          <td>Read-Only · Idempotent</td>
          <td>Changes any single slide to a new layout (such as Key Numbers Grid, Quarterly Chart, 3-Pillar Executive Summary, Financial Table, Customer Quote Spotlight, or 90-Day Roadmap) and sharpens its headline, takeaway banner, and speaker notes.</td>
        </tr>
        <tr>
          <td><code>generate_editable_pptx</code></td>
          <td>Read-Only · Idempotent</td>
          <td>Creates a ready-to-present, fully editable PowerPoint (<code>.pptx</code>) presentation file from the structured slide plan with native editable text boxes, metric cards, charts, tables, and speaker notes.</td>
        </tr>
        <tr>
          <td><code>generate_google_slides_batch_requests</code></td>
          <td>Read-Only · Idempotent</td>
          <td>Prepares the presentation for online slide tools and renders crisp 16:9 interactive SVG visual previews for every slide in the deck.</td>
        </tr>
      </tbody>
    </table>

    <h2>4. Copy-Paste Example Prompts (Works Immediately Without Setup)</h2>
    <ul>
      <li><strong>Build a 6-Slide Board Deck from Notes:</strong> <em>"Use DeckForge to turn our Q3 business update into a 6-slide Boardroom Navy presentation: Annual Recurring Revenue reached $18.4M (+142% YoY), Net Customer Retention hit 124% (+900 bps), Gross Margin expanded to 81.2%, and Customer Payback dropped to 9.5 mos. Quarterly revenue progressed from Q1 $11.2M to Q2 $14.5M, Q3 $18.4M, and Q4 plan $23.0M."</em></li>
      <li><strong>Update a Single Slide Layout &amp; Polish Wording:</strong> <em>"Use DeckForge remix_or_update_slide to change Slide 2 of our presentation to a bar_chart_slide layout and tighten the executive headline and speaker talking points."</em></li>
      <li><strong>Export an Editable PowerPoint (.pptx) File &amp; Visual Preview:</strong> <em>"Use DeckForge generate_editable_pptx and generate_google_slides_batch_requests to build the downloadable PowerPoint (.pptx) file and 16:9 visual slide previews for our Q3 presentation."</em></li>
    </ul>

    <h2>5. Policies, Repository &amp; Support</h2>
    <ul>
      <li><strong>About DeckForge:</strong> <a href="/about">https://deckforge-mcp-production.up.railway.app/about</a></li>
      <li><strong>Privacy Policy:</strong> <a href="/privacy">https://deckforge-mcp-production.up.railway.app/privacy</a></li>
      <li><strong>Terms of Service:</strong> <a href="/terms">https://deckforge-mcp-production.up.railway.app/terms</a></li>
      <li><strong>GitHub Repository:</strong> <a href="https://github.com/mulak1/deckforge-mcp">https://github.com/mulak1/deckforge-mcp</a></li>
      <li><strong>Support Email:</strong> <a href="mailto:mulak1@gmail.com">mulak1@gmail.com</a></li>
    </ul>
  </main>
</body>
</html>"""


def render_about_html() -> str:
    """Returns the Public About & Company Information page (/about)."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>About DeckForge — Executive Presentation &amp; Slide Deck Studio</title>
  <style>{PUBLIC_PAGE_STYLE}</style>
</head>
<body>
  <main>
    {TOP_NAV}
    <h1>About DeckForge</h1>
    <p><strong>DeckForge</strong> builds plain-English executive presentation and slide generation tools that work both as a standalone interactive web studio and natively inside AI assistants via the Model Context Protocol (MCP).</p>

    <h2>Our Mission</h2>
    <p>Business leaders, chiefs of staff, finance teams, and consultants spend hours formatting slides from meeting notes and spreadsheets. DeckForge turns rough notes and quarterly numbers into clear, structured 6-slide presentations with headline takeaways, 4-card key metric grids, configurable charts, financial tables, 90-day roadmaps, and editable PowerPoint (<code>.pptx</code>) exports in seconds.</p>

    <h2>Privacy &amp; Security by Design</h2>
    <ul>
      <li><strong>Zero Model Training:</strong> We never train AI models on your meeting notes, financial metrics, or presentations.</li>
      <li><strong>100% Read-Only &amp; Ephemeral Architecture:</strong> All MCP tools are stateless, read-only, and idempotent. Notes and generated slide files are processed strictly in ephemeral memory.</li>
    </ul>

    <h2>Company &amp; Leadership</h2>
    <ul>
      <li><strong>Company:</strong> DeckForge</li>
      <li><strong>Founder &amp; Creator:</strong> Kader Mula</li>
      <li><strong>Website:</strong> <a href="https://deckforge-mcp-production.up.railway.app">https://deckforge-mcp-production.up.railway.app</a></li>
      <li><strong>Documentation:</strong> <a href="/docs">https://deckforge-mcp-production.up.railway.app/docs</a></li>
      <li><strong>GitHub:</strong> <a href="https://github.com/mulak1/deckforge-mcp">https://github.com/mulak1/deckforge-mcp</a></li>
      <li><strong>Contact &amp; Support:</strong> <a href="mailto:mulak1@gmail.com">mulak1@gmail.com</a></li>
    </ul>
  </main>
</body>
</html>"""


def render_privacy_html() -> str:
    """Returns the plain-English Privacy & Confidentiality Policy page (/privacy)."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Privacy &amp; Confidentiality Policy — DeckForge</title>
  <style>{PUBLIC_PAGE_STYLE}</style>
</head>
<body>
  <main>
    {TOP_NAV}
    <h1>Privacy &amp; Confidentiality Policy</h1>
    <p><strong>Effective Date:</strong> November 2, 2026. Your business notes, numbers, and presentations belong strictly to you.</p>
    <h2>1. Ephemeral In-Memory Slide Processing</h2>
    <p>Meeting notes, business memos, spreadsheet rows, and numbers submitted to DeckForge are processed strictly in memory to generate your slide deck, chart preview, or PowerPoint (<code>.pptx</code>) file. We do not store your presentation contents in persistent databases after your request completes.</p>
    <h2>2. Zero AI Model Training</h2>
    <p>Your business documents, financial metrics, and slide decks are never used to train, fine-tune, or improve any artificial intelligence model.</p>
    <h2>3. Transport &amp; Sign-In Security</h2>
    <p>All connections are encrypted in transit over HTTPS (TLS 1.3). For questions regarding privacy, security, or IT administrator reviews, contact <strong>Kader Mula</strong> at <a href="mailto:mulak1@gmail.com">mulak1@gmail.com</a>.</p>
  </main>
</body>
</html>"""


def render_terms_html() -> str:
    """Returns the plain-English Terms of Service page (/terms)."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Terms of Service — DeckForge</title>
  <style>{PUBLIC_PAGE_STYLE}</style>
</head>
<body>
  <main>
    {TOP_NAV}
    <h1>Terms of Service</h1>
    <p><strong>Effective Date:</strong> November 2, 2026</p>
    <h2>1. Service Overview</h2>
    <p>DeckForge turns meeting notes, memos, and spreadsheet tables into editable PowerPoint (<code>.pptx</code>) presentations, visual slide previews, and 1-page meeting read-ahead briefs.</p>
    <h2>2. Plans &amp; Usage</h2>
    <p>All 8 business templates, 8 slide layouts, 4 architectural design styles, and 4 chart types are available immediately. Customer notes and generated slide decks remain 100% the property of the user.</p>
    <h2>3. Contact &amp; Support</h2>
    <p>Questions regarding these terms may be directed to <strong>Kader Mula</strong> at <a href="mailto:mulak1@gmail.com">mulak1@gmail.com</a>.</p>
  </main>
</body>
</html>"""
