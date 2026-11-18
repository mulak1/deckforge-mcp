"""
Public HTML Pages for DeckForge MCP (/docs, /documentation, /about, /privacy, /terms).
Designed for End Users, IT Administrators, and Anthropic Claude / OpenAI MCP Directory Reviewers.
"""

from __future__ import annotations

DECKFORGE_FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
    '<rect width="48" height="48" rx="12" fill="#0F172A" stroke="#0284C7" stroke-width="2"/>'
    '<rect x="8.5" y="12.5" width="23" height="16.5" rx="3" fill="#4F46E5"/>'
    '<rect x="13" y="17.5" width="25.5" height="17.5" rx="3.5" fill="#0284C7" stroke="#E0F2FE" stroke-width="1.2"/>'
    '<rect x="17.5" y="27.5" width="4" height="4.5" rx="0.8" fill="#0F172A"/>'
    '<rect x="23.5" y="24" width="4" height="8" rx="0.8" fill="#0F172A"/>'
    '<rect x="29.5" y="20.5" width="4" height="11.5" rx="0.8" fill="#FFFFFF"/>'
    '<path d="M36.5 7.5L38 12L42.5 13.5L38 15L36.5 19.5L35 15L30.5 13.5L35 12Z" fill="#F59E0B"/>'
    "</svg>"
)

PUBLIC_PAGE_STYLE = """
  body { font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#070b14; color:#f8fafc; margin:0; padding:2.5rem 1.25rem; line-height:1.65; font-size:15.5px; }
  main { max-width:860px; margin:0 auto; background:#0f172a; border:1px solid #334155; border-radius:16px; padding:2.5rem; }
  h1 { font-size:1.95rem; font-weight:800; color:#ffffff; margin:0 0 0.5rem; letter-spacing:-0.02em; }
  h2 { font-size:1.15rem; font-weight:700; margin:1.85rem 0 0.55rem; color:#38bdf8; }
  p, li { color:#cbd5e1; max-width:72ch; }
  code { background:#020617; border:1px solid #334155; color:#38bdf8; padding:0.15rem 0.45rem; border-radius:6px; font-size:0.88rem; }
  .table-wrapper { overflow:auto; max-inline-size:100%; container-type:inline-size; margin:1rem 0; border:1px solid #334155; border-radius:10px; }
  table { width:100%; border-collapse:separate; border-spacing:0; font-size:0.92rem; }
  caption { text-align:left; font-weight:700; padding:0.65rem 0.75rem; background:#020617; color:#38bdf8; border-bottom:1px solid #334155; }
  thead { position:sticky; inset-block-start:0; z-index:1; }
  th, td { text-align:left; padding:0.65rem 0.75rem; border-bottom:1px solid #334155; vertical-align:top; color:#e2e8f0; }
  th { font-weight:700; color:#38bdf8; background:#020617; }
  tbody th { position:sticky; inset-inline-start:0; background:#0f172a; color:#f8fafc; }
  a { color:#38bdf8; text-decoration:none; font-weight:600; }
  a:hover { text-decoration:underline; }
  a:focus-visible, .table-wrapper:focus-visible { outline:3px solid #38bdf8; outline-offset:3px; }
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
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="icon" type="image/png" href="/icon.png" />
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
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="icon" type="image/png" href="/icon.png" />
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
    """Returns the complete Privacy & Confidentiality Policy page (/privacy) covering data collected, tool inputs/outputs, purposes, recipients, retention, and user controls."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="icon" type="image/png" href="/icon.png" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Privacy &amp; Confidentiality Policy — DeckForge</title>
  <style>{PUBLIC_PAGE_STYLE}</style>
</head>
<body>
  <main>
    {TOP_NAV}
    <h1>Privacy &amp; Confidentiality Policy</h1>
    <p><strong>Effective Date:</strong> November 17, 2026 · <strong>Controller:</strong> Kader Mula (DeckForge) · <strong>Contact:</strong> <a href="mailto:mulak1@gmail.com">mulak1@gmail.com</a></p>
    <p>Your business notes, financial metrics, and presentations belong strictly to you. This Privacy Policy discloses all data collected by DeckForge across our Web Presentation Studio and our Claude / ChatGPT Model Context Protocol (MCP) connectors, the exact inputs and outputs of each tool, purposes of processing, recipients, retention windows, and your user controls.</p>

    <h2>1. Data Collected &amp; Current MCP Tool Inputs and Outputs</h2>
    <p>DeckForge collects only the user-supplied inputs required to execute the specific presentation tool you invoke, plus minimal technical request headers for rate-limiting and quota accounting:</p>
    <div tabindex="0" role="region" aria-labelledby="df-privacy-tools-caption" class="table-wrapper">
      <table>
        <caption id="df-privacy-tools-caption">DeckForge MCP Tool Inputs, Outputs, and Data Handling</caption>
        <thead>
          <tr><th scope="col">Tool Name</th><th scope="col">Tool Inputs Collected</th><th scope="col">Tool Outputs Returned</th><th scope="col">Retention &amp; Storage</th></tr>
        </thead>
        <tbody>
          <tr><th scope="row"><code>transform_memo_to_slide_spec</code></th><td><code>raw_memo</code> (meeting notes, business memo, or metrics text), optional <code>deck_title</code>, <code>organization</code>, <code>theme_preset</code>, <code>target_slide_count</code> (3–12), <code>audience</code> (<code>board</code>, <code>leadership</code>, <code>client</code>, <code>team</code>), and <code>footer_label</code>.</td><td>Structured 6-slide <code>deck_spec</code> JSON object (slide headlines, 4-card KPI metrics grid, chart series, financial table rows, 90-day roadmap, and speaker talking points) and 16:9 SVG slide previews.</td><td>100% stateless in-memory execution; zero database persistence after the HTTP response completes.</td></tr>
          <tr><th scope="row"><code>remix_or_update_slide</code></th><td><code>deck_spec</code> (existing slide deck object), <code>slide_number</code> (1–50), <code>new_layout_type</code>, optional <code>chart_type</code>, <code>polish_mode</code>, <code>action_title</code>, and <code>takeaway_banner</code>.</td><td>Updated <code>deck_spec</code> JSON object with the remixed slide layout, sharpened headline and speaker talking points, and updated 16:9 SVG preview.</td><td>100% stateless in-memory execution; zero database persistence after the HTTP response completes.</td></tr>
          <tr><th scope="row"><code>generate_editable_pptx</code></th><td><code>deck_spec</code> (structured slide deck specification with title, theme, and slides) and optional <code>api_key</code> for Pro tier quota verification.</td><td>Editable OpenXML PowerPoint (<code>.pptx</code>) presentation file (base64 payload, byte size, slide count, and temporary <code>/downloads/&lt;filename&gt;.pptx</code> URL) plus current quota status.</td><td>Input processed in RAM; generated <code>.pptx</code> binary held in a bounded in-memory LRU cache (max 40 files) solely for immediate download and cleared automatically.</td></tr>
          <tr><th scope="row"><code>generate_google_slides_batch_requests</code></th><td><code>deck_spec</code> (structured slide deck specification) and optional <code>presentation_id</code> label.</td><td>Google Slides API <code>batchUpdate</code> layout operations array and 16:9 interactive SVG slide previews for every slide in the deck.</td><td>100% stateless in-memory execution; zero external API writes and zero database persistence.</td></tr>
        </tbody>
      </table>
    </div>
    <p><strong>Technical &amp; Quota Metadata:</strong> Standard HTTP request headers (caller IP address or <code>X-Client-Id</code>, user-agent string, and optional Pro <code>api_key</code>) are processed in memory to meter the Free Tier (3 PowerPoint exports/month) versus Pro Tier and prevent automated abuse.</p>

    <h2>2. Purposes of Data Processing</h2>
    <ul>
      <li><strong>Slide Planning &amp; Formatting:</strong> Parsing submitted meeting notes and numbers into structured 6-slide outlines, 16:9 SVG previews, and OpenXML PowerPoint (<code>.pptx</code>) files.</li>
      <li><strong>Quota Enforcement &amp; Billing Verification:</strong> Tracking monthly free-tier deck export counts and verifying Pro API keys or OAuth 2.1 tokens.</li>
      <li><strong>Service Security &amp; Reliability:</strong> Enforcing payload size caps (5 MB maximum), preventing denial-of-service abuse, and maintaining service health.</li>
    </ul>

    <h2>3. Zero AI Model Training</h2>
    <p>Your meeting notes, business memos, financial metrics, tool inputs, and generated slide decks are <strong>never</strong> used to train, fine-tune, or improve any artificial intelligence or foundation model (<code>trains_on_customer_data: false</code>).</p>

    <h2>4. Recipients &amp; Third-Party Subprocessors</h2>
    <p>We never sell, rent, or share your presentation content or tool inputs/outputs with advertisers, data brokers, or external AI providers. Infrastructure subprocessors are strictly limited to:</p>
    <ul>
      <li><strong>Railway Corp. (United States):</strong> Encrypted cloud container infrastructure hosting the stateless DeckForge FastAPI MCP server.</li>
      <li><strong>Stripe, Inc. (United States):</strong> Payment processing only when a user voluntarily upgrades to a paid DeckForge Pro plan via Stripe Checkout. DeckForge never collects or stores raw payment card numbers.</li>
    </ul>

    <h2>5. Data Retention &amp; Ephemeral Memory Policy</h2>
    <ul>
      <li><strong>Tool Inputs &amp; JSON Outputs:</strong> Processed strictly in volatile RAM during the active HTTP request and discarded immediately upon response delivery.</li>
      <li><strong>Temporary <code>.pptx</code> Download Cache:</strong> Generated PowerPoint (<code>.pptx</code>) files are held in an ephemeral in-memory dictionary (capped at 40 files) so you can click the direct download link in ChatGPT, Claude, or the Web Studio, and are automatically evicted as new files are created or upon container restart.</li>
      <li><strong>Aggregate Telemetry:</strong> Non-content operational counters (such as tool invocation counts by tool name) contain zero user text, zero financial figures, and zero personally identifiable information.</li>
    </ul>

    <h2>6. User Controls, Deletion &amp; Privacy Rights (GDPR / CCPA)</h2>
    <ul>
      <li><strong>Input Controls:</strong> You control all text and numbers sent to DeckForge tools and may omit or anonymize sensitive names or figures at any time.</li>
      <li><strong>Browser Storage Controls:</strong> Web Studio users can reset their workspace or clear saved Pro plan keys at any time via the Studio controls or by clearing browser <code>localStorage</code>.</li>
      <li><strong>Access, Deletion &amp; Opt-Out Requests:</strong> To request immediate purge of any cached <code>.pptx</code> download artifact, deletion of Stripe billing records, or to exercise GDPR/CCPA access, erasure, or portability rights, contact <strong>Kader Mula</strong> at <a href="mailto:mulak1@gmail.com">mulak1@gmail.com</a>. All requests are honored within 24 hours.</li>
    </ul>

    <h2>7. Transport &amp; Authentication Security</h2>
    <p>All connections are encrypted in transit over HTTPS (TLS 1.3) with strict HSTS, Content-Security-Policy, and OAuth 2.1 with S256 PKCE support.</p>
  </main>
</body>
</html>"""


def render_terms_html() -> str:
    """Returns the plain-English Terms of Service page (/terms)."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="icon" type="image/png" href="/icon.png" />
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
