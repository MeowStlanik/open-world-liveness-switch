# Security model

## Invariants

1. Absence cannot arm a switch.
2. `UNKNOWN` never becomes or counts as `NO_ACTIVITY`.
3. A source outage cannot lower a configured quorum.
4. Negative progression requires independent source families.
5. Any accepted active quorum clears negative progression.
6. Grace expiry alone cannot release.
7. Owner and guardians may delay once but never accelerate.
8. An armed switch cannot be cancelled or reconfigured by the owner key.
9. Payload metadata is hidden by the public API until release, but remains public in raw chain storage.

## Threat analysis

| Threat | Mitigation | Residual risk |
| --- | --- | --- |
| One website is down | `UNKNOWN`; absolute quorum unchanged | Too many outages can stall forever |
| Correlated platform outage | Family-diversity quorum | Families are labels chosen at registration |
| Stolen owner key | Armed configuration is immutable; no heartbeat reset | Attacker may compromise public sources too |
| Stolen social account | Multiple heterogeneous sources | Quorum compromise can forge activity |
| Prompt injection in a page | Untrusted-data delimiters, independent validator fetch, semantic check | Model-level attacks remain possible |
| Partial/paginated history | `NO_ACTIVITY` requires `COMPLETE` coverage | A model may overestimate completeness |
| False negative consensus | Repeated rounds, grace, guardian extension, final fresh probe | Colluding/incorrect validators remain a risk |
| Malicious guardian | Only one delay; cannot release or redirect | A guardian can consume the only extension |
| Public payload metadata | Release-gated API and commitment | Raw on-chain storage is always public |

## Source selection guidance

- Use sources controlled by different providers and authentication systems.
- Prefer feeds or pages that expose a complete bounded activity window.
- Put a stable identity marker on owner-controlled pages.
- Do not treat an HTTP success code as complete evidence.
- Avoid criteria that require inaccessible private context.
- Set inactive quorum and family quorum conservatively.

## Scope exclusions

This primitive does not establish death, legal incapacity, identity, ownership of external accounts, or entitlement under inheritance law. It does not custody decryption keys or guarantee external payload availability. Production asset movement should use a separately audited adapter and wait for GenLayer transaction finality.
