# Verification

The release is accepted only after two complete verification passes over identical contract bytes.

Each pass runs:

1. Python bytecode compilation.
2. `genvm-lint check` for SDK/schema/GenVM restrictions.
3. `genvm-lint typecheck` with the pinned environment.
4. 21 direct-mode tests covering registration invariants, custom consensus validation, unknown handling, source-family quorum, state transitions, guardian delay, final-probe release, authorization, and rate limiting.

Run on Linux/macOS:

```bash
./scripts/verify.sh
```

On Windows, run the commands from scripts/verify.sh in Git Bash or WSL.
