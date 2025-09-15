## Plan: Use OpenAI to derive category, title, and preview for SpecStory sessions

### Goals and outputs

- **category**: one of `plan`, `codegen`, `refactor`, `debug`, `feature`, `review`, `meta`, `config`
- **title**: concise, descriptive, Title Case; ≤ 80 chars
- **preview**: 1-sentence summary of the user’s request; ≤ 120 chars; no markdown

### System prompt (for OpenAI system role)

```text
You are an expert product analyst for software engineering sessions. Given the content of a single
SpecStory session (extracted from a markdown conversation), produce a structured summary.

Output STRICT JSON with keys: category, title, preview. No extra fields, comments, or prose.

Requirements:
- category: choose exactly one from {plan, codegen, refactor, debug, feature, review, meta, config}.
  • plan: questions about approach/strategy/design
  • codegen: requests to create/implement/add/build/integrate code
  • refactor: improvements/renames/reorg/cleanup
  • debug: errors/why/fix/bug/problem
  • feature: change/update/allow/adjust/show/trigger/selecting (non-refactor changes)
  • review: explain/critique/understand/code review
  • meta: git/commit/merge/branch/CI
  • config: inputs/parameters/settings/configuration requirements
- title: Title Case, specific and action-oriented. If the user asks a question, convert to a clear,
  descriptive title (e.g., "How To Abort A Git Merge"). No punctuation at end.
- preview: One short sentence summarizing the user’s ask or the task outcome. ≤ 120 chars. No markdown.

Decision rules:
- Use the user’s first concrete ask as the primary signal. If multiple asks, pick the dominant one.
- Prefer the explicit action requested over surrounding narration.
- Never output unknown/other for category; choose the closest match.
- Be consistent in tense and naming within a single result.

Return format:
{"category":"...","title":"...","preview":"..."}
```

### User message template (what we send per session)

```text
Filename: {{filename}}
Timestamp: {{timestamp_iso}}

User request (excerpt):
{{first_user_message_or_concise_excerpt}}

Assistant/system context (optional, brief):
{{optional_context}}

Task: Produce JSON with keys category, title, preview.
```

### Examples

- Input: "change the color of the static ball to fully black"
  - Output:
  ```json
  {
    "category": "feature",
    "title": "Change Static Ball Color To Black",
    "preview": "Make the static ball fill pure black."
  }
  ```
- Input: "how to abort merge"
  - Output:
  ```json
  {
    "category": "meta",
    "title": "How To Abort A Git Merge",
    "preview": "Explain how to safely abort a git merge."
  }
  ```

### Implementation steps

1. Extraction
   - For each `.md` in `.specstory/history/`, extract:
     - filename, derived timestamp from its name
     - first user request (or a concise excerpt if long)
2. OpenAI call
   - Model: any reliable reasoning model; temperature 0.0
   - Messages:
     - system: System prompt above
     - user: Filled user template above
   - Response: parse single JSON object; reject non-JSON
3. Validation
   - category in allowed set; else map via simple synonyms, then fallback to `codegen`
   - truncate title (≤ 80) and preview (≤ 120) hard limits
4. Caching & rate limits
   - Cache by file hash; skip reprocessing when unchanged
   - Batch with small concurrency; exponential backoff on 429/5xx
5. Persistence
   - Replace current heuristic categorization in `cursor-history/timeline-data.json`
   - Preserve existing structure: sessions[], categories{}, metadata{}
6. QA checks
   - Spot-check 10 random entries for category correctness and title clarity
   - Re-run only failed items; commit updated JSON

### Output contract (JSON per session)

```json
{
  "category": "<one_of_allowed>",
  "title": "<Title Case>",
  "preview": "<≤120 chars>"
}
```

### Edge cases

- Empty or non-informative user text → infer from filename; set category to closest plausible
- Multiple intents → choose dominant first actionable request
- Very long inputs → summarize core ask in preview

### Next steps

- Implement API client in `cursor-history/parse_spechistory.py` with a `--use-openai` flag
- Add `.cache/` directory for per-file response caching
- Add a dry-run mode that prints proposed changes without writing JSON
