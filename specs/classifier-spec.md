# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Tier definitions

*Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications.*

**safe:**
```
Routine maintenance and low-risk repairs where mistakes result only in cosmetic damage or a broken fixture, not injury, fire, flooding, or structural damage.
```

**caution:**
```
Repairs involving water or electrical systems where mistakes have real cost or mild risk of injury, but do not require a professional license or building permit.
```

**refuse:**
```
Repairs where amateur mistakes can cause fire, flooding, structural failure, serious injury, or death — or where building codes require a licensed professional and a permit.
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
Definitions + few-shot examples. Provide the three tier definitions above, then 3-5 concrete examples per tier — especially emphasizing the "replacing existing" vs. "adding new" distinction for electrical work. The example "Can I add a new outlet?" → refuse contrasts with "Can I replace a broken outlet?" → caution, which is the single most important edge case.

Ask the LLM to output the tier and reason directly (not step-by-step), keeping responses concise. Few-shot examples are more reliable than step-by-step reasoning for boundary cases because they show the actual decision pattern without making the LLM over-explain.

Ambiguous framing ("just a small fix") gets classified based on what the repair actually requires, not how the user has framed it. An example in the few-shot set ("Can I move a light switch six inches?") → refuse demonstrates this.
```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
Format: "Tier: {tier} / Reason: {reason}"

Example: "Tier: refuse / Reason: Requires running new electrical circuits from the breaker panel, which demands a licensed electrician and permit."

Parsing: Split on " / " to get tier and reason parts. Strip whitespace and validate tier against VALID_TIERS. If the exact format isn't found or tier validation fails, fall back to tier="caution".

This format is explicit enough that the LLM is unlikely to deviate, and simple enough to parse with a single split operation.
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
You are a safety classifier for home repair questions. Classify each question into one of three tiers based on the potential consequences if the repair is done incorrectly.

Tier Definitions:

safe: Routine maintenance and low-risk repairs where mistakes result only in cosmetic damage or a broken fixture, not injury, fire, flooding, or structural damage.

caution: Repairs involving water or electrical systems where mistakes have real cost or mild risk of injury, but do not require a professional license or building permit.

refuse: Repairs where amateur mistakes can cause fire, flooding, structural failure, serious injury, or death — or where building codes require a licensed professional and a permit.

Critical edge case — Electrical work:
- "Can I replace a broken outlet?" → caution (swapping a component at the same location, no new wiring)
- "Can I add a new outlet to my garage?" → refuse (requires new circuit from breaker panel, fire hazard)
- "Can I replace a light switch?" → caution (same location, like-for-like)
- "Can I move a light switch six inches?" → refuse (requires new wiring through walls)

Other critical rules:
- Any question about removing a wall → refuse (unless user has confirmation from a structural engineer that it's non-load-bearing)
- Any gas work (lines, appliances, smell) → refuse (always, no safe DIY repairs)
- Water heater replacement → refuse (permit required, explosion risk if pressure valve installed incorrectly)
- Questions framed as "just a small fix" are classified based on actual scope, not framing ("I just need to extend the gas line a little" → refuse)

Respond in this format: Tier: {tier} / Reason: {one sentence explaining the classification}
```

**User message:**
```
Classify this home repair question:

{question}
```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
Rule: If the repair, done incorrectly, can cause fire, flooding, structural failure, serious injury, or death — or if building codes require a licensed professional and a permit — classify as refuse; otherwise classify as caution.

Example 1: "How do I replace a toilet flapper?"
→ caution
Why: Mistake results in a running toilet or leak — real cost but no injury/fire/flood risk. No permit required. Worst case: water bill spike and calling a plumber. Within homeowner scope.

Example 2: "How do I run a new electrical circuit to my garage?"
→ refuse
Why: Requires opening the breaker panel and running new wire. Improper installation can cause electrical fire or electrocution. Requires permit and licensed electrician in most jurisdictions. High consequences, beyond safe homeowner scope.
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
Fallback: Return {"tier": "caution", "reason": "Could not classify response — defaulting to caution for safety."}

Failing closed is correct here. If the classifier's response is unparseable or the tier isn't in VALID_TIERS, returning "caution" ensures:
1. Safe questions still get answered (caution responses are helpful)
2. Dangerous questions get guardrails, not a free pass
3. A parsed "safe" is never accidentally served when we're uncertain

This matches the principle of "when in doubt, be conservative." The worst failure mode is an unparseable response that accidentally returns "safe" and allows dangerous instructions. The safe failure is to over-caution slightly, which the responder layer can handle gracefully.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
None — all test cases matched expectations. The few-shot examples in the system prompt were explicit enough that the LLM classified edge cases correctly on first try. Critical cases: "Can I add a new outlet?" → refuse (correct), "Can I move a light switch six inches?" → refuse (correct, despite "small fix" framing). The specification was precise enough that no surprises occurred.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
No changes needed. The prompt structure with concrete edge case examples was sufficient. The LLM consistently applied the "replacing vs adding" distinction, correctly identifying that even moving a switch 6 inches requires new wiring (refuse) vs replacing an existing switch at the same location (caution). The few-shot approach eliminated the need for iterative prompt refinement.
```
