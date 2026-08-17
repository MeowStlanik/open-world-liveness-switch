# Consensus design

## Safety-relevant output

Every probe produces one record per registered source:

```json
{
  "id": "github",
  "status": "ACTIVE | NO_ACTIVITY | UNKNOWN",
  "coverage": "COMPLETE | PARTIAL | UNAVAILABLE",
  "anchor_status": "MATCH | MISMATCH | UNKNOWN",
  "observed_activity_at": "ISO-8601 or empty",
  "evidence": "short public-evidence explanation",
  "confidence": 0
}
```

Only three fields influence deterministic aggregation: `status`, `coverage`, and `anchor_status`. Evidence, timestamps, and confidence must pass invariants and semantic validation but are not independently used to accelerate release.

## Leader execution

The leader renders every URL as text, truncates each page to a bounded size, labels unavailable sources, and asks an LLM to evaluate the immutable source definition as of the deterministic transaction timestamp. Source documents are wrapped as untrusted data and prompt instructions explicitly reject embedded instructions.

## Validator execution

Each validator:

1. parses the leader JSON and checks every structural invariant;
2. independently repeats all web fetches and the classification prompt;
3. checks its source ID set exactly matches registration;
4. requires exact per-source agreement on status, coverage, and identity-anchor status;
5. asks a separate comparison prompt whether both evidence sets consistently justify those labels and dates;
6. accepts only the literal verdict `ACCEPT`.

This is stricter than format validation. Validators independently reproduce the safety-relevant judgment, while semantic comparison allows different quotes or phrasing when they support the same classification.

## Deterministic aggregation

Positive and negative evidence are intentionally asymmetric:

- `active_count >= active_quorum` confirms activity and resets all negative progress.
- A negative round requires zero active sources, `inactive_count >= inactive_quorum`, and enough distinct inactive source families.
- Every other combination is inconclusive.
- Unknown sources remain visible in the audit log but contribute to neither side.

The absolute quorums are frozen at registration. An unavailable source therefore cannot reduce the denominator or make release easier.

## Transition rules

- `UNARMED` only becomes `MONITORING` after positive consensus.
- Consecutive negative rounds in `MONITORING` start `GRACE`.
- Positive consensus during `GRACE` returns to `MONITORING` and clears all negative progress.
- Passing `release_eligible_at` changes nothing by itself.
- A new negative consensus probe after the deadline changes `GRACE` to `RELEASED`.

This final probe avoids release based on evidence that may have become stale during grace.

## Why no refundable probe bond

Rate limiting already bounds probe spam. A refundable bond would add native-value transfer failure modes without improving the semantic decision, while a burn on unchanged results would discourage useful monitoring. The primitive therefore keeps probing permissionless and rate-limited.
