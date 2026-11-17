# Tangled Phase 3 ML Classification & Learning-Signal Evaluation

## 1. Executive summary

**Final verdict: PARTIALLY VERIFIED**

Phase 3 evaluated the existing classification and learning-signal pipeline without
changing prompts, thresholds, or aggregation rules. A disposable, de-identified
60-utterance set was run against the configured OpenAI-compatible provider. Of
60 requests, 54 completed and 6 failed with provider `RateLimitError`; failed
requests were excluded from classification quality metrics and reported
separately.

Among successful real-provider classifications, accuracy was **0.907** and
macro-F1 was **0.903**. Information questions generated two false confusion
signals, while three `other` examples were classified as information. Evidence
phrases were exact substrings for all successful predictions, but semantic
support was not independently established for every item. The evaluation had no
gold-positive misconception examples, so misconception precision/recall/F1 are
not estimable. Topic assignment and deterministic aggregation behaved as
designed in the disposable checks. The pipeline is therefore useful for
instructor review, but not sufficiently verified to claim reliable autonomous
classification.

## 2. Existing classification architecture

The background job in `backend/app/services/analysis.py`:

1. Loads the message and idempotent `AnalysisJob`.
2. Assigns a course-scoped topic using embedding similarity, unless a valid
   course-scoped `concept_id` already exists.
3. Sends the student message and topic passage to the configured LLM with a
   rubric requesting `intent`, confidence, misconception, and evidence phrase.
4. Parses and validates the JSON with the `Classification` Pydantic model.
5. Requires a non-empty evidence phrase to be an exact substring when supplied.
6. Stores intent, confidence, misconception, phrase, topic, and job status.
7. Retries provider failures according to the existing analysis loop and records
   only the exception type on failure.

The allowed intents are `confusion`, `information`, and `other`. The default
backend is `llm`; the repository also contains a logistic-regression backend,
but it was not used for this real-provider baseline.

Instructor aggregation in `backend/app/services/insights.py` is course and
topic scoped. Confusion counts require `intent == "confusion"` and confidence
at least `settings.min_conf`. Distinct students are counted from student IDs,
and information messages are counted separately. `backend/app/services/rules.py`
then produces `none`, `watch`, or `needs_attention`; the latter requires the
configured minimum number of confused students plus quiz corroboration or
persistent confusion.

## 3. Evaluation dataset and rubric

The disposable dataset contained **60 de-identified synthetic utterances**:

| Gold class | Count | Coverage |
|---|---:|---|
| confusion | 20 | Explicit misunderstanding, requests to re-explain, apparent contradictions, incorrect interpretations, partial understanding, clarification after an answer |
| information | 20 | Definitions, factual questions, examples, summaries, procedural instructions, normal curiosity |
| other | 20 | Greetings, thanks, administrative questions, irrelevant content, incomplete or unclear messages |

Each record had a unique test ID, synthetic message, gold class, expected topic
where applicable, explicit-misconception flag, supporting evidence, and
annotation rationale. The records were generated for the run and were not
stored in production data or committed to the repository.

Annotation rubric:

- Classify as `confusion` only when the utterance expresses difficulty,
  contradiction, misunderstanding, or an incorrect interpretation.
- Classify ordinary factual, definition, example, summary, and procedure
  requests as `information` unless confusion is explicitly expressed.
- Use `other` for social, administrative, irrelevant, incomplete, or
  insufficiently specified messages.
- Mark misconception only when the student states or clearly implies an
  incorrect belief; confusion alone is insufficient.
- Evidence must be grounded in the student’s words, not inferred intent.

There was no second annotator. Cohen’s kappa is therefore **NOT VERIFIED**.
The labels are single-annotator gold labels for this disposable evaluation.

## 4. Real LLM classification baseline

Evidence type: **REAL LLM EVALUATION**.

The existing LLM prompt and thresholds were unchanged. Calls were made
sequentially after a concurrent attempt produced provider throttling; no failed
request was converted into a prediction.

### 4.1 Results

| Result | Count |
|---|---:|
| Total cases | 60 |
| Successful predictions | 54 |
| Provider `RateLimitError` failures | 6 |
| Successful prediction rate | 90.0% |

Confusion matrix for successful predictions (rows are gold, columns are
predicted):

| Gold \ Predicted | confusion | information | other |
|---|---:|---:|---:|
| confusion | 20 | 0 | 0 |
| information | 2 | 14 | 0 |
| other | 0 | 3 | 15 |

Metrics are calculated over the 54 successful predictions:

| Class | Precision | Recall | F1 |
|---|---:|---:|---:|
| confusion | 0.909 | 1.000 | 0.952 |
| information | 0.824 | 0.875 | 0.848 |
| other | 1.000 | 0.833 | 0.909 |
| **Macro average** | **0.911** | **0.903** | **0.903** |
| **Weighted average** | **0.908** | **0.907** | **0.907** |

Overall successful-case accuracy was **0.907**. The principal safety concern
was the two normal information questions classified as confusion. Three
administrative/irrelevant `other` cases were classified as information.
Provider failures are operational failures, not classification successes, and
must be included in availability planning.

### 4.2 Confidence and abstention

Evidence type: **REAL LLM EVALUATION**.

The provider returned confidence values in the requested schema. The recorded
latency range was approximately **823 ms to 7,026 ms**, with median
approximately **2,144 ms**. A full calibration curve and statistically robust
confidence calibration analysis were not completed. No new confidence
threshold or abstention policy was introduced.

The existing design can produce `other`, but the real baseline did not treat
provider failure as a conservative classification; failures become
`analysis_failed`. This is preferable to manufacturing a success-shaped signal,
but the operational impact of six rate-limit failures remains unverified under
normal production load.

## 5. Evidence phrase evaluation

Evidence type: **REAL LLM EVALUATION** plus **MANUAL REVIEW limitation**.

| Measure | Result |
|---|---:|
| Evidence phrase coverage among successful predictions | 54/54 (100%) |
| Exact substring validity | 54/54 (100%) |
| Semantic support accuracy | Not fully verified |

The implementation rejects a returned phrase that is not an exact substring of
the student message. Exact-substring validity does not prove that the phrase
supports the predicted class or that it is useful to an instructor. A complete
independent semantic review was not performed, so no stronger support metric is
claimed.

## 6. Misconception detection

Evidence type: **REAL LLM EVALUATION**, with an insufficient gold set.

The baseline produced **14 positive misconception predictions**, but the
60-record synthetic set contained **zero gold-positive misconception cases**.
Consequently, precision, recall, F1, and false-positive rate are
**NOT VERIFIED** and must not be inferred from the 14 predictions. This is a
dataset limitation, not evidence that the detector is accurate.

## 7. Topic assignment

Evidence type: **DETERMINISTIC UNIT TEST / MANUAL VERIFICATION** using a
disposable SQLModel database and the existing embedding implementation.

Eight labelled messages were evaluated against two course-1 topics, including
an unrelated message, an ambiguous message, and a course-isolation setup.

| Measure | Result |
|---|---:|
| Exact topic accuracy | 7/8 (87.5%) |
| Missing-topic rate | 1/8 (12.5%) |
| Invalid-topic rate | 0/8 (0%) |
| Incorrect topic assignment rate | 1/8 (12.5%) |
| Cross-course topic leakage | 0 observed |

The one incorrect assignment was an intentionally ambiguous message mentioning
both course topics. The topic lookup and pre-existing topic validation were
course-scoped; a concept from another course was not returned.

## 8. Aggregation and instructor insight evaluation

Evidence type: **DETERMINISTIC UNIT TEST** and **MANUAL VERIFICATION** with
controlled synthetic database rows.

Verified behaviors:

- Two confusion messages from one student counted as one distinct confused
  student.
- Two additional distinct confused students produced `students_confused = 2`
  and the expected `watch` tier.
- Information messages increased `info_msgs` but did not independently create
  a confusion signal.
- Persistence is based on students with at least two confusion messages.
- Quiz corroboration is part of the existing `needs_attention` rule.
- Course and concept filters are applied to aggregation queries.
- Existing rule tests cover addressed/false-alarm behavior through the
  course-level insight query paths and the repository’s verdict handling.

The controlled aggregation probe produced 4 students asked, 2 distinct
students confused, 3 confusion messages, 2 information messages, and tier
`watch`. No production thresholds or rule behavior was changed.

## 9. Reliability and regression testing

The six provider rate-limit failures are the only failures observed in the
real classification run. They prevent a complete 60-case real-provider
baseline and demonstrate that provider availability is a material limitation.
The provider retry behavior itself was previously covered in Phase 2 by
controlled local HTTP tests; that evidence does not substitute for a
provider-generated classification evaluation.

Required regression commands:

| Command | Result |
|---|---|
| `cd backend; pytest -q` | **PASS — 40 passed, 1 warning, 10.44s** |
| `cd frontend; npm run test` | **PASS — 2 files, 10 tests, 8.81s** |
| `cd frontend; npm run build` | **PASS — TypeScript check and Vite production build** |
| `git diff --check` | **PASS** |

## 10. Files modified

For Phase 3, only this report was created. No classifier, prompt, threshold,
aggregation rule, frontend behavior, or production data was modified. Existing
uncommitted Phase 1 and Phase 2 changes were preserved.

## 11. Known limitations and recommended next steps

1. Repeat the real-provider run under an approved rate-limit-safe test budget
   so all 60 cases complete, or document a provider quota specifically
   allocated for evaluation.
2. Add a balanced misconception-positive and misconception-negative set before
   reporting misconception metrics.
3. Use two independent annotators for a future gold set and calculate Cohen’s
   kappa.
4. Perform blinded semantic review of evidence phrases and claim support.
5. Evaluate confidence calibration with a larger completed set.
6. Keep information-vs-confusion false positives as a primary regression target.

## 12. Final conclusion

The existing pipeline produced promising results on 54 successful real-provider
classifications and deterministic aggregation behaved consistently with the
specified privacy-conscious rules. However, provider failures, missing
misconception-positive labels, absent inter-annotator agreement, and incomplete
semantic evidence review mean the learning-signal pipeline is not yet
verified as sufficiently accurate and evidence-backed for a reliability claim.

**Phase 3 verdict: PARTIALLY VERIFIED.**

Application code did not change during Phase 3. Phase 4 should not treat this
baseline as proof of classifier reliability; it may begin only with the
limitations above explicitly carried forward.

## Phase 3.1 — Evaluation Gap Closure

### Expanded dataset and annotation methodology

Evidence source: **REAL LLM EVALUATION** using a disposable synthetic dataset.

The expanded run contained **105 de-identified examples**:

- 20 explicit or implicit confusion examples.
- 35 information examples, including factual questions, definitions,
  examples, summaries, procedures, and curiosity.
- 35 other examples, including administrative, conversational, irrelevant,
  incomplete, and ambiguous messages.
- 15 explicit misconception-positive statements.
- 15 misconception-negative statements, including ordinary questions,
  confusion without a misconception, correct statements, and ambiguous
  statements.

The misconception-positive and negative records were labelled independently
from the intent label. No real student data was used. The original 60-case
results remain unchanged above; this section reports the separate expanded
run.

The configured model was `gemini-3.5-flash-lite`, with the existing
OpenAI-compatible client setting `max_retries=1`. Prompts and thresholds were
not changed.

### Updated classification metrics

Evidence source: **REAL LLM EVALUATION**. Provider failures were excluded from
quality denominators and reported separately.

| Result | Count |
|---|---:|
| Expanded cases attempted | 105 |
| Successful predictions | 87 |
| Provider `RateLimitError` failures | 18 |
| Successful prediction rate | 82.9% |

Confusion matrix for the 87 successful predictions:

| Gold \ Predicted | confusion | information | other |
|---|---:|---:|---:|
| confusion | 15 | 0 | 0 |
| information | 17 | 24 | 0 |
| other | 14 | 6 | 11 |

| Class | Precision | Recall | F1 |
|---|---:|---:|---:|
| confusion | 0.326 | 1.000 | 0.492 |
| information | 0.800 | 0.585 | 0.676 |
| other | 1.000 | 0.355 | 0.524 |
| **Macro-F1** |  |  | **0.564** |
| **Weighted-F1** |  |  | **0.590** |

Successful-case accuracy was **0.575**. The information-to-confusion
false-positive rate was **17/41 = 41.5%** among successful information
examples. The other-to-confusion rate was **14/31 = 45.2%**. These results
are substantially weaker than the original 60-case run and show that the
classifier's false-positive behavior is not stable across synthetic prompt
sets.

Representative failures:

- `I06`: “Which steps should I follow to find a limit?” → `confusion`.
- `I10`: “What is the difference between velocity and acceleration?” →
  `confusion`.
- `O18`: “I have a question.” → `confusion`.
- `A01`: “How do derivatives work?” → `confusion`.

### Misconception confusion matrix and metrics

Evidence source: **REAL LLM EVALUATION**, on successful misconception cases
only.

Of the 30 balanced misconception cases, 23 completed successfully: 12
positive and 11 negative. The remaining 7 were provider rate-limit failures
(3 positive and 4 negative), so they were not counted as positive or negative
predictions.

| Gold \ Predicted | misconception true | misconception false |
|---|---:|---:|
| misconception true | 12 | 0 |
| misconception false | 0 | 11 |

| Measure | Result |
|---|---:|
| True positives | 12 |
| False positives | 0 |
| True negatives | 11 |
| False negatives | 0 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 | 1.000 |
| Specificity | 1.000 |
| False-positive rate | 0.000 |

These are incomplete-case metrics, not full-set metrics. They are therefore
promising but **NOT VERIFIED** as a complete misconception evaluation.
The current schema has no rationale field separate from `evidence_phrase`.
The 12 positive flags all included an exact phrase from the original message,
but rationale quality was not independently adjudicated for every item.

### Evidence semantic-support audit

Evidence source: **MANUAL REVIEW** plus deterministic checks.

For all 87 successful classifications:

| Measure | Result |
|---|---:|
| Evidence phrase present | 87/87 (100%) |
| Exact substring valid | 87/87 (100%) |
| Misconception-positive result without a phrase | 0/12 |
| Full semantic support accuracy | **NOT VERIFIED** |

Representative manual review found that explicit misconception phrases such as
“A limit always equals the function value at the point” directly support the
flag, while ordinary question phrases such as “what is the formal definition?”
do not assert a misconception. However, the full 87-item semantic audit was
not independently double-reviewed. Exact substring validation alone does not
establish that a phrase supports the predicted class or avoids an intent
inference.

### Expanded topic assignment evaluation

Evidence source: **DETERMINISTIC UNIT TEST** with the existing real embedding
implementation and a disposable SQLModel database.

Twenty labelled messages covered clear topics, overlapping terminology,
ambiguous messages, no-topic messages, same-named topics in separate courses,
and an explicit cross-course concept ID.

| Measure | Result |
|---|---:|
| Exact topic accuracy | 19/20 (95.0%) |
| Missing-topic predictions | 2/20 (10.0%) |
| Invalid-topic predictions | 0/20 (0.0%) |
| Wrong-topic predictions | 1/20 (5.0%) |
| Cross-course leakage | 0 observed |

The individual failure was `T13`, “derivative and integral”, which was assigned
to Derivatives although the annotation marked it ambiguous/no single topic.
The two missing predictions were intentionally no-topic messages. An explicit
message carrying a concept ID from course 2 was rejected for a course-1
message, confirming course isolation.

### Provider reliability results

Evidence sources: **REAL LLM EVALUATION**, **MOCKED PROVIDER TEST**, and
**CONTROLLED HTTP TEST**.

The expanded real-provider run had 18 `RateLimitError` failures. They were not
reclassified and did not produce successful message results. The configured
client used one SDK retry, and the classifier's `_classify` loop also permits
two classification attempts; provider behavior was kept separate from quality
metrics.

Controlled local HTTP results with the existing client:

| Scenario | Requests | Result |
|---|---:|---|
| HTTP 429 then success | 2 | Recovered |
| Persistent HTTP 429 | 2 | Final `RateLimitError` |
| HTTP 500 then success | 2 | Recovered in the prior Phase 2 controlled test |
| Persistent HTTP 500 | 2 | Final `InternalServerError` |
| Timeout | 2 | Final `APITimeoutError` |

A mocked analysis-job test then forced a provider timeout. The first attempt
left `Message.intent=analysis_failed`, `AnalysisJob.status=failed`, and only
the exception type in `last_error`. A subsequent retry changed the same job
to `done` and stored the successful result; no partial answer or classification
was stored during failure. This was a **MOCKED PROVIDER TEST**, not real
provider behavior.

### Phase 3.1 regression checks

Evidence source: **DETERMINISTIC UNIT TEST** and build execution.

| Command | Result |
|---|---|
| `cd backend; pytest -q` | **PASS — 40 passed, 1 warning** |
| `cd frontend; npm run test` | **PASS — 2 files, 10 tests** |
| `cd frontend; npm run build` | **PASS — TypeScript check and Vite build** |
| `git diff --check` | **PASS** |

No application code, prompt, threshold, aggregation rule, or frontend code
was modified in Phase 3.1. The only Phase 3.1 repository change is this
report.

### Remaining limitations and Phase 3.1 verdict

1. The expanded real-provider baseline has a high confusion false-positive
   rate, especially for ordinary information and ambiguous messages.
2. Misconception metrics cover only 23 of 30 cases because seven cases were
   rate-limited.
3. Full semantic evidence support was not independently reviewed for every
   successful prediction.
4. No second annotator was available, so Cohen's kappa remains unavailable.
5. Synthetic results do not establish production reliability.

**Phase 3.1 verdict: PARTIALLY VERIFIED.**

The provider failure path is safe in controlled tests and topic assignment is
course-isolated, but confusion false positives and incomplete misconception
and evidence audits prevent a `VERIFIED` verdict. Tangled is **not ready for
Phase 4 as a reliability claim**; Phase 4 may begin only as continued
evaluation or remediation work with these limitations carried forward.

## Phase 3.2 — Classifier Improvement & Comparative Evaluation

### Failure-pattern diagnosis

Evidence source: **MANUAL REVIEW** of the Phase 3.1 successful predictions.

The largest baseline error groups were ordinary technical questions and
ambiguous short messages. Direct factual questions, definition/procedure
requests, “why/how” questions, and technically difficult questions were often
treated as confusion despite no stated difficulty. Administrative messages
were sometimes treated as information, while incomplete messages such as “I
have a question” were sometimes treated as confusion. The observed pattern
indicates that the original rubric did not make the evidence-of-difficulty
requirement explicit enough.

### Rubric and implementation change

Evidence source: **CODE INSPECTION** and **DETERMINISTIC UNIT TEST**.

The only application change was the `RUBRIC` system prompt in
`backend/app/services/analysis.py`. It now:

- requires explicit evidence of difficulty, uncertainty, failed attempts,
  unresolved contradictions, difficulty following an explanation, or
  misunderstanding for `confusion`;
- explicitly classifies ordinary factual, definition, example, summary,
  procedure, curiosity, and technically difficult requests as `information`
  when difficulty is not expressed;
- reserves `other` for administrative, conversational, irrelevant, and
  insufficient messages; and
- requires misconception flags to represent a stated or clearly implied
  incorrect belief, not a question or confusion alone.

The output schema, three intent classes, evidence substring validation, topic
assignment, confidence threshold, retry behavior, and aggregation rules were
unchanged. No keyword rule or backend switch was added.

### Comparative evaluation

Evidence source: **REAL LLM EVALUATION** using the same 105-case dataset,
model (`gemini-3.5-flash-lite`), and evaluation labels. The original and
revised calls were separate provider runs; provider failures were excluded
from quality denominators and reported independently. Per-case original and
revised outputs are stored in [TANGLED_PHASE_3_2_RESULTS.json](./TANGLED_PHASE_3_2_RESULTS.json).

| Metric | Original Phase 3.1 | Revised Phase 3.2 |
|---|---:|---:|
| Cases attempted | 105 | 105 |
| Successful predictions | 87 | 80 |
| Provider failures | 18 | 25 |
| Accuracy | 0.575 | 0.875 |
| Macro-F1 | 0.564 | 0.863 |
| Weighted-F1 | 0.590 | 0.878 |
| Information → confusion FP rate | 41.5% (17/41) | 7.5% (3/40) |
| Other → confusion FP rate | 45.2% (14/31) | 18.2% (4/22) |

Original confusion matrix:

| Gold \ Predicted | confusion | information | other |
|---|---:|---:|---:|
| confusion | 15 | 0 | 0 |
| information | 17 | 24 | 0 |
| other | 14 | 6 | 11 |

Revised confusion matrix:

| Gold \ Predicted | confusion | information | other |
|---|---:|---:|---:|
| confusion | 17 | 1 | 0 |
| information | 3 | 35 | 2 |
| other | 4 | 0 | 18 |

Revised per-class metrics:

| Class | Precision | Recall | F1 |
|---|---:|---:|---:|
| confusion | 0.708 | 0.944 | 0.810 |
| information | 0.972 | 0.875 | 0.921 |
| other | 0.900 | 0.818 | 0.857 |

On the 66 cases completed successfully by both versions, the revised prompt
changed 23 predictions. It corrected most ordinary-question false positives:
`I06`, `I07`, `I10`, `I11`, `I12`, `I13`, `I18`, `I20`, `N01`, `N02`, `N03`,
`N04`, `N07`, `N08`, and `N15` moved from `confusion` to `information`.
One explicit confusion case moved from `confusion` to `information`, so
confusion recall was preserved at **0.944** in the revised successful set but
not perfectly preserved.

### Misconception and evidence regression

Evidence sources: **REAL LLM EVALUATION**, **MANUAL REVIEW**, and deterministic
substring checks.

On the 23 successfully completed misconception cases in the revised run,
the confusion matrix was **8 true positives, 0 false positives, 15 true
negatives, and 0 false negatives**. This gives precision 1.000, recall 1.000,
F1 1.000, specificity 1.000, and false-positive rate 0.000 for the completed
subset. The revised run had 7 provider failures across the balanced
misconception set, so full-set misconception preservation remains
**NOT VERIFIED**. The baseline completed subset had 12 true positives, 0
false positives, 11 true negatives, and 0 false negatives.

Among 80 revised successful predictions, evidence coverage was **80/80** and
exact-substring validity was **80/80**. All eight revised misconception
positive predictions included an exact phrase from the original message.
Semantic evidence support remains only partially manually reviewed; the
schema still has no separate misconception rationale field.

### Provider and regression results

Evidence sources: **REAL LLM EVALUATION**, **CONTROLLED HTTP TEST**, and
**DETERMINISTIC UNIT TEST**.

The revised run had **25 `RateLimitError` failures**, compared with 18 in the
baseline. This is an availability regression in these runs, not a
classification quality metric. Controlled Phase 3.1 tests remain valid:
transient HTTP 429 recovers in two requests, persistent 429 stops after two
requests, persistent 500 stops after two requests, and timeout failure is
surfaced without a partial result. The revised prompt did not alter retry or
persistence code.

| Command | Result |
|---|---|
| `cd backend; pytest -q` | **PASS — 40 passed, 1 warning** |
| `cd frontend; npm run test` | **PASS — 2 files, 10 tests** |
| `cd frontend; npm run build` | **PASS — TypeScript check and Vite build** |
| `git diff --check` | **PASS** |

### Phase 3.2 verdict and recommendation

The false-positive problem materially improved: information-to-confusion
errors fell from 41.5% to 7.5% in the successful evaluation denominators, and
other-to-confusion errors also fell. Genuine confusion recall remained high at
0.944, but one explicit confusion case was over-corrected and provider
failures increased from 18 to 25. Misconception and semantic evidence
preservation are promising but incomplete.

**Phase 3.2 verdict: PARTIALLY VERIFIED.**

The revised classifier is a meaningful improvement for this synthetic
evaluation, but it is not production-reliability evidence. Before Phase 4,
repeat the paired evaluation under a rate-limit-safe provider budget, complete
the semantic evidence review, and evaluate a larger independently annotated
set. Phase 4 should not assume the provider failure rate is acceptable.

## Phase 3.3 — Independent Validation & Reliability Evaluation

### Frozen implementation and independent dataset

Evidence source: **CODE INSPECTION** and **REAL PROVIDER EVALUATION**.

The Phase 3.2 classifier was frozen. The prompt, schema, confidence
thresholds, topic assignment, retry settings, and aggregation logic were not
changed during this evaluation. The configured model was
`gemini-3.5-flash-lite`, temperature `0`, client `max_retries=1`, and the
classifier's existing two-attempt loop.

A new dataset of **120 de-identified synthetic messages** was created in
[TANGLED_PHASE_3_3_INDEPENDENT_DATASET.json](./TANGLED_PHASE_3_3_INDEPENDENT_DATASET.json)
and independently annotated in
[TANGLED_PHASE_3_3_ANNOTATIONS.json](./TANGLED_PHASE_3_3_ANNOTATIONS.json):

| Class | Cases | Coverage |
|---|---:|---|
| confusion | 40 | Explicit and subtle difficulty, failed reasoning, contradictions, incorrect interpretations |
| information | 40 | Definitions, factual questions, examples, procedures, summaries, technical curiosity |
| other | 40 | Administrative, conversational, irrelevant, incomplete, and ambiguous messages |

One annotator was available; Cohen's kappa is **NOT VERIFIED**. Labels were
created before running the frozen classifier and were not changed after seeing
predictions. No real participant data was used.

### Independent classification results

Evidence source: **REAL PROVIDER EVALUATION**.

| Metric | Phase 3.2 | Independent Phase 3.3 |
|---|---:|---:|
| Cases attempted | 105 | 120 |
| Successful predictions | 80 | 90 |
| Provider failures | 25 | 30 |
| Classification coverage | 76.2% | 75.0% |
| Accuracy among successful cases | 87.5% | 98.9% |
| Macro-F1 | 86.3% | 98.8% |
| Weighted-F1 | 87.8% | 98.9% |
| Information → confusion FP rate | 7.5% | 0.0% |
| Other → confusion FP rate | 18.2% | 0.0% |

Independent confusion matrix among 90 successful cases:

| Gold \ Predicted | confusion | information | other |
|---|---:|---:|---:|
| confusion | 33 | 0 | 0 |
| information | 0 | 24 | 0 |
| other | 0 | 1 | 32 |

| Class | Precision | Recall | F1 |
|---|---:|---:|---:|
| confusion | 1.000 | 1.000 | 1.000 |
| information | 0.960 | 1.000 | 0.980 |
| other | 1.000 | 0.970 | 0.985 |

The only successful classification error was `OT18`, “Do we need
identification for the field trip?”, classified as `information`. The result
is encouraging on this independent synthetic set, but the 25% provider failure
rate means the headline quality metrics do not describe all attempted cases.
The independent dataset is also synthetic and single-annotator, so it does
not establish production generalization.

Per-case outcomes are preserved in
[TANGLED_PHASE_3_3_RESULTS.json](./TANGLED_PHASE_3_3_RESULTS.json). Provider
failures are recorded as `RateLimitError` and are not counted as correct or
incorrect classifications.

### Evidence quality audit

Evidence source: **MANUAL HUMAN REVIEW** plus deterministic checks.

Forty-five successful predictions were reviewed, 15 from each intent class,
using the rubric “the phrase must be an exact excerpt and must support the
predicted intent rather than merely repeat a topic or question.”

| Measure | Result |
|---|---:|
| Successful predictions with an evidence phrase | 90/90 (100%) |
| Exact substring validity | 90/90 (100%) |
| Manually reviewed predictions | 45 |
| Reviewed exact-substring validity | 45/45 (100%) |
| Reviewed semantic support | 41/45 (91.1%) |
| Reviewed prediction correctness | 45/45 (100%) |

The detailed review is in
[TANGLED_PHASE_3_3_EVIDENCE_AUDIT.json](./TANGLED_PHASE_3_3_EVIDENCE_AUDIT.json).
The 4 reviewed phrases marked semantically unsupported demonstrate why
substring validity is insufficient. The current schema still has no separate
misconception rationale field.

### Misconception validation

Evidence source: **REAL PROVIDER EVALUATION**.

A separate balanced 40-case subset (20 explicit incorrect beliefs and 20
negative cases) was evaluated. Results are in
[TANGLED_PHASE_3_3_MISCONCEPTION_RESULTS.json](./TANGLED_PHASE_3_3_MISCONCEPTION_RESULTS.json).
Thirty-three cases completed; seven were provider rate-limit failures.

| Gold \ Predicted | misconception true | misconception false |
|---|---:|---:|
| misconception true | 19 | 1 |
| misconception false | 0 | 13 |

On the 33 completed cases, precision was **1.000**, recall **0.950**, F1
**0.974**, specificity **1.000**, and false-positive rate **0.000**. Seven
cases failed with provider rate limits and were excluded from these quality
denominators. The completed-case result is promising but incomplete, so full
misconception reliability remains **NOT VERIFIED**. No confusion flag was
treated as a misconception automatically.

### Independent topic assignment and course isolation

Evidence source: **DETERMINISTIC TEST** using the existing embedding
implementation and disposable SQLModel database.

Thirty messages were evaluated across Physics, Biology, and History topics,
including overlapping/ambiguous terms, no-topic messages, same-named topics in
different courses, and an explicit cross-course concept ID.

| Measure | Result |
|---|---:|
| Exact topic accuracy | 24/30 (80.0%) |
| Missing-topic predictions | 6/30 (20.0%) |
| Correct no-topic handling | 3/6 no-topic cases |
| Wrong-topic assignments | 3/30 (10.0%) |
| Invalid-topic assignments | 0 |
| Cross-course leakage | 0 observed |

The three wrong assignments were ambiguous cross-topic prompts or a low-match
topic that was incorrectly assigned. Three valid topic cases fell below the
similarity threshold and returned no topic. The explicit concept from the
other course was rejected, preserving course isolation.

### Provider reliability and aggregation safety

Evidence sources: **REAL PROVIDER EVALUATION**, **CONTROLLED HTTP TEST**, and
**DETERMINISTIC UNIT TEST**.

The independent run had 30 `RateLimitError` failures out of 120 attempts.
The real provider response code was not available from the SDK exception
without exposing provider details; no credentials or provider response bodies
were recorded.

Controlled local results with the existing client and `max_retries=1`:

| Scenario | Requests | Observed result |
|---|---:|---|
| HTTP 429 then success | 2 | Recovered |
| Persistent HTTP 429 | 2 | Final `RateLimitError` |
| HTTP 500 then success | 2 | Controlled server response surfaced as `APIConnectionError` because the test response was not provider-compatible |
| Persistent HTTP 500 | 2 | `APIConnectionError` in this controlled harness |
| Timeout | 2 | Final `APITimeoutError` |

Earlier Phase 2 controlled tests with provider-compatible response bodies
verified transient HTTP 500 recovery and persistent 500 retry limits. A mocked
analysis-job recovery test verified that a failed attempt stores only
`analysis_failed` and the exception type, and a later successful attempt
completes the same job without a partial classification.

Existing deterministic aggregation tests and controlled probes confirm that:

- repeated questions from one student count once in distinct-student totals;
- information messages do not independently create confusion counts;
- one misconception flag does not establish a widespread insight;
- course and topic filters are preserved; and
- instructor evidence is aggregate phrase data rather than student identity or
  raw transcript exposure.

### Phase 3.3 regression results

Evidence source: **DETERMINISTIC UNIT TEST** and build execution.

| Command | Result |
|---|---|
| `cd backend; pytest -q` | **PASS — 40 passed, 1 warning** |
| `cd frontend; npm run test` | **PASS — 2 files, 10 tests** |
| `cd frontend; npm run build` | **PASS — TypeScript check and Vite build** |
| `git diff --check` | **PASS** |

### Phase 3.3 verdict and recommendation

The frozen Phase 3.2 classifier generalized well on the 90 completed cases
from this independent synthetic set: false-positive confusion rates were
0%, confusion recall was 100%, and macro-F1 was 98.8%. However, 30/120
provider calls failed, topic accuracy was 80%, semantic evidence support was
91.1% in the reviewed sample, misconception metrics were not finalized, and
annotation was single-annotator.

**Phase 3.3 verdict: PARTIALLY VERIFIED.**

Phase 4 should not begin as a production-reliability claim. Before it begins,
re-run the independent evaluation with a rate-limit-safe provider budget,
finalize the misconception confusion matrix, improve topic-assignment
coverage for ambiguous/low-similarity messages, and obtain independent
annotation or human review.

## Phase 3.4 — Real-World Classifier Validation

### Evaluation status

**NOT VERIFIED**

Evidence source: **NOT VERIFIED**.

Phase 3.4 required genuinely human-written student messages from an
authorized, consented, and anonymized source. No such dataset was available in
the repository or provided for this evaluation. The repository's available
classification artifacts are synthetic evaluation data from Phases 3.1–3.3;
they were not relabelled or presented as real-world data.

No private student conversations were accessed, no identifying data was
collected, and no real-world messages were sent to the configured provider.
The frozen Phase 3.2 classifier was not modified.

### Prepared artifacts

The following artifacts document the blocked evaluation and provide empty
schemas for a future authorized run:

- [TANGLED_PHASE_3_4_DATASET.json](./TANGLED_PHASE_3_4_DATASET.json)
- [TANGLED_PHASE_3_4_ANNOTATIONS.json](./TANGLED_PHASE_3_4_ANNOTATIONS.json)
- [TANGLED_PHASE_3_4_RESULTS.json](./TANGLED_PHASE_3_4_RESULTS.json)
- [TANGLED_PHASE_3_4_EVIDENCE_AUDIT.json](./TANGLED_PHASE_3_4_EVIDENCE_AUDIT.json)

All four artifacts intentionally contain zero real messages and null metrics.
They must not be interpreted as a completed real-world validation.

### Missing evidence

The following Phase 3.4 results are **NOT VERIFIED**:

- Accuracy, per-class precision/recall/F1, macro-F1, weighted-F1, and
  confusion matrix on human-written messages.
- Information-to-confusion and other-to-confusion false-positive rates.
- Human-annotated misconception precision, recall, F1, specificity, and
  false-positive rate.
- Human-message evidence phrase semantic support.
- Human-message topic assignment quality.
- Generalization beyond synthetic evaluation sets.

Existing synthetic results remain valid only as synthetic evidence:
Phase 3.3 completed 90/120 predictions with 30 provider rate-limit failures,
and its completed-case metrics must not be combined with or substituted for
Phase 3.4.

### Annotation protocol for a future authorized run

Use the same rubric as Phase 3.2 and independently label each authorized,
de-identified message for primary class (`confusion`, `information`, or
`other`), misconception, relevant topic, supporting evidence, confidence, and
ambiguity. Prefer two annotators, calculate Cohen's kappa before adjudication,
and retain disagreements and adjudication decisions. Do not send the source
dataset to an external provider until authorization explicitly covers that
processing.

### Phase 3.4 verdict

**NOT VERIFIED.**

Phase 4 must not claim real-world classifier reliability based on the
synthetic Phase 3 results. A future Phase 3.4 rerun requires an authorized
human-message dataset, documented consent/anonymization, independent human
annotation, and a rate-limit-safe evaluation budget.
