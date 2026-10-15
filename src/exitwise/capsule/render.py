"""Renderers for capsule.md, self-contained capsule.html (Editorial Dark), and index.html."""

import html
import json
from pathlib import Path
from exitwise.models import DependencyCapsule, Provenance, TrustSummary


def provenance_badge_html(prov: Provenance | str) -> str:
    """Generate accessible provenance badge with distinct icon, label, and style."""
    val = prov.value if isinstance(prov, Provenance) else str(prov)
    if val == "OBSERVED":
        icon = "◉"
        cls = "prov-observed"
        label = "OBSERVED"
    elif val == "VERIFIED_BY_EXECUTION":
        icon = "✓"
        cls = "prov-verified"
        label = "VERIFIED BY EXECUTION"
    elif val == "AI_GENERATED":
        icon = "✦"
        cls = "prov-ai"
        label = "AI PROPOSED"
    elif val == "AI_VERIFIED":
        icon = "★"
        cls = "prov-ai-verified"
        label = "AI VERIFIED"
    else:
        icon = "⚠"
        cls = "prov-not-verified"
        label = "NOT VERIFIED"

    return f'<span class="prov-badge {cls}" title="{label}"><span class="prov-icon" aria-hidden="true">{icon}</span> {label}</span>'


def render_capsule_markdown(capsule: DependencyCapsule) -> str:
    """Render human-readable Markdown capsule."""
    meta = capsule.meta
    dep = capsule.dependency
    ts = capsule.provenance_summary

    lines = [
        f"# Dependency Exit Capsule: `{dep.name}`",
        "",
        f"> **Verdict:** `{capsule.overall_verdict}` | **Tool:** {meta.tool_name} v{meta.tool_version} | **Generated:** {meta.generated_at}",
        f"> **Gemma Model:** `{meta.gemma_model_id}` ({meta.access_method})",
        "",
        "## Trust Summary",
        "",
        f"- **Total Claims / Findings:** {ts.total_claims}",
        f"- **Observed (deterministic / static / registry):** {ts.observed_count} (`OBSERVED`)",
        f"- **Verified by Sandbox Execution:** {ts.verified_by_execution_count} (`VERIFIED_BY_EXECUTION`)",
        f"- **AI Proposed by Gemma (unverified):** {ts.ai_generated_count} (`AI_GENERATED`)",
        f"- **AI Proposed & Confirmed by Test Run:** {ts.ai_verified_count} (`AI_VERIFIED`)",
        f"- **Unverified / Skipped:** {ts.not_verified_count} (`NOT_VERIFIED`)",
        "",
        "## 1. Dependency Details",
        "",
        f"- **Package:** `{dep.name}`",
        f"- **Pinned Version:** `{dep.pinned_version or 'unpinned'}`",
        f"- **Raw Specifier:** `{dep.raw_spec}`",
        f"- **Source Manifests:** {', '.join(dep.source_manifests) or 'None'}",
        f"- **Latest PyPI Version:** `{dep.latest_version or 'unknown'}`",
        "",
        "## 2. Risk Indicators",
        "",
        "| ID | Severity | Indicator | Evidence | Provenance |",
        "|---|---|---|---|---|",
    ]

    for ind in capsule.risk_indicators:
        ev_str = ", ".join(ind.evidence_ids) if ind.evidence_ids else "-"
        lines.append(f"| `{ind.id}` | **{ind.severity}** | {ind.observed_value} | {ev_str} | `{ind.provenance.value}` |")

    lines.extend([
        "",
        "## 3. Usage & Coupling",
        "",
        f"- **Files touched:** {capsule.usage_summary.total_files}",
        f"- **Occurrences:** {capsule.usage_summary.total_occurrences}",
        f"- **Dynamic patching:** {'YES (Hazard)' if capsule.usage_summary.is_monkey_patched else 'No'}",
        f"- **Coupling Score:** {capsule.usage_summary.coupling_score}/10",
        "",
        "### Usage Locations",
        "",
        "| File | Line | Symbol | Kind | Context | Provenance |",
        "|---|---|---|---|---|---|",
    ])

    for loc in capsule.usage_locations:
        lines.append(f"| `{loc.file}` | {loc.line} | `{loc.symbol}` | {loc.kind} | {loc.context} | `{loc.provenance.value}` |")

    lines.extend([
        "",
        "## 4. Proposed Replacement & Migration",
        "",
    ])

    if capsule.proposed_replacement:
        cand = capsule.proposed_replacement
        lines.extend([
            f"- **Candidate:** `{cand.name}` ({'Python Standard Library' if cand.kind == 'stdlib' else 'PyPI'})",
            f"- **Validation Status:** `{cand.status}` ({cand.validation.validation_log})",
            f"- **Trade-offs:** {'; '.join(cand.tradeoffs) or 'None listed'}",
            f"- **Provenance:** `{cand.provenance.value}`",
        ])
    else:
        lines.append("No automated replacement proposed (Keep & Monitor).")

    if capsule.migration_steps:
        lines.extend(["", "### Migration Steps", ""])
        for step in capsule.migration_steps:
            lines.append(f"{step.order}. [{step.provenance.value}] {step.description}")

    if capsule.patch and capsule.patch.unified_diff:
        lines.extend([
            "",
            "### Migration Diff",
            f"> Applied cleanly: `{capsule.patch.applied_cleanly}`",
            "",
            "```diff",
            capsule.patch.unified_diff.strip(),
            "```",
        ])

    lines.extend([
        "",
        "## 5. Executed Test Results",
        "",
        "| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |",
        "|---|---|---|---|---|---|---|",
    ])

    for tr in capsule.executed_test_results:
        lines.append(
            f"| `{tr.side}` | {tr.python_version} | {tr.exit_code} | {tr.passed} | {tr.failed} | {tr.duration_seconds}s | `{tr.provenance.value}` |"
        )

    lines.extend([
        "",
        "## 6. Compatibility Gaps & Concerns",
        "",
    ])

    if capsule.compatibility_gaps:
        for g in capsule.compatibility_gaps:
            lines.append(f"- **[{g.severity}] {g.id}:** {g.description} (`{g.provenance.value}`)")
            lines.append(f"  *Suggested Resolution:* {g.suggested_resolution}")
    else:
        lines.append("No compatibility gaps surfaced during execution.")

    return "\n".join(lines)


def render_capsule_html(capsule: DependencyCapsule) -> str:
    """Render self-contained HTML capsule with Editorial Dark design system and zero external assets."""
    meta = capsule.meta
    dep = capsule.dependency
    ts = capsule.provenance_summary
    verdict_cls = {
        "READY": "verdict-ready",
        "READY WITH GAPS": "verdict-warning",
        "BLOCKED": "verdict-blocked",
        "NOT EXECUTED": "verdict-neutral",
    }.get(capsule.overall_verdict, "verdict-neutral")

    # Render risk table rows
    risk_rows = ""
    for r in capsule.risk_indicators:
        risk_rows += f"""
        <tr>
          <td><code>{html.escape(r.id)}</code></td>
          <td><span class="severity-pill sev-{r.severity.lower()}">{r.severity}</span></td>
          <td>{html.escape(r.observed_value)}</td>
          <td><code>{html.escape(", ".join(r.evidence_ids) or "-")}</code></td>
          <td>{provenance_badge_html(r.provenance)}</td>
        </tr>
        """

    # Render usage table rows
    usage_rows = ""
    for u in capsule.usage_locations:
        usage_rows += f"""
        <tr>
          <td><code>{html.escape(u.file)}</code></td>
          <td>{u.line}</td>
          <td><code>{html.escape(u.symbol)}</code></td>
          <td><span class="badge-subtle">{html.escape(u.kind)}</span></td>
          <td><span class="badge-subtle">{html.escape(u.context)}</span></td>
          <td>{provenance_badge_html(u.provenance)}</td>
        </tr>
        """

    # Render test rows
    test_rows = ""
    for t in capsule.executed_test_results:
        test_rows += f"""
        <tr>
          <td><strong>{html.escape(t.side.upper())}</strong></td>
          <td><code>Python {html.escape(t.python_version)}</code></td>
          <td><span class="status-code {'code-ok' if t.exit_code == 0 else 'code-fail'}">{t.exit_code}</span></td>
          <td>{t.passed} passed</td>
          <td>{t.failed} failed</td>
          <td>{t.duration_seconds}s</td>
          <td>{provenance_badge_html(t.provenance)}</td>
        </tr>
        """

    # Render diff block
    diff_html = ""
    if capsule.patch and capsule.patch.unified_diff:
        diff_html = f"""
        <div class="diff-container">
          <div class="diff-header">
            <span>UNIFIED DIFF</span>
            <span>Applied cleanly: <strong>{capsule.patch.applied_cleanly}</strong></span>
          </div>
          <pre class="diff-body"><code>{html.escape(capsule.patch.unified_diff)}</code></pre>
        </div>
        """

    # Render gaps
    gaps_html = ""
    if capsule.compatibility_gaps:
        for g in capsule.compatibility_gaps:
            gaps_html += f"""
            <div class="gap-card">
              <div class="gap-title">
                <span class="severity-pill sev-{g.severity.lower()}">{g.severity}</span>
                <strong>{html.escape(g.id)}:</strong> {html.escape(g.description)}
                {provenance_badge_html(g.provenance)}
              </div>
              <p class="gap-resolution"><strong>Resolution:</strong> {html.escape(g.suggested_resolution)}</p>
            </div>
            """
    else:
        gaps_html = '<p class="text-secondary">No compatibility gaps identified.</p>'

    template = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Exitwise Capsule — {html.escape(dep.name)}</title>
  <style>
    :root {{
      --bg: #09090b;
      --bg-raised: #0f0f12;
      --bg-sunken: #060607;
      --bg-hover: #16161a;
      --text: #fafafa;
      --text-2: #d4d4d8;
      --text-3: #a1a1aa;
      --text-4: #71717a;
      --line: rgba(255, 255, 255, 0.08);
      --line-strong: rgba(255, 255, 255, 0.16);
      --accent: #5b8cff;
      --accent-2: #22d3ee;
      --success: #34d399;
      --warning: #fbbf24;
      --danger: #f87171;
      --radius-sm: 6px;
      --radius-md: 12px;
      --radius-lg: 20px;
      --radius-pill: 9999px;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text-2);
      font-family: var(--font-sans);
      font-size: 15px;
      line-height: 1.6;
      padding: 40px 20px;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    header {{
      margin-bottom: 48px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 32px;
    }}
    .mono-eyebrow {{
      font-family: var(--font-mono);
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--text-4);
      margin-bottom: 8px;
    }}
    h1.editorial-h1 {{
      font-size: clamp(32px, 5vw, 56px);
      font-weight: 600;
      letter-spacing: -0.04em;
      line-height: 1.05;
      color: var(--text);
      margin-bottom: 16px;
    }}
    h1.editorial-h1 em {{
      font-family: "Georgia", "Times New Roman", serif;
      font-style: italic;
      font-weight: 400;
      color: var(--accent);
    }}
    .lead {{
      font-size: 18px;
      color: var(--text-3);
      max-width: 800px;
    }}
    /* Trust Summary HUD */
    .trust-hud {{
      background: var(--bg-raised);
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      padding: 24px;
      margin-bottom: 48px;
    }}
    .hud-title {{
      font-family: var(--font-mono);
      font-size: 12px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--accent-2);
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .hud-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }}
    .hud-card {{
      background: var(--bg-sunken);
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      padding: 16px;
    }}
    .hud-num {{
      font-size: 32px;
      font-weight: 600;
      color: var(--text);
      line-height: 1;
      margin-bottom: 4px;
    }}
    .hud-label {{
      font-size: 13px;
      color: var(--text-3);
    }}
    .prov-legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      border-top: 1px solid var(--line);
      padding-top: 16px;
      font-size: 13px;
    }}
    /* Provenance badges */
    .prov-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.04em;
      white-space: nowrap;
    }}
    .prov-observed {{ background: rgba(34, 211, 238, 0.12); color: #22d3ee; border: 1px solid rgba(34, 211, 238, 0.3); }}
    .prov-verified {{ background: rgba(52, 211, 153, 0.12); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }}
    .prov-ai {{ background: rgba(167, 139, 250, 0.12); color: #a78bfa; border: 1px solid rgba(167, 139, 250, 0.3); }}
    .prov-ai-verified {{ background: rgba(251, 191, 36, 0.12); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }}
    .prov-not-verified {{ background: rgba(248, 113, 113, 0.12); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); }}

    /* Chapter Anatomy */
    .chapter {{
      margin-bottom: 64px;
    }}
    .chapter-label {{
      font-family: var(--font-mono);
      font-size: 12px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--text-4);
      margin-bottom: 8px;
    }}
    .chapter-h2 {{
      font-size: 24px;
      font-weight: 600;
      color: var(--text);
      letter-spacing: -0.02em;
      margin-bottom: 24px;
    }}
    .chapter-h2 em {{
      font-family: "Georgia", "Times New Roman", serif;
      font-style: italic;
      color: var(--text);
    }}

    /* Data Tables */
    table.editorial-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      background: var(--bg-raised);
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      overflow: hidden;
      margin-bottom: 24px;
    }}
    table.editorial-table th {{
      text-align: left;
      padding: 12px 16px;
      background: var(--bg-sunken);
      color: var(--text-4);
      font-family: var(--font-mono);
      font-size: 11px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      border-bottom: 1px solid var(--line);
    }}
    table.editorial-table td {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      color: var(--text-2);
      vertical-align: top;
    }}
    table.editorial-table tr:last-child td {{
      border-bottom: none;
    }}
    code {{
      font-family: var(--font-mono);
      font-size: 12px;
      background: rgba(255, 255, 255, 0.06);
      padding: 2px 6px;
      border-radius: 4px;
      color: var(--text);
    }}

    /* Severity Pills */
    .severity-pill {{
      display: inline-block;
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 4px;
      text-transform: uppercase;
    }}
    .sev-critical {{ background: rgba(248, 113, 113, 0.2); color: #f87171; }}
    .sev-high {{ background: rgba(251, 146, 60, 0.2); color: #fb923c; }}
    .sev-medium {{ background: rgba(251, 191, 36, 0.2); color: #fbbf24; }}
    .sev-low {{ background: rgba(52, 211, 153, 0.2); color: #34d399; }}

    .verdict-badge {{
      display: inline-block;
      padding: 6px 14px;
      border-radius: var(--radius-pill);
      font-weight: 600;
      font-size: 13px;
      text-transform: uppercase;
    }}
    .verdict-ready {{ background: rgba(52, 211, 153, 0.2); color: #34d399; border: 1px solid #34d399; }}
    .verdict-warning {{ background: rgba(251, 191, 36, 0.2); color: #fbbf24; border: 1px solid #fbbf24; }}
    .verdict-blocked {{ background: rgba(248, 113, 113, 0.2); color: #f87171; border: 1px solid #f87171; }}
    .verdict-neutral {{ background: rgba(161, 161, 170, 0.2); color: #a1a1aa; border: 1px solid #a1a1aa; }}

    /* Diff View */
    .diff-container {{
      background: var(--bg-sunken);
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      overflow: hidden;
      margin: 20px 0;
    }}
    .diff-header {{
      background: var(--bg-raised);
      padding: 10px 16px;
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-3);
      display: flex;
      justify-content: space-between;
      border-bottom: 1px solid var(--line);
    }}
    .diff-body {{
      padding: 16px;
      font-family: var(--font-mono);
      font-size: 13px;
      line-height: 1.5;
      overflow-x: auto;
      color: var(--text-2);
    }}

    /* Gap Card */
    .gap-card {{
      background: var(--bg-raised);
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      padding: 16px;
      margin-bottom: 12px;
    }}
    .gap-title {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }}
    .gap-resolution {{
      color: var(--text-3);
      font-size: 14px;
    }}
    footer {{
      border-top: 1px solid var(--line);
      padding-top: 32px;
      margin-top: 64px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--text-4);
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="mono-eyebrow">DEPENDENCY EXIT CAPSULE · TRACK 1 GEMMA 4</div>
      <h1 class="editorial-h1">Exitwise: {html.escape(dep.name)}.</h1>
      <p class="lead">Gemma proposes; the machine verifies; the capsule records which is which.</p>
      <div style="margin-top: 20px; display: flex; gap: 16px; align-items: center;">
        <span class="verdict-badge {verdict_cls}">VERDICT: {html.escape(capsule.overall_verdict)}</span>
        <span style="color: var(--text-3); font-size: 14px;">Target: <code>{html.escape(meta.target_repo_url)}</code> ({html.escape(meta.target_commit_sha[:8])})</span>
      </div>
    </header>

    <!-- Trust Summary HUD -->
    <div class="trust-hud">
      <div class="hud-title">● TRUST SUMMARY & PROVENANCE BREAKDOWN</div>
      <div class="hud-grid">
        <div class="hud-card">
          <div class="hud-num" style="color: #22d3ee;">{ts.observed_count}</div>
          <div class="hud-label">Observed Directly (Code / Registry)</div>
        </div>
        <div class="hud-card">
          <div class="hud-num" style="color: #34d399;">{ts.verified_by_execution_count}</div>
          <div class="hud-label">Verified By Execution (Sandbox Tests)</div>
        </div>
        <div class="hud-card">
          <div class="hud-num" style="color: #a78bfa;">{ts.ai_generated_count}</div>
          <div class="hud-label">AI Proposed by Gemma (Unverified)</div>
        </div>
        <div class="hud-card">
          <div class="hud-num" style="color: #fbbf24;">{ts.ai_verified_count}</div>
          <div class="hud-label">AI Proposed & Verified by Run</div>
        </div>
      </div>
      <div class="prov-legend">
        <span><strong>Legend:</strong></span>
        {provenance_badge_html(Provenance.OBSERVED)}
        {provenance_badge_html(Provenance.VERIFIED_BY_EXECUTION)}
        {provenance_badge_html(Provenance.AI_GENERATED)}
        {provenance_badge_html(Provenance.AI_VERIFIED)}
        {provenance_badge_html(Provenance.NOT_VERIFIED)}
      </div>
    </div>

    <!-- Chapter 01: Risk Indicators -->
    <section class="chapter">
      <div class="chapter-label">01 / SURFACED RISKS</div>
      <h2 class="chapter-h2">Identified <em>Vulnerabilities</em> & Drift.</h2>
      <table class="editorial-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Severity</th>
            <th>Observed Finding</th>
            <th>Evidence IDs</th>
            <th>Provenance</th>
          </tr>
        </thead>
        <tbody>
          {risk_rows}
        </tbody>
      </table>
    </section>

    <!-- Chapter 02: Code Usage -->
    <section class="chapter">
      <div class="chapter-label">02 / USAGE ANALYSIS</div>
      <h2 class="chapter-h2">Where and <em>how</em> it is coupled.</h2>
      <div style="margin-bottom: 16px; color: var(--text-3);">
        Coupling Score: <strong>{capsule.usage_summary.coupling_score} / 10</strong> |
        Files: <strong>{capsule.usage_summary.total_files}</strong> |
        Dynamic Patching: <strong>{'YES (High Risk Hazard)' if capsule.usage_summary.is_monkey_patched else 'None'}</strong>
      </div>
      <table class="editorial-table">
        <thead>
          <tr>
            <th>File</th>
            <th>Line</th>
            <th>Symbol</th>
            <th>Kind</th>
            <th>Context</th>
            <th>Provenance</th>
          </tr>
        </thead>
        <tbody>
          {usage_rows}
        </tbody>
      </table>
    </section>

    <!-- Chapter 03: Proposed Replacement -->
    <section class="chapter">
      <div class="chapter-label">03 / PROPOSAL & DIFF</div>
      <h2 class="chapter-h2">Candidate <em>Migration</em> Path.</h2>
      {f'''
      <div class="gap-card" style="margin-bottom: 24px;">
        <p><strong>Candidate:</strong> <code>{html.escape(capsule.proposed_replacement.name)}</code> ({html.escape(capsule.proposed_replacement.kind)}) {provenance_badge_html(capsule.proposed_replacement.provenance)}</p>
        <p><strong>Validation:</strong> {html.escape(capsule.proposed_replacement.validation.validation_log)}</p>
      </div>
      ''' if capsule.proposed_replacement else '<p>Keep and monitor.</p>'}
      {diff_html}
    </section>

    <!-- Chapter 04: Execution Results -->
    <section class="chapter">
      <div class="chapter-label">04 / EXECUTION EVIDENCE</div>
      <h2 class="chapter-h2">Baseline vs Candidate <em>Verification</em>.</h2>
      <table class="editorial-table">
        <thead>
          <tr>
            <th>Side</th>
            <th>Interpreter</th>
            <th>Exit Code</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Duration</th>
            <th>Provenance</th>
          </tr>
        </thead>
        <tbody>
          {test_rows}
        </tbody>
      </table>
    </section>

    <!-- Chapter 05: Gaps -->
    <section class="chapter">
      <div class="chapter-label">05 / COMPATIBILITY GAPS</div>
      <h2 class="chapter-h2">Surfaced <em>Gaps</em> & Concerns.</h2>
      {gaps_html}
    </section>

    <footer>
      <div>Generated by <strong>Exitwise</strong> v{html.escape(meta.tool_version)}</div>
      <div>Gemma Model: <code>{html.escape(meta.gemma_model_id)}</code></div>
      <div>Terms: Apache-2.0</div>
    </footer>
  </div>
</body>
</html>
"""
    return template


def render_index_html(capsules: list[DependencyCapsule], repo_url: str) -> str:
    """Render top-level index.html listing all evaluated dependencies and risk rankings with repository analysis widget."""
    rows = ""
    for c in capsules:
        dep = c.dependency
        ts = c.provenance_summary
        cand_name = c.proposed_replacement.name if c.proposed_replacement else "None (Monitor)"
        verdict_cls = {
            "READY": "verdict-ready",
            "READY WITH GAPS": "verdict-warning",
            "BLOCKED": "verdict-blocked",
            "NOT EXECUTED": "verdict-neutral",
        }.get(c.overall_verdict, "verdict-neutral")

        rows += f"""
        <tr>
          <td><strong><a href="javascript:void(0)" onclick="openCapsuleModal('{html.escape(dep.name)}')" style="color: var(--accent); text-decoration: none;">{html.escape(dep.name)}</a></strong></td>
          <td><code>{html.escape(dep.pinned_version or 'unpinned')}</code></td>
          <td><code>{html.escape(dep.latest_version or 'unknown')}</code></td>
          <td>{c.usage_summary.coupling_score}/10</td>
          <td><code>{html.escape(cand_name)}</code></td>
          <td><span class="verdict-badge {verdict_cls}">{html.escape(c.overall_verdict)}</span></td>
          <td>
            <span style="font-size: 11px; font-family: var(--font-mono); color: var(--text-3);">
              {ts.observed_count} obs · {ts.verified_by_execution_count} ver · {ts.ai_generated_count} ai
            </span>
          </td>
          <td><button class="action-btn" onclick="openCapsuleModal('{html.escape(dep.name)}')">View Capsule →</button></td>
        </tr>
        """

    # If exitwise-output/index.html exists, return its content or updated template
    index_file = Path("exitwise-output") / "index.html"
    if index_file.is_file():
        return index_file.read_text(encoding="utf-8")

    return f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Exitwise — Dependency Exit Capsules</title>
  <style>
    :root {{
      --bg: #09090b;
      --bg-raised: #0f0f12;
      --bg-sunken: #060607;
      --text: #fafafa;
      --text-2: #d4d4d8;
      --text-3: #a1a1aa;
      --text-4: #71717a;
      --line: rgba(255, 255, 255, 0.08);
      --accent: #5b8cff;
      --accent-2: #22d3ee;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      --font-mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text-2); font-family: var(--font-sans); padding: 48px 24px; }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .eyebrow {{ font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.14em; color: var(--text-4); margin-bottom: 12px; }}
    h1 {{ font-size: 40px; color: var(--text); margin-bottom: 12px; font-weight: 600; }}
    h1 em {{ font-family: Georgia, serif; font-style: italic; color: var(--accent); }}
    p.sub {{ font-size: 18px; color: var(--text-3); margin-bottom: 40px; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--bg-raised); border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }}
    th {{ padding: 14px 18px; text-align: left; background: var(--bg-sunken); font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; color: var(--text-4); border-bottom: 1px solid var(--line); }}
    td {{ padding: 16px 18px; border-bottom: 1px solid var(--line); }}
    tr:last-child td {{ border-bottom: none; }}
    .verdict-badge {{ padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
    .verdict-ready {{ background: rgba(52, 211, 153, 0.2); color: #34d399; }}
    .verdict-warning {{ background: rgba(251, 191, 36, 0.2); color: #fbbf24; }}
    .verdict-blocked {{ background: rgba(248, 113, 113, 0.2); color: #f87171; }}
    .verdict-neutral {{ background: rgba(161, 161, 170, 0.2); color: #a1a1aa; }}
    .action-btn {{ font-size: 13px; color: var(--text); text-decoration: none; border: 1px solid var(--line); padding: 6px 12px; border-radius: 6px; cursor: pointer; }}
    .action-btn:hover {{ background: rgba(255, 255, 255, 0.08); }}
    code {{ font-family: var(--font-mono); font-size: 12px; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="eyebrow">DEPENDENCY EXIT CAPSULES · INDEX</div>
    <h1>Exitwise. <em>Resilience</em> Dashboard.</h1>
    <p class="sub">Evaluated dependencies for <code>{html.escape(repo_url)}</code>.</p>
    <table>
      <thead>
        <tr>
          <th>Dependency</th>
          <th>Pinned</th>
          <th>Latest</th>
          <th>Coupling</th>
          <th>Candidate</th>
          <th>Verdict</th>
          <th>Trust Distribution</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</body>
</html>
"""
