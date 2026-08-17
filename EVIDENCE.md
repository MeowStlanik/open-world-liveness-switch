# Release evidence

## Source

- Repository: https://github.com/MeowStlanik/open-world-liveness-switch
- Immutable contract source: https://github.com/MeowStlanik/open-world-liveness-switch/blob/975dcb69fe54bd023540d1b062917be7bab08d61/contracts/open_world_liveness_switch.py
- Source SHA-256: `9308a95b5cec8d20f215580342ae0290473c3ec908654737d7faec2da4349036`
- Direct tests: https://github.com/MeowStlanik/open-world-liveness-switch/tree/975dcb69fe54bd023540d1b062917be7bab08d61/tests
- Consensus design: https://github.com/MeowStlanik/open-world-liveness-switch/blob/975dcb69fe54bd023540d1b062917be7bab08d61/docs/CONSENSUS.md
- Security model: https://github.com/MeowStlanik/open-world-liveness-switch/blob/975dcb69fe54bd023540d1b062917be7bab08d61/docs/SECURITY.md

## Bradbury

- Contract address: `0x66553A47Cf2ad63671E3f8003ADD7a46790aB7B9`
- Deployment transaction: `0xb9fc529cf68e604b83df354f79e94c1466478dae86aa9d020b9570f3b50bbddb`
- Transaction evidence: https://explorer-bradbury.genlayer.com/tx/0xb9fc529cf68e604b83df354f79e94c1466478dae86aa9d020b9570f3b50bbddb
- Contract evidence: https://explorer-bradbury.genlayer.com/address/0x66553A47Cf2ad63671E3f8003ADD7a46790aB7B9

## Verification claim

The guarded release pipeline performs two complete passes of Python compilation, GenVM lint/SDK validation, GenVM type checking, and 21 direct-mode tests against identical contract bytes. It then deploys once, caches the transaction/address bound to the source hash, and verifies the deployed schema and `get_stats()` view before publishing this evidence.

## Reviewed behaviors

- A switch cannot arm from absence.
- Unknown/unavailable sources never count as inactivity.
- Negative consensus requires absolute source and independent-family quorums.
- Validators independently repeat fetch/classification and exactly agree on safety labels.
- Positive consensus clears negative progress and grace.
- Grace expiry cannot release without a fresh negative consensus probe.
- Owner/guardians can delay once and cannot accelerate release.
- Armed switches cannot be cancelled or reconfigured by a stolen owner key.
- Beneficiary payload metadata is released only through the authorization view, with an explicit warning that raw chain storage is public.
