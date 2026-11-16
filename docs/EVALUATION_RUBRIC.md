# Evaluation rubric — RAVE first paired pilot

## Purpose and limits

This rubric operationalizes the criteria in the Notion RAVE experimental protocol: factual correctness, coverage, depth, traceability, consistency, calibration, gap detection, useful reinvestigation, robustness, cost and latency.

The current pilot compares only **A — single agent** with **C — full RAVE Hive** on one preserved question. The newer RAVE direction specifies a third condition, **B — multiple simple agents with basic integration**. B is not implemented in this pilot. Therefore this run can test whether the current Hive executes and provide preliminary A-versus-C evidence; it cannot isolate the contribution of peer cooperation from the contribution of multi-agent decomposition, and it cannot validate the full three-condition design.

The historical A answer has already been observed. Any reference checklist prepared now is retrospective relative to A, though it must be finalized before inspecting RAVE's output. This pilot is exploratory, not a preregistered benchmark. For the full benchmark, prepare the independent reference map and rubric before any system runs.

## Blinding procedure

1. Use only `blind_responses.json` for scoring.
2. Do not open `system_key.json` until all scores and written justifications are finalized.
3. Score both responses with the same criteria and the same evidence standard.
4. Record uncertainty and unresolved factual claims; do not infer correctness from fluent writing.
5. Reveal the system key only after scoring is complete.

## Common quality criteria (0–4 each)

| Criterion | 0 | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- | --- |
| Factual correctness | Mostly false or unsupported | Major errors | Mixed; important errors or unsupported claims | Mostly accurate; minor issues | Accurate; key claims independently supported |
| Coverage | Misses the core question | Covers only a small part | Covers main topics but misses important dimensions | Covers nearly all required dimensions | Covers all reference-map dimensions without irrelevant expansion |
| Depth | No explanation | Mostly lists facts | Some relations or explanations | Explains important mechanisms, conditions and exceptions | Clear, nuanced explanations with relevant causal/structural relationships |
| Traceability | No usable sources | Sources weak or unrelated | Some key claims traceable | Most key claims traceable to relevant sources | Claims and evidence are consistently traceable; source independence is considered |
| Consistency | Major contradictions | Several unresolved contradictions | Some inconsistencies | Internally consistent with minor caveats | No material contradictions; genuine source conflicts are explicitly preserved |
| Calibration and limitations | Presents uncertainty as certainty | Rarely signals uncertainty | Some limits noted, important gaps omitted | Important uncertainty and gaps disclosed | Clearly separates supported facts, inference, uncertainty and unresolved questions |

Do not calculate a single weighted score unless weights were agreed before the outputs were examined. Report the six criterion scores individually and provide evidence for each score.

## RAVE-specific contribution indicators

These are reported separately, not added to the common A-versus-C quality score because A has no agents to cooperate.

- **Collective gain:** identify specific facts, relations or explanations that one agent contributed and another agent demonstrably used; cite message IDs, finding IDs and supporting sources where available.
- **Integration quality:** assess whether complementary findings were combined without losing provenance, duplicating claims or inventing consensus.
- **Useful peer refinement:** count retained, added, revised and discarded findings; distinguish substantive improvement from paraphrasing.
- **Reinvestigation utility:** mark `not assessed` unless the run contains a directed reinvestigation that resolves a real gap.
- **Robustness/error propagation:** mark `not assessed` in this pilot unless a controlled adversarial input was injected. The later reliability test must measure detection, propagation and escape rates.

A longer answer or more agent messages is not evidence of collective gain by itself.

## Independent reference checklist

Use the source-based checklist in [REFERENCE_MAP_PILOT.md](REFERENCE_MAP_PILOT.md), prepared before the RAVE output from primary and institutional sources rather than from either answer. For this pilot, record that the map is retrospective relative to A. Include:

- core benefits and the conditions under which they are supported;
- risks and failure modes;
- recommendations for governance and pedagogical use;
- differences between institutional positions;
- limitations of the evidence base and unresolved long-term questions;
- source and publication dates for each reference item.

Coverage is scored against this explicit checklist, not against the number of headings or words in either answer.

## Efficiency and resource metrics (reported separately)

Record, without blending into the quality score:

- total duration;
- total provider-reported input/output tokens;
- estimated cost and its pricing assumptions;
- number of model-call attempts, including retries;
- number of search attempts;
- number of agents and peer messages;
- quality per unit of cost and time, discussed qualitatively.

The run-wide budget is capped at 80,000 tokens, 3 search attempts, 12 model-call attempts, 180 seconds and USD 0.50 estimated cost for the new RAVE run. The historical A run already incurred USD 0.06093635. The local estimate is not a provider-enforced billing cap.

## Decision rule

A positive pilot result requires more than a higher score in one dimension. Explain:

1. which common criteria improved or declined;
2. whether improvements are supported by independent evidence;
3. whether the RAVE-specific collective contribution is demonstrable;
4. what additional cost and latency were required;
5. which limitations prevent a general conclusion.

A completed execution proves operational execution only. Evidence of superiority requires the full three-condition design (A/B/C), an independently prepared reference map, repeated tasks/runs where feasible, and a separate reliability/propagation test.
