# API reference

## `register_switch`

Creates an immutable candidate switch in `UNARMED`.

Parameters:

- `switch_id`: unique identifier (`[A-Za-z0-9_-]`, 1–64 chars).
- `sources_json`: 3–8 source definitions with `id`, `family`, `url`, `criteria`, and `identity_anchor`.
- `beneficiaries_json`: 1–8 `{address, share_bps}` entries totalling 10,000.
- `guardians_json`: 1–5 addresses, disjoint from owner and beneficiaries.
- `active_quorum`: positive source count required to confirm activity.
- `inactive_quorum`: negative source count required; minimum 2.
- `inactive_family_quorum`: distinct negative families required; minimum 2.
- `consecutive_rounds_required`: 2–10.
- `min_probe_seconds`: 3,600–2,592,000.
- `grace_seconds`: 86,400–31,536,000.
- `payload_uri`: public locator or encrypted-object locator.
- `payload_sha256`: optional 64-character hex commitment.

## `probe(switch_id)`

Permissionless consensus write. Enforces the frozen interval, records all source results, aggregates quorums, and applies at most one state transition.

## `request_grace_extension(switch_id)`

Owner or any registered guardian may add exactly one additional `grace_seconds` period per grace episode. It must be called before the current deadline.

## `cancel_unarmed(switch_id)`

Owner-only cancellation. Rejected after positive arming.

## Views

- `get_switch(switch_id)`: full state-machine configuration and counters.
- `get_source(switch_id, source_id)`: source definition and latest normalized evidence.
- `get_probe(switch_id, probe_number)`: immutable JSON audit snapshot.
- `liveness(switch_id)`: compact status for downstream contracts.
- `authorization(switch_id, beneficiary)`: share and payload metadata only after release.
- `get_stats()`: contract-level limits and safety flags.

## Statuses

- `UNARMED`: registered but no positive baseline yet.
- `MONITORING`: positively armed and accepting evidence rounds.
- `GRACE`: negative threshold reached; delay and final probe required.
- `RELEASED`: terminal authorization state.
- `CANCELLED`: terminal owner cancellation before arming.
