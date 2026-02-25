from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.domain.value_objects.action import EditorResult, HtmlPatch
from app.domain.value_objects.enums import PatchAction

# ─────────────────────────── Prompt ───────────────────────────────────────
# Full reproduction of the HTML_EDIT_PROMPT from paper Appendix C.4.

HTML_EDIT_PROMPT = """\
You are an assistant that edits self-contained HTML snapshots in
response to natural language edit requests. You receive:
1) the full HTML source of a single page
2) an unambiguous target element locator
3) a user request describing the intended change

Your job is to output a structured set of minimal changes that
apply the user's request without breaking existing behavior.

Contract
- Input fields:
  - html: a complete HTML snapshot that can be opened directly in
    a browser. It may include inline <style> and <script> tags.
    No external network access should be required.
  - target: one of:
    - a CSS selector string
    - a unique element marker: <!--TARGET-START--> ...
      <!--TARGET-END-->
    - a short HTML snippet exactly as it appears in html
  - policy: optional constraints

- Output format:
Return a single JSON object in a fenced code block with keys:
{
  "status": "ok" | "ambiguous" | "impossible",
  "patches": [
    {
      "selector": "<css selector>",
      "action": "<action type>", // e.g. "replace_text",
        "add_class", "remove_attribute"
      "value": "<new value or delta>",
      "rationale": "<short reason>"
    }
  ],
  "notes": "<short guidance or summary of changes>"
}

- Only output the minimal necessary `patches` to satisfy the
  request.

- Each patch should be atomic and directly applicable using
  `document.querySelector`.

- Do not output full HTML documents.
- Do not include markdown, explanations, or any extra text.

Allowed patch actions
- replace_text: Replace innerText of the selected element
- set_attribute: Set or replace an attribute (requires "name"
  key)
- remove_attribute: Remove a named attribute (requires "name"
  key)
- add_class / remove_class: Modify classList
- insert_before / insert_after / replace_element /
  remove_element: Structural changes
- append_child: Add a new child (must include 'value' as HTML
  string)
- inject_style: Add <style> block content (only once, use
  selector-scoped rules)

Target element resolution
1) Use <!--TARGET-START--> ... <!--TARGET-END--> if present
2) Else query CSS selector. If multiple matches, set
   status:"ambiguous" and explain.
3) Else match exact snippet. If not found, status:"impossible".

Edit policy
- Text: change only requested text nodes.
- Style: prefer classes and <style> blocks over inline style.
- Moves: relocate elements without unrelated rewrites.
- Attributes: preserve unrelated attributes.
- Scripts: append minimal, non-invasive code in <script
  id="llm-edits"> at end of <body>.
- Safety: no analytics, remote fetches, or external resources
  unless explicitly allowed.

Ambiguity & refusal
- If unclear/conflicting, return status:"ambiguous" and explain.
- If impossible within constraints, return status:"impossible"
  and explain.

Validation
- Ensure all selectors are valid.
- Ensure actions are minimal and can be applied with a DOM
  patcher.
- Do not return modified_html.

Respond only with the JSON object in a fenced code block. Do not
include extra commentary.
"""


class EditorAgent(BaseAgent):
  """
  Agent that receives natural-language edit instructions and generates HTML patches.

  Design decisions (paper 5.1.3 / Appendix C.4):
    - Two modes: CSS-level editing (UI toolbar) / natural-language editing (chat)
    - This agent handles the natural-language editing mode
    - LLM: claude-sonnet-4-6 (requires accurate structural understanding of HTML/CSS)
    - temperature=0 (deterministic)
    - Maximum tokens: 8192 (in case large patches are needed)
  """

  async def run(
    self,
    html: str,
    target: str,
    instruction: str,
    policy: str = "",
  ) -> EditorResult:
    """
    Generate fix patches for an HTML snapshot.

    Parameters
    ----------
    html:
        The full HTML snapshot to be modified
    target:
        CSS selector / <!--TARGET-START-->..<!--TARGET-END--> / HTML snippet
    instruction:
        Natural-language edit instruction
    policy:
        Optional constraints

    Returns
    -------
    EditorResult
        Fix result containing status, patches, and notes
    """
    user_content = json.dumps(
      {
        "html": html,
        "target": target,
        "request": instruction,
        "policy": policy,
      },
      ensure_ascii=False,
    )

    raw = await self._call(
      system=HTML_EDIT_PROMPT,
      user=user_content,
      temperature=0.0,
      max_tokens=8192,
    )

    json_str = self._extract_json(raw)
    parsed: dict = json.loads(json_str)

    patches = [
      HtmlPatch(
        selector=p["selector"],
        action=PatchAction(p["action"]),
        value=p.get("value"),
        name=p.get("name"),
        rationale=p.get("rationale", ""),
      )
      for p in parsed.get("patches", [])
    ]

    return EditorResult(
      status=parsed["status"],
      patches=patches,
      notes=parsed.get("notes", ""),
    )
